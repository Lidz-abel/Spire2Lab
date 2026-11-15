"""Run one preregistered E3 seed on CPU; independent budget, no final-test path."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, choices=(41, 42, 43), required=True)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--resume", type=Path)
    args = parser.parse_args()
    if args.attempt < 1:
        parser.error("attempt must be positive")
    run(args.seed, args.attempt, args.resume)


def run(seed, attempt, resume):
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
    from sts2lab.rl_experiment import (
        load_experiment,
        experiment_compatibility,
        ExperimentBudget,
    )
    from sts2lab.rl_io import (
        append_json,
        write_json,
        source_version,
        state_digest,
        isolated_rng,
        save_checkpoint,
        load_checkpoint,
        rng_state,
        file_hash,
    )
    from sts2lab.rl_model import ActorCritic, tensor_batch, make_optimizer
    from sts2lab.rl_rollout import CaseScheduler, EnvironmentPool, collect
    from sts2lab.rl_ppo import update
    from sts2lab.rl_evaluate import evaluate, selection_key

    spec, base = load_experiment()
    campaign = ROOT / spec["campaign_directory"]
    run_id = f"seed-{seed}-attempt-{attempt}"
    out = campaign / run_id
    out.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(spec["torch_threads"])
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    compatible = experiment_compatibility(spec, base)
    origin = source_version()
    if origin["dirty"]:
        raise ValueError("Commit source before E3 execution")
    write_json(
        out / "run.json",
        {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "pid": os.getpid(),
            "cwd": str(ROOT),
            "argv": sys.argv,
            "source": origin,
            "compatibility": compatible,
            "seed": seed,
            "base_recipe": base,
            "experiment": spec,
            "resume": str(resume) if resume else None,
            "stop": "SIGINT/SIGTERM or wall-time limit: checkpoint after update",
        },
    )
    budget, pool = None, None
    stopped = False

    def request_stop(signum, frame):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    started = time.perf_counter()
    learner = {"updates": 0, "valid_steps": 0}
    history, best, initial_summary = [], None, None
    last_path = None
    initial_path = out / "checkpoints/update-0000.pt"
    sampling_seconds, optimization_seconds, evaluation_seconds = 0.0, 0.0, 0.0
    run_steps = 0
    try:
        budget = ExperimentBudget(campaign / "budget.jsonl", spec, seed)
        model = ActorCritic(base)
        optimizer = make_optimizer(model, base)
        scheduler = CaseScheduler(base, seed)
        if resume:
            restored = load_checkpoint(resume, model, optimizer, compatible)
            if restored["recipe"]["seed"] != seed:
                raise ValueError("Resume seed mismatch")
            learner = dict(restored["counters"])
            scheduler = CaseScheduler(base, seed, restored["scheduler"])
            history = list(restored["validation"])
            initial_entry = next(row for row in history if row["update"] == 0)
            initial_summary = initial_entry["summary"]
            initial_path = Path(initial_entry["checkpoint"])
            trained = [row for row in history if row["update"] > 0]
            if trained:
                row = max(
                    trained, key=lambda r: selection_key(r["summary"], r["valid_steps"])
                )
                best = (
                    selection_key(row["summary"], row["valid_steps"]),
                    row["checkpoint"],
                )
            write_json(
                out / "resume.json",
                {
                    "parent": str(resume),
                    "counters": learner,
                    "aborted_by_resume": restored["active_episodes"],
                    "model_equal": state_digest(model.state_dict())
                    == state_digest(restored["model"]),
                    "optimizer_equal": state_digest(optimizer.state_dict())
                    == state_digest(restored["optimizer"]),
                    "rng_equal": state_digest(rng_state())
                    == state_digest(restored["rng"]),
                },
            )
        elif budget.seed_charged:
            raise ValueError(
                "Seed already consumed budget; use compatible checkpoint, not fresh restart"
            )
        if learner["valid_steps"] >= spec["valid_transitions_per_seed"]:
            raise ValueError("Seed already reached target")
        pool = EnvironmentPool(spec["workers"])
        for index in range(spec["workers"]):
            pool.reset(index, scheduler.next())

        def checkpoint(number):
            path = out / "checkpoints" / f"update-{number:04d}.pt"
            probe_obs = [pool.observations[0]]
            with torch.no_grad():
                logits, value = model(tensor_batch(probe_obs))
            save_checkpoint(
                path,
                model,
                optimizer,
                {"base": base, "experiment": spec, "seed": seed},
                compatible,
                scheduler.state(),
                learner.copy(),
                list(history),
                pool.active_episodes(),
                {"observations": probe_obs, "logits": logits, "value": value},
                origin,
            )
            with isolated_rng():
                other = ActorCritic(base)
                other_opt = make_optimizer(other, base)
                saved = load_checkpoint(path, other, other_opt, compatible)
                with torch.no_grad():
                    other_logits, other_value = other(tensor_batch(probe_obs))
                proof = {
                    "model_equal": state_digest(other.state_dict())
                    == state_digest(model.state_dict()),
                    "optimizer_equal": state_digest(other_opt.state_dict())
                    == state_digest(optimizer.state_dict()),
                    "rng_equal": state_digest(rng_state())
                    == state_digest(saved["rng"]),
                    "probe_equal": torch.equal(logits, other_logits)
                    and torch.equal(value, other_value),
                }
                write_json(path.with_suffix(".reload.json"), proof)
                if not all(proof.values()):
                    raise AssertionError("Checkpoint reload mismatch")
            return path

        if initial_summary is None:
            tick = time.perf_counter()
            initial_summary = evaluate(
                base, "rl_greedy", out / "validation/update-0000", model
            )
            evaluation_seconds += time.perf_counter() - tick
            selection_key(initial_summary, 0)  # reject incomplete initial control
            history.append(
                {
                    "update": 0,
                    "valid_steps": 0,
                    "checkpoint": str(initial_path),
                    "summary": initial_summary,
                }
            )
            checkpoint(0)
            print(
                json.dumps(
                    {
                        "seed": seed,
                        "initial_validation": {
                            k: initial_summary[k]
                            for k in ("won", "mean_final_hp_all_cases")
                        },
                    }
                ),
                flush=True,
            )
        while learner["valid_steps"] < spec["valid_transitions_per_seed"]:
            before = state_digest(model.state_dict())
            rollout = collect(
                model,
                pool,
                scheduler,
                base["ppo"]["rollout_steps_per_worker"],
                budget,
                run_id,
                learner["updates"],
            )
            count = len(rollout["observations"])
            learner["valid_steps"] += count
            run_steps += count
            number = learner["updates"] + 1
            sampling_seconds += rollout["sampling_seconds"]
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
            (out / "rollouts").mkdir(exist_ok=True)
            np.savez_compressed(out / "rollouts" / f"update-{number:04d}.npz", **arrays)
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
                base,
            )
            optimization_seconds += time.perf_counter() - tick
            learner["updates"] = number
            after = state_digest(model.state_dict())
            if before == after or metrics["max_grad_norm_observed"] <= 0:
                raise AssertionError("Missing finite nonzero update")
            metrics.update(
                **learner,
                run_valid_steps=run_steps,
                parameter_hash_before=before,
                parameter_hash_after=after,
                sampling_seconds=rollout["sampling_seconds"],
                inference_batch_ms_p50=float(np.median(rollout["inference_batch_ms"])),
            )
            append_json(out / "updates.jsonl", metrics)
            if time.perf_counter() - started >= spec["max_seconds_per_run"]:
                stopped = True
            if (
                number % spec["validation_every_updates"] == 0
                or learner["valid_steps"] == spec["valid_transitions_per_seed"]
                or stopped
            ):
                tick = time.perf_counter()
                summary = evaluate(
                    base,
                    "rl_greedy",
                    out / "validation" / f"update-{number:04d}",
                    model,
                )
                evaluation_seconds += time.perf_counter() - tick
                score = selection_key(summary, learner["valid_steps"])
                path = out / "checkpoints" / f"update-{number:04d}.pt"
                history.append(
                    {
                        "update": number,
                        "valid_steps": learner["valid_steps"],
                        "checkpoint": str(path),
                        "summary": summary,
                    }
                )
                last_path = checkpoint(number)
                if best is None or score > best[0]:
                    best = (score, str(last_path))
                print(
                    json.dumps(
                        {
                            "seed": seed,
                            "updates": number,
                            "valid_steps": learner["valid_steps"],
                            "won": summary["won"],
                            "mean_hp": summary["mean_final_hp_all_cases"],
                            "elapsed_seconds": time.perf_counter() - started,
                        }
                    ),
                    flush=True,
                )
            if stopped:
                break
        cleanup = pool.close()
        if any(r["alive"] or r["forced"] or r["exitcode"] != 0 for r in cleanup):
            raise AssertionError("Worker shutdown failed")
        final_summary = history[-1]["summary"]
        write_json(
            out / "result.json",
            {
                "status": "stopped" if stopped else "passed",
                "seed": seed,
                "scope": "E3_simulator_validation_only",
                "counters": learner,
                "run_valid_transitions": run_steps,
                "budget_charged": budget.charged,
                "budget_confirmed": budget.valid,
                "seed_charged": budget.seed_charged,
                "seed_confirmed": budget.seed_valid,
                "initial_checkpoint": str(initial_path),
                "last_checkpoint": str(last_path),
                "best_checkpoint": best[1] if best else None,
                "initial_summary": initial_summary,
                "final_summary": final_summary,
                "fixed_final_minus_initial_hp": final_summary["mean_final_hp_all_cases"]
                - initial_summary["mean_final_hp_all_cases"],
                "fixed_final_minus_initial_win_rate": final_summary["win_rate"]
                - initial_summary["win_rate"],
                "sampling_seconds": sampling_seconds,
                "optimization_seconds": optimization_seconds,
                "evaluation_seconds": evaluation_seconds,
                "total_seconds": time.perf_counter() - started,
                "training_transitions_per_second": run_steps
                / (sampling_seconds + optimization_seconds),
                "parent_peak_rss_kib": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss,
                "worker_cleanup": cleanup,
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
                "budget_charged": budget.charged if budget else None,
            },
        )
        raise
    finally:
        if pool is not None:
            write_json(out / "cleanup.json", {"processes": pool.close()})
        if budget is not None:
            budget.close()


if __name__ == "__main__":
    main()
