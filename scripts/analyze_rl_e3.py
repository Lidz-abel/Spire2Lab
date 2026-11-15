"""E3 saved-data audits, fixed-budget paired comparisons, and validation case traces."""

import argparse
import csv
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def case_map(path):
    rows = lines(path)
    mapping = {(r["encounter"], r["seed"]): r for r in rows}
    if len(mapping) != len(rows) or any(r["outcome"] == "error" for r in rows):
        raise ValueError("Duplicate or failed evaluation cases")
    return mapping


def audit_seed(path):
    import numpy as np
    from sts2lab.rl_io import file_hash

    result = json.loads((path / "result.json").read_text())
    metadata = json.loads((path / "run.json").read_text())
    assert result["status"] == "passed" and not metadata["source"]["dirty"]
    assert result["counters"] == {"updates": 64, "valid_steps": 32768}
    rows = lines(path / "transitions.jsonl")
    offset, previous = 0, {}
    for file in sorted((path / "rollouts").glob("*.npz")):
        with np.load(file, allow_pickle=False) as archive:
            data = {k: archive[k] for k in archive.files}
        actions = data["actions"].reshape(-1)
        n = len(actions)
        assert data["obs/action_mask"][np.arange(n), actions].all()
        term, trunc = data["terminated"].reshape(-1), data["truncated"].reshape(-1)
        assert not (term & trunc).any()
        done = term | trunc
        assert np.array_equal(data["next_obs/action_mask"].any(axis=1), ~done)
        reward = data["rewards"].reshape(-1)
        assert np.isin(reward[term], [-1, 1]).all() and (reward[~term] == 0).all()
        keys = [k[4:] for k in data if k.startswith("obs/")]
        for i, row in enumerate(rows[offset : offset + n]):
            worker = row["worker"]
            if worker in previous:
                prev, prev_done, next_obs = previous[worker]
                if prev_done:
                    assert (
                        row["episode_id"] != prev["episode_id"]
                        and row["step_index"] == 0
                    )
                else:
                    assert (
                        row["episode_id"] == prev["episode_id"]
                        and row["step_index"] == prev["step_index"] + 1
                    )
                    for key in keys:
                        np.testing.assert_array_equal(
                            data[f"obs/{key}"][i], next_obs[key]
                        )
            previous[worker] = (
                row,
                done[i],
                {k: data[f"next_obs/{k}"][i].copy() for k in keys},
            )
        offset += n
    assert offset == len(rows) == result["run_valid_transitions"] == 32768
    updates = lines(path / "updates.jsonl")
    assert len(updates) == 64
    for row in updates:
        assert row["parameter_hash_before"] != row["parameter_hash_after"]
        assert row["max_grad_norm_observed"] > 0
        assert all(
            np.isfinite(row[k]) for k in ("loss", "entropy", "grad_norm", "approx_kl")
        )
    reloads = list((path / "checkpoints").glob("*.reload.json"))
    assert len(reloads) == 9 and all(
        all(json.loads(f.read_text()).values()) for f in reloads
    )
    for p in (path / "checkpoints").glob("*.pt"):
        assert (
            file_hash(p)
            == json.loads(p.with_suffix(".sha256.json").read_text())["sha256"]
        )
    assert all(
        not r["alive"] and not r["forced"] and r["exitcode"] == 0
        for r in result["worker_cleanup"]
    )
    return {
        "seed": result["seed"],
        "transitions_audited": offset,
        "checkpoint_reload_checks": len(reloads),
        "boundary_audit_passed": True,
    }


