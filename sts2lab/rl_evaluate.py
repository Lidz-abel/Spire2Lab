"""Validation-only evaluation; no final-test execution path in E2."""

import time

import numpy as np
import torch

from .contracts import digest
from .gym_env import CombatEnv
from .policies import Policy
from .rl_contract import evaluation_cases, validate_transition
from .rl_io import append_json, isolated_rng, state_digest, write_json
from .rl_model import tensor_batch


def evaluate(recipe, policy, output, model=None):
    if policy not in ("random", "heuristic", "rl_greedy") or (
        (policy == "rl_greedy") != (model is not None)
    ):
        raise ValueError("Unknown evaluation policy or missing model")
    output.mkdir(parents=True, exist_ok=False)
    cases = evaluation_cases(recipe, "validation")
    records, all_latencies = [], []
    started = time.perf_counter()
    with isolated_rng(), torch.no_grad():
        if model is not None:
            model.eval()
        for encounter, seed in cases:
            env = CombatEnv(encounter)
            steps, episode_return, latency = 0, 0.0, []
            record = {"encounter": encounter, "seed": seed, "policy": policy}
            chain = []
            try:
                obs, _ = env.reset(seed=seed)
                rule = (
                    Policy(policy, recipe["evaluation"]["random_policy_seed"])
                    if model is None
                    else None
                )
                while True:
                    tick = time.perf_counter()
                    if rule is not None:
                        selected = rule.decide(env.sim.observe()).selected_action_id
                        action = next(
                            i
                            for i, a in enumerate(env.actions)
                            if a.action_id == selected
                        )
                    else:
                        logits, _ = model(tensor_batch([obs]))
                        action = int(logits.argmax(dim=-1).item())
                    latency.append(1000 * (time.perf_counter() - tick))
                    transition = validate_transition(obs, action, env.step(action))
                    steps += 1
                    episode_return += transition.reward
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
                        record.update(
                            outcome=(
                                "won"
                                if transition.reward == 1
                                else "lost" if transition.reward == -1 else "truncated"
                            ),
                            final_hp=int(obs["player"][0]),
                        )
                        break
                record["trajectory_sha256"] = digest(chain)
            except Exception as exc:
                record.update(
                    outcome="error", error=f"{type(exc).__name__}: {exc}", final_hp=None
                )
            finally:
                env.close()
            record.update(
                valid_steps=steps, episode_return=episode_return, decision_ms=latency
            )
            append_json(output / "cases.jsonl", record)
            records.append(record)
            all_latencies.extend(latency)
    counts = {
        k: sum(r["outcome"] == k for r in records)
        for k in ("won", "lost", "truncated", "error")
    }
    elapsed = time.perf_counter() - started
    summary = {
        "scope": "simulator_validation_only",
        "policy": policy,
        "split": "validation",
        "case_manifest_sha256": digest(cases),
        "cases": len(records),
        **counts,
        "win_rate": counts["won"] / len(records),
        "mean_final_hp_all_cases": (
            None
            if counts["error"]
            else float(np.mean([r["final_hp"] for r in records]))
        ),
        "mean_return": float(np.mean([r["episode_return"] for r in records])),
        "valid_steps": sum(r["valid_steps"] for r in records),
        "seconds": elapsed,
        "decision_ms_p50": float(np.median(all_latencies)) if all_latencies else None,
        "decision_ms_p95": (
            float(np.percentile(all_latencies, 95)) if all_latencies else None
        ),
        "model_sha256": state_digest(model.state_dict()) if model is not None else None,
        "by_encounter": {
            enc: {
                k: sum(r["encounter"] == enc and r["outcome"] == k for r in records)
                for k in counts
            }
            for enc in recipe["encounters"]
        },
    }
    summary["transitions_per_second"] = summary["valid_steps"] / elapsed
    write_json(output / "summary.json", summary)
    return summary


def selection_key(summary, valid_steps):
    if summary["error"] or summary["mean_final_hp_all_cases"] is None:
        raise ValueError("Incomplete validation cannot select a checkpoint")
    return (summary["win_rate"], summary["mean_final_hp_all_cases"], -valid_steps)
