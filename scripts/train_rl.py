"""Bounded E2 CPU training. No final test or E3 long-training mode."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--profile", choices=("main", "resume", "workers2", "workers4"), default="main"
    )
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    if (args.profile == "resume") != bool(args.resume):
        parser.error("Only the resume profile requires --resume")
    if Path(args.run_id).name != args.run_id or args.run_id in (".", ".."):
        parser.error("run-id must be a single directory name")
    campaign = args.campaign.resolve()
    if not campaign.is_relative_to(ROOT / "artifacts"):
        parser.error("Campaign output must be under ignored artifacts/")
    run(campaign, args.run_id, args.profile, args.resume)


def run(campaign, run_id, profile, resume):
    # Imports here keep spawned environment processes free of the Torch learner.
    from datetime import datetime, timezone
    import json
    import os
    import random
    import resource
    import signal
    import time
    import traceback
    import numpy as np
    import torch
    from sts2lab.rl_contract import load_recipe
    from sts2lab.rl_io import (
        Budget,
        append_json,
        compatibility,
        isolated_rng,
        load_checkpoint,
        rng_state,
        save_checkpoint,
        source_version,
        state_digest,
        write_json,
        file_hash,
    )
    from sts2lab.rl_model import ActorCritic, make_optimizer, tensor_batch
    from sts2lab.rl_ppo import update
    from sts2lab.rl_rollout import CaseScheduler, EnvironmentPool, collect
    from sts2lab.rl_evaluate import evaluate, selection_key

    recipe = load_recipe()
    workers, transitions = {
        "main": (1, 8192),
        "resume": (1, 256),
        "workers2": (2, 512),
        "workers4": (4, 1024),
    }[profile]
    out = campaign / run_id
    out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    seed = recipe["smoke"]["run_seed"]
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    origin = source_version()
    compatible = compatibility(recipe)
    write_json(
        out / "run.json",
        {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "cwd": str(ROOT),
            "argv": sys.argv,
            "profile": profile,
            "workers": workers,
            "target_new_transitions": transitions,
            "source": origin,
            "compatibility": compatible,
            "recipe": recipe,
            "resume": str(resume) if resume else None,
            "device": "cpu",
            "stop": "SIGINT/SIGTERM requests checkpoint after full update",
        },
    )
    budget, pool = None, None
    started = time.perf_counter()
    stopping = False

    def stop_requested(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop_requested)
    signal.signal(signal.SIGTERM, stop_requested)
    learner = {"updates": 0, "valid_steps": 0}
    history, best, last_path = [], None, None
    run_steps, rollout_seconds, optimize_seconds, evaluation_seconds = 0, 0.0, 0.0, 0.0
    model = ActorCritic(recipe)
    optimizer = make_optimizer(model, recipe)
    scheduler = CaseScheduler(recipe, seed)
    try:
        budget = Budget(campaign / "budget.jsonl")
        if budget.charged + transitions > budget.cap:
            raise ValueError(
                "Insufficient remaining E2 budget for this execution profile"
            )
        if resume:
            restored = load_checkpoint(resume, model, optimizer, compatible)
            learner = dict(restored["counters"])
            scheduler = CaseScheduler(recipe, seed, restored["scheduler"])
            history = list(restored["validation"])
            if history:
                selected = max(
                    history,
                    key=lambda row: selection_key(row["summary"], row["valid_steps"]),
                )
                best = (
                    selection_key(selected["summary"], selected["valid_steps"]),
                    selected["checkpoint"],
                )
            with torch.no_grad():
                logits, value = model(tensor_batch(restored["probe"]["observations"]))
            proof = {
                "parent_checkpoint": str(resume),
                "parent_file_sha256": file_hash(resume),
                "model_equal": state_digest(model.state_dict())
                == state_digest(restored["model"]),
                "optimizer_equal": state_digest(optimizer.state_dict())
                == state_digest(restored["optimizer"]),
                "rng_equal": state_digest(rng_state()) == state_digest(restored["rng"]),
                "probe_equal": torch.equal(logits, restored["probe"]["logits"])
                and torch.equal(value, restored["probe"]["value"]),
                "restored_counters": learner.copy(),
                "scheduler_cursor": scheduler.cursor,
                "aborted_by_resume": restored["active_episodes"],
                "mid_episode_exact_resume": False,
            }
            write_json(out / "resume-proof.json", proof)
            if not all(
                proof[k]
                for k in ("model_equal", "optimizer_equal", "rng_equal", "probe_equal")
            ):
                raise AssertionError("Resume equivalence failed")
        pool = EnvironmentPool(workers)
        for index in range(workers):
            pool.reset(index, scheduler.next())
        initial_model = state_digest(model.state_dict())
        while run_steps < transitions:
            before_hash = state_digest(model.state_dict())
            rollout = collect(
                model,
                pool,
                scheduler,
                recipe["ppo"]["rollout_steps_per_worker"],
                budget,
                run_id,
                learner["updates"],
            )
            count = len(rollout["observations"])
            run_steps += count
            learner["valid_steps"] += count
            rollout_seconds += rollout["sampling_seconds"]
            number = learner["updates"] + 1
            roll_dir = out / "rollouts"
            roll_dir.mkdir(exist_ok=True)
            arrays = {
                k: rollout[k]
                for k in (
                    "actions",
                    "log_prob",
                    "values",
                    "next_values",
                    "rewards",
                    "terminated",
                    "truncated",
                )
            }
            for prefix, rows in (
                ("obs", rollout["observations"]),
                ("next_obs", rollout["next_observations"]),
            ):
                arrays.update(
                    {f"{prefix}/{k}": np.stack([o[k] for o in rows]) for k in rows[0]}
                )
            np.savez_compressed(roll_dir / f"update-{number:04d}.npz", **arrays)
            for row in rollout["audit"]:
                append_json(out / "transitions.jsonl", row)
            for row in rollout["episodes"]:
                append_json(out / "episodes.jsonl", row)
            tick = time.perf_counter()
            metrics = update(
                model,
                optimizer,
                tensor_batch(rollout["observations"]),
                rollout["actions"],
                rollout["log_prob"],
                rollout["values"],
                rollout["rewards"],
                rollout["next_values"],
                rollout["terminated"],
                rollout["truncated"],
                recipe,
            )
            optimize_seconds += time.perf_counter() - tick
            learner["updates"] = number
            after_hash = state_digest(model.state_dict())
            if metrics["max_grad_norm_observed"] <= 0 or before_hash == after_hash:
                raise AssertionError("No nonzero-gradient parameter update")
            metrics.update(
                **learner,
                run_valid_steps=run_steps,
                budget_charged=budget.charged,
                parameter_hash_before=before_hash,
                parameter_hash_after=after_hash,
                sampling_seconds=rollout["sampling_seconds"],
                inference_batch_ms_p50=float(np.median(rollout["inference_batch_ms"])),
            )
            append_json(out / "updates.jsonl", metrics)
            print(
                json.dumps(
                    {
                        k: metrics[k]
                        for k in (
                            "updates",
                            "valid_steps",
                            "loss",
                            "entropy",
                            "grad_norm",
                        )
                    }
                ),
                flush=True,
            )
            should_validate = (
                number % recipe["evaluation"]["validation_every_updates"] == 0
                or run_steps == transitions
                or stopping
            )
            if should_validate:
                tick = time.perf_counter()
                summary = evaluate(
                    recipe,
                    "rl_greedy",
                    out / "validation" / f"update-{number:04d}",
                    model,
                )
                evaluation_seconds += time.perf_counter() - tick
                score = selection_key(summary, learner["valid_steps"])
                history.append(
                    {
                        "update": number,
                        "valid_steps": learner["valid_steps"],
                        "summary": summary,
                        "checkpoint": str(
                            out / "checkpoints" / f"update-{number:04d}.pt"
                        ),
                    }
                )
            if number == 1 or should_validate:
                probe_obs = [pool.observations[0]]
                with torch.no_grad():
                    probe_logits, probe_value = model(tensor_batch(probe_obs))
                last_path = out / "checkpoints" / f"update-{number:04d}.pt"
                save_checkpoint(
                    last_path,
                    model,
                    optimizer,
                    recipe,
                    compatible,
                    scheduler.state(),
                    learner.copy(),
                    history,
                    pool.active_episodes(),
                    {
                        "observations": probe_obs,
                        "logits": probe_logits,
                        "value": probe_value,
                    },
                    origin,
                )
                if should_validate and (best is None or score > best[0]):
                    best = (score, str(last_path))
                # Independent model+optimizer reconstruction, preserving the live learner RNG.
                with isolated_rng():
                    check_model = ActorCritic(recipe)
                    check_opt = make_optimizer(check_model, recipe)
                    saved = load_checkpoint(
                        last_path, check_model, check_opt, compatible
                    )
                    with torch.no_grad():
                        check_logits, check_value = check_model(tensor_batch(probe_obs))
                    proof = {
                        "checkpoint": str(last_path),
                        "model_equal": state_digest(check_model.state_dict())
                        == state_digest(model.state_dict()),
                        "optimizer_equal": state_digest(check_opt.state_dict())
                        == state_digest(optimizer.state_dict()),
                        "rng_equal": state_digest(rng_state())
                        == state_digest(saved["rng"]),
                        "probe_equal": torch.equal(check_logits, probe_logits)
                        and torch.equal(check_value, probe_value),
                    }
                    write_json(last_path.with_suffix(".reload.json"), proof)
                    if not all(
                        proof[k]
                        for k in (
                            "model_equal",
                            "optimizer_equal",
                            "rng_equal",
                            "probe_equal",
                        )
                    ):
                        raise AssertionError("Checkpoint reload failed")
            if stopping:
                break
        if profile == "main" and not stopping:
            for policy in ("random", "heuristic"):
                tick = time.perf_counter()
                baseline = evaluate(recipe, policy, out / "validation" / policy)
                evaluation_seconds += time.perf_counter() - tick
                if baseline["error"]:
                    raise AssertionError("Baseline evaluation errors")
        cleanup = pool.close()
        if any(r["alive"] or r["forced"] or r["exitcode"] != 0 for r in cleanup):
            raise AssertionError("Unclean worker shutdown")
        elapsed = time.perf_counter() - started
        write_json(
            out / "result.json",
            {
                "status": "stopped" if stopping else "passed",
                "scope": "E2_simulator_training_only",
                "profile": profile,
                "workers": workers,
                "counters": learner,
                "run_valid_transitions": run_steps,
                "budget_charged": budget.charged,
                "budget_confirmed": budget.valid,
                "initial_model_sha256": initial_model,
                "final_model_sha256": state_digest(model.state_dict()),
                "last_checkpoint": str(last_path),
                "best_checkpoint": best[1] if best else None,
                "best_validation_key": best[0] if best else None,
                "sampling_seconds": rollout_seconds,
                "optimization_seconds": optimize_seconds,
                "evaluation_seconds": evaluation_seconds,
                "total_seconds": elapsed,
                "sampling_transitions_per_second": run_steps / rollout_seconds,
                "training_transitions_per_second": run_steps
                / (rollout_seconds + optimize_seconds),
                "end_to_end_training_transitions_per_second": run_steps / elapsed,
                "parent_peak_rss_kib": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss,
                "worker_cleanup": cleanup,
                "unfinished_episodes_at_stop": pool.active_episodes(),
                "test_cases_executed": 0,
                "original_game_evidence_added": False,
            },
        )
    except BaseException as exc:
        write_json(
            out / "failure.json",
            {
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "counters": learner,
                "run_valid_transitions": run_steps,
                "budget_charged": budget.charged if budget else None,
            },
        )
        raise
    finally:
        if pool is not None:
            cleanup = pool.close()
            write_json(out / "cleanup.json", {"workers": workers, "processes": cleanup})
        if budget is not None:
            budget.close()


if __name__ == "__main__":
    main()