def replay_first_update(path, seed, base):
    import numpy as np
    import torch
    from sts2lab.rl_io import state_digest
    from sts2lab.rl_model import ActorCritic, make_optimizer, tensor_batch
    from sts2lab.rl_ppo import update

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = ActorCritic(base)
    optimizer = make_optimizer(model, base)
    row = lines(path / "updates.jsonl")[0]
    assert state_digest(model.state_dict()) == row["parameter_hash_before"]
    with np.load(path / "rollouts/update-0001.npz", allow_pickle=False) as archive:
        data = {k: archive[k] for k in archive.files}
    keys = [k[4:] for k in data if k.startswith("obs/")]
    observations = [{k: data[f"obs/{k}"][i] for k in keys} for i in range(512)]
    with torch.no_grad():
        for t in range(128):
            dist, value = model.distribution(
                tensor_batch(observations[t * 4 : (t + 1) * 4])
            )
            actions = dist.sample()
            np.testing.assert_array_equal(actions.numpy(), data["actions"][t])
            np.testing.assert_array_equal(
                dist.log_prob(actions).numpy(), data["log_prob"][t]
            )
            np.testing.assert_array_equal(value.numpy(), data["values"][t])
    update(
        model,
        optimizer,
        tensor_batch(observations),
        data["actions"],
        data["log_prob"],
        data["values"],
        data["rewards"],
        data["next_values"],
        data["terminated"],
        data["truncated"],
        base,
    )
    assert state_digest(model.state_dict()) == row["parameter_hash_after"]
    return {
        "seed": seed,
        "actions_replayed": 512,
        "parameter_hash_exact": True,
        "new_environment_steps": 0,
    }


def capture_case(model, expected, output):
    import torch
    from sts2lab.contracts import digest
    from sts2lab.gym_env import CombatEnv
    from sts2lab.rl_contract import validate_transition
    from sts2lab.rl_io import write_json
    from sts2lab.rl_model import tensor_batch

    assert 20000 <= expected["seed"] <= 20019
    env = CombatEnv(expected["encounter"])
    chain, labels = [], []
    try:
        obs, _ = env.reset(seed=expected["seed"])
        with torch.no_grad():
            while True:
                logits, _ = model(tensor_batch([obs]))
                action = int(logits.argmax(-1).item())
                labels.append(env.actions[action].label)
                transition = validate_transition(obs, action, env.step(action))
                chain.append(
                    {
                        "obs": {k: v.tolist() for k, v in obs.items()},
                        "action": action,
                        "reward": transition.reward,
                        "terminated": transition.terminated,
                        "truncated": transition.truncated,
                    }
                )
                obs = transition.next_observation
                if transition.terminated or transition.truncated:
                    break
        assert digest(chain) == expected["trajectory_sha256"]
        assert int(obs["player"][0]) == expected["final_hp"]
        write_json(
            output,
            {
                "scope": "validation_case_replay_not_new_training_or_test_case",
                "case": expected,
                "action_labels": labels,
                "transitions": chain,
            },
        )
        return len(chain)
    finally:
        env.close()


