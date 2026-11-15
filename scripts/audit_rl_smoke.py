"""Audit saved E2 evidence and replay the first actor/update without environment steps."""

import argparse
import csv
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def read_lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_run(path):
    import numpy as np

    result = json.loads((path / "result.json").read_text())
    updates = read_lines(path / "updates.jsonl")
    audit = read_lines(path / "transitions.jsonl")
    offset, previous = 0, {}
    for file in sorted((path / "rollouts").glob("*.npz")):
        with np.load(file, allow_pickle=False) as archive:
            data = {key: archive[key] for key in archive.files}
            actions = data["actions"].reshape(-1)
            n = len(actions)
            masks = data["obs/action_mask"]
            assert masks[np.arange(n), actions].all()
            terminal = data["terminated"].reshape(-1)
            truncated = data["truncated"].reshape(-1)
            assert not (terminal & truncated).any()
            done = terminal | truncated
            assert np.array_equal(data["next_obs/action_mask"].any(axis=1), ~done)
            reward = data["rewards"].reshape(-1)
            assert (
                np.isin(reward[terminal], [-1, 1]).all()
                and (reward[~terminal] == 0).all()
            )
            keys = [key[4:] for key in data if key.startswith("obs/")]
            for i, row in enumerate(audit[offset : offset + n]):
                worker = row["worker"]
                if worker in previous:
                    prev_meta, prev_done, prev_next = previous[worker]
                    if prev_done:
                        assert (
                            row["episode_id"] != prev_meta["episode_id"]
                            and row["step_index"] == 0
                        )
                    else:
                        assert row["episode_id"] == prev_meta["episode_id"]
                        assert row["step_index"] == prev_meta["step_index"] + 1
                        for key in keys:
                            np.testing.assert_array_equal(
                                data[f"obs/{key}"][i], prev_next[key]
                            )
                previous[worker] = (
                    row,
                    done[i],
                    {key: data[f"next_obs/{key}"][i].copy() for key in keys},
                )
            offset += n
    assert offset == len(audit) == result["run_valid_transitions"]
    assert all(
        row["parameter_hash_before"] != row["parameter_hash_after"]
        and row["max_grad_norm_observed"] > 0
        for row in updates
    )
    assert all(
        all(np.isfinite(row[k]) for k in ("loss", "entropy", "grad_norm", "approx_kl"))
        for row in updates
    )
    reloads = [
        json.loads(f.read_text()) for f in (path / "checkpoints").glob("*.reload.json")
    ]
    assert reloads and all(
        all(
            row[k]
            for k in ("model_equal", "optimizer_equal", "rng_equal", "probe_equal")
        )
        for row in reloads
    )
    assert result["status"] == "passed" and result["test_cases_executed"] == 0
    assert all(
        not r["alive"] and not r["forced"] and r["exitcode"] == 0
        for r in result["worker_cleanup"]
    )
    return {
        "run": path.name,
        "profile": result["profile"],
        "valid_transitions": offset,
        "updates": len(updates),
        "reload_checks": len(reloads),
        "boundary_audit_passed": True,
    }


def replay_first_update(path):
    import numpy as np
    import torch
    from sts2lab.rl_contract import load_recipe
    from sts2lab.rl_io import state_digest
    from sts2lab.rl_model import ActorCritic, make_optimizer, tensor_batch
    from sts2lab.rl_ppo import update

    recipe = load_recipe()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(41)
    np.random.seed(41)
    torch.manual_seed(41)
    model = ActorCritic(recipe)
    optimizer = make_optimizer(model, recipe)
    recorded = read_lines(path / "updates.jsonl")[0]
    assert state_digest(model.state_dict()) == recorded["parameter_hash_before"]
    with np.load(path / "rollouts/update-0001.npz", allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
        fields = [key[4:] for key in data if key.startswith("obs/")]
        observations = [
            {key: data[f"obs/{key}"][i] for key in fields}
            for i in range(len(data["obs/player"]))
        ]
        with torch.no_grad():
            for i, observation in enumerate(observations):
                dist, value = model.distribution(tensor_batch([observation]))
                action = dist.sample()
                assert action.item() == data["actions"][i, 0]
                np.testing.assert_array_equal(
                    dist.log_prob(action).numpy(), data["log_prob"][i]
                )
                np.testing.assert_array_equal(value.numpy(), data["values"][i])
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
            recipe,
        )
    assert state_digest(model.state_dict()) == recorded["parameter_hash_after"]
    return {
        "scope": "saved_public_observation_actor_and_optimizer_replay_no_environment_steps",
        "actions_replayed": len(observations),
        "log_prob_and_values_exact": True,
        "updated_parameter_hash_exact": True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    args = parser.parse_args()
    from sts2lab.rl_io import write_json

    campaign = args.campaign
    runs = [
        campaign / name
        for name in ("main-01", "resume-01", "workers2-01", "workers4-01")
    ]
    records = [audit_run(path) for path in runs]
    events = read_lines(campaign / "budget.jsonl")
    charged = sum(e.get("reserved", 0) for e in events)
    confirmed = sum(e.get("confirmed", 0) for e in events)
    assert charged == confirmed == sum(r["valid_transitions"] for r in records) == 9984
    resume = json.loads((runs[1] / "resume-proof.json").read_text())
    assert all(
        resume[k]
        for k in ("model_equal", "optimizer_equal", "rng_equal", "probe_equal")
    )
    assert resume["restored_counters"] == {"updates": 64, "valid_steps": 8192}
    main_result = json.loads((runs[0] / "result.json").read_text())
    selected = Path(main_result["best_checkpoint"]).stem
    validation = {
        p: json.loads((runs[0] / "validation" / name / "summary.json").read_text())
        for p, name in (
            ("random", "random"),
            ("heuristic", "heuristic"),
            ("rl_selected", selected),
        )
    }
    with (campaign / "training-curve.csv").open("x") as f:
        fields = [
            "updates",
            "valid_steps",
            "loss",
            "policy_loss",
            "value_loss",
            "entropy",
            "grad_norm",
            "approx_kl",
        ]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(read_lines(runs[0] / "updates.jsonl"))
    with (campaign / "validation-curve.csv").open("x") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["update", "valid_steps", "win_rate", "mean_final_hp_all_cases"],
        )
        writer.writeheader()
        for file in sorted((runs[0] / "validation").glob("update-*/summary.json")):
            row = json.loads(file.read_text())
            number = int(file.parent.name.split("-")[1])
            writer.writerow(
                {
                    "update": number,
                    "valid_steps": number * 128,
                    "win_rate": row["win_rate"],
                    "mean_final_hp_all_cases": row["mean_final_hp_all_cases"],
                }
            )
    summary = {
        "scope": "E2_simulator_engineering_acceptance_not_original_game",
        "runs": records,
        "budget_charged": charged,
        "budget_confirmed": confirmed,
        "replay": replay_first_update(runs[0]),
        "validation": validation,
        "final_test_cases_executed": 0,
        "original_game_evidence_added": False,
    }
    write_json(campaign / "acceptance.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "validation"}, indent=2))


if __name__ == "__main__":
    main()