def summarize(campaign):
    import numpy as np
    import torch
    from sts2lab.rl_experiment import load_experiment, experiment_compatibility
    from sts2lab.rl_io import file_hash, load_checkpoint, write_json
    from sts2lab.rl_model import ActorCritic

    spec, base = load_experiment()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output = campaign / "analysis"
    output.mkdir(exist_ok=False)
    heuristic = case_map(campaign / "baselines/heuristic/cases.jsonl")
    random_rows = case_map(campaign / "baselines/random/cases.jsonl")
    records, audits, replay, curve, paired, failures = [], [], [], [], [], []
    capture_steps = 0
    for seed in spec["training_run_seeds"]:
        path = campaign / f"seed-{seed}-attempt-1"
        audits.append(audit_seed(path))
        replay.append(replay_first_update(path, seed, base))
        result = json.loads((path / "result.json").read_text())
        paths = {
            "initial": Path(result["initial_checkpoint"]),
            "final": Path(result["last_checkpoint"]),
            "selected": Path(result["best_checkpoint"]),
        }
        cases = {
            k: case_map(p.parent.parent / "validation" / p.stem / "cases.jsonl")
            for k, p in paths.items()
        }
        assert all(
            set(v) == set(heuristic) == set(random_rows) and len(v) == 60
            for v in cases.values()
        )
        row = {
            "seed": seed,
            "training_transitions": result["run_valid_transitions"],
            "total_seconds": result["total_seconds"],
            "training_transitions_per_second": result[
                "training_transitions_per_second"
            ],
            "checkpoints": {
                k: {"path": str(p.relative_to(ROOT)), "sha256": file_hash(p)}
                for k, p in paths.items()
            },
        }
        for label, values in cases.items():
            row[label] = {
                "won": sum(c["outcome"] == "won" for c in values.values()),
                "lost": sum(c["outcome"] == "lost" for c in values.values()),
                "truncated": sum(c["outcome"] == "truncated" for c in values.values()),
                "mean_final_hp": float(
                    np.mean([c["final_hp"] for c in values.values()])
                ),
            }
        row["final_minus_initial_hp"] = (
            row["final"]["mean_final_hp"] - row["initial"]["mean_final_hp"]
        )
        row["selected_minus_heuristic_hp"] = row["selected"]["mean_final_hp"] - float(
            np.mean([c["final_hp"] for c in heuristic.values()])
        )
        records.append(row)
        for key in sorted(heuristic):
            paired.append(
                {
                    "run_seed": seed,
                    "encounter": key[0],
                    "environment_seed": key[1],
                    **{f"{k}_hp": v[key]["final_hp"] for k, v in cases.items()},
                    "heuristic_hp": heuristic[key]["final_hp"],
                    "random_hp": random_rows[key]["final_hp"],
                    "final_minus_initial_hp": cases["final"][key]["final_hp"]
                    - cases["initial"][key]["final_hp"],
                }
            )
        for p in sorted((path / "validation").glob("update-*/summary.json")):
            data = json.loads(p.read_text())
            number = int(p.parent.name.split("-")[1])
            curve.append(
                {
                    "run_seed": seed,
                    "update": number,
                    "valid_steps": number * 512,
                    "win_rate": data["win_rate"],
                    "mean_final_hp": data["mean_final_hp_all_cases"],
                }
            )
        # Deterministic three largest final-model HP deficits per seed, including losses.
        worst = sorted(
            heuristic,
            key=lambda k: (cases["final"][k]["final_hp"] - heuristic[k]["final_hp"], k),
        )[:3]
        model = ActorCritic(base)
        load_checkpoint(
            paths["final"],
            model,
            None,
            experiment_compatibility(spec, base),
            restore_random=False,
        )
        model.eval()
        for index, key in enumerate(worst):
            expected = cases["final"][key]
            capture_steps += capture_case(
                model, expected, output / f"case-{seed}-{index}.json"
            )
            failures.append(
                {
                    "run_seed": seed,
                    "encounter": key[0],
                    "environment_seed": key[1],
                    "outcome": expected["outcome"],
                    "initial_hp": cases["initial"][key]["final_hp"],
                    "final_hp": expected["final_hp"],
                    "heuristic_hp": heuristic[key]["final_hp"],
                    "trace": f"case-{seed}-{index}.json",
                }
            )
    ledger = lines(campaign / "budget.jsonl")
    charged = sum(r.get("reserved", 0) for r in ledger)
    confirmed = sum(r.get("confirmed", 0) for r in ledger)
    assert charged == confirmed == spec["campaign_hard_cap"] == 98304
    aggregates = {}
    for label in ("initial", "final", "selected"):
        values = [r[label]["mean_final_hp"] for r in records]
        aggregates[label + "_hp"] = {
            "mean": float(np.mean(values)),
            "sample_std": float(np.std(values, ddof=1)),
        }
    deltas = [r["final_minus_initial_hp"] for r in records]
    aggregates["final_minus_initial_hp"] = {
        "mean": float(np.mean(deltas)),
        "sample_std": float(np.std(deltas, ddof=1)),
    }
    for name, rows in (("paired-cases.csv", paired), ("validation-curve.csv", curve)):
        with (output / name).open("x") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    summary = {
        "scope": "E3_small_budget_simulator_validation_only",
        "recipe": "config/rl-e3-v1.json",
        "budget_charged": charged,
        "budget_confirmed": confirmed,
        "training_seeds": records,
        "across_seed_statistics": aggregates,
        "audits": audits,
        "first_update_replays": replay,
        "baselines": {
            k: json.loads((campaign / "baselines" / k / "summary.json").read_text())
            for k in ("random", "heuristic")
        },
        "low_hp_cases": failures,
        "case_replay_validation_steps": capture_steps,
        "final_test_cases_executed": 0,
        "original_game_evidence_added": False,
        "limitations": [
            "Three training seeds on the same 60 validation cases, not 180 independent tasks.",
            "Selected checkpoints are validation-optimistic; primary contrast is fixed final versus initialization.",
            "No full-run training, original-game model deployment, final test or million-step budget.",
        ],
    }
    write_json(output / "summary.json", summary)
    print(
        json.dumps({"across_seed_statistics": aggregates, "budget": charged}, indent=2)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    summarize(args.campaign.resolve())


if __name__ == "__main__":
    main()
