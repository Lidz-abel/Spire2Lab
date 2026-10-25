"""Fixed-budget comparison with immutable traces, failures and policy replay."""

import argparse
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.contracts import StepRequest
from sts2lab.planning_replay import replay_planning
from sts2lab.planning import PlanningConfig
from sts2lab.runtime import Lab
from sts2lab.simulator import CONFIG, ROOT
from sts2lab.traces import read_trace
from sts2lab.verification import replay_trace


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(rows):
    result = []
    groups = sorted({(r["policy"], r["search_budget"], r["condition"]) for r in rows})
    for policy, budget, condition in groups:
        subset = [
            r
            for r in rows
            if (r["policy"], r["search_budget"], r["condition"])
            == (policy, budget, condition)
        ]
        latencies = sorted(v for r in subset for v in r["decision_ms"])
        result.append(
            {
                "policy": policy,
                "search_budget": budget,
                "condition": condition,
                "episodes": len(subset),
                "outcomes": dict(Counter(r["outcome"] for r in subset)),
                "mean_final_hp": sum(r["hp"] for r in subset) / len(subset),
                "decisions": sum(r["decisions"] for r in subset),
                "fallback_decisions": sum(r["fallback_decisions"] for r in subset),
                "search_calls": sum(r["search_calls"] for r in subset),
                "belief_calls": sum(r["belief_calls"] for r in subset),
                "initializations": sum(r["initializations"] for r in subset),
                "decision_ms_p50": latencies[math.ceil(len(latencies) * 0.5) - 1],
                "decision_ms_p95": latencies[math.ceil(len(latencies) * 0.95) - 1],
            }
        )
    return result


def conditions_for(recipe, selected=None):
    conditions = recipe.get("conditions")
    if conditions is None:
        conditions = [
            {
                "id": f"{name}:{budget}",
                "policy": name,
                "planning_config": (
                    {**recipe["planning"], "search_calls": budget}
                    if name in ("rollout", "hierarchical")
                    else None
                ),
            }
            for name in recipe["policies"]
            for budget in (
                recipe["budgets"] if name in ("rollout", "hierarchical") else [0]
            )
        ]
    ids = [c["id"] for c in conditions]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Conditions require unique IDs")
    if selected and (len(selected) != len(set(selected)) or set(selected) - set(ids)):
        raise ValueError("Unknown or duplicate requested condition")
    for c in conditions:
        if c["policy"] not in ("random", "heuristic", "rollout", "hierarchical"):
            raise ValueError("Unknown policy")
        if c["policy"] in ("rollout", "hierarchical"):
            PlanningConfig.model_validate(c["planning_config"])
        elif c.get("planning_config") is not None:
            raise ValueError("Baseline cannot carry unused planning settings")
    return [c for c in conditions if not selected or c["id"] in selected]


def seeds_for(recipe, split, pilot=False, shard_index=0, shard_count=1):
    """Partition the preregistered inventory without selecting by outcomes."""
    seeds = recipe.get(f"{split}_seeds", CONFIG[f"{split}_seeds"])
    if len(seeds) != len(set(seeds)) or not seeds:
        raise ValueError("Seeds must be a nonempty unique inventory")
    if not 1 <= shard_count <= len(seeds) or not 0 <= shard_index < shard_count:
        raise ValueError("Invalid seed shard")
    if pilot and (split == "heldout" or shard_count != 1):
        raise ValueError("Pilot evaluation is development-only and unsharded")
    return seeds[:1] if pilot else seeds[shard_index::shard_count]


async def run(args):
    recipe = json.loads(args.recipe.read_text())
    conditions = conditions_for(recipe, args.conditions)
    seeds = seeds_for(
        recipe, args.split, args.pilot, args.shard_index, args.shard_count
    )
    output = args.output
    output.mkdir(parents=True, exist_ok=False)  # preserve every prior attempt
    source_paths = subprocess.check_output(
        ["git", "ls-files", "*.py", "*.json", "native", "vendor/manifest.json"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    source = {p: sha(ROOT / p) for p in source_paths if (ROOT / p).is_file()}
    status = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=ROOT, text=True
    )
    if args.split == "heldout" and status.strip():
        raise ValueError(
            "Commit the frozen implementation/configuration before heldout evaluation"
        )
    cpu = next(
        (
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        "unknown",
    )
    report = {
        "schema": "planning-evaluation-v1",
        "status": "running",
        "scope": "simulator_only",
        "split": args.split,
        "pilot": args.pilot,
        "recipe": recipe,
        "recipe_sha256": sha(args.recipe),
        "selected_conditions": [c["id"] for c in conditions],
        "selected_seeds": seeds,
        "seed_shard": {"index": args.shard_index, "count": args.shard_count},
        "source_sha256": source,
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(status.strip()),
        "python": platform.python_version(),
        "hardware": {
            "cpu": cpu,
            "logical_cpus": os.cpu_count(),
            "cpu_affinity_count": len(os.sched_getaffinity(0)),
            "memory": next(
                line
                for line in Path("/proc/meminfo").read_text().splitlines()
                if line.startswith("MemTotal:")
            ),
            "platform": platform.platform(),
            "exclusive_host": False,
            "gpu_used": False,
        },
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": [],
        "new_original_game_evidence": False,
    }

    def save():
        report["summary"] = summarize(report["results"])
        temp = output / "report.tmp"
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(output / "report.json")

    lab = Lab(output / "traces")
    save()
    try:
        for encounter in CONFIG["encounters"]:
            for seed in seeds:
                for condition in conditions:
                    name = condition["policy"]
                    config = condition.get("planning_config")
                    budget = config["search_calls"] if config else 0
                    state = await lab.new_session(
                        encounter,
                        seed,
                        name,
                        recipe["policy_seed"],
                        planning_config=config,
                    )
                    while state["status"] != "finished":
                        state = await lab.step(
                            StepRequest(
                                request_id=f'bench-{len(state["history"])}-{lab.env.sequence}',
                                decision_id=state["observation"]["decision_id"],
                            )
                        )
                    path = lab.trace_path(state["metadata"]["run_id"])
                    await lab.archive(state["metadata"]["run_id"])
                    events = read_trace(path)
                    decisions = [e["data"] for e in events if e["kind"] == "decision"]
                    reports = [
                        e["data"] for e in events if e["kind"] == "planning_report"
                    ]
                    replay = replay_trace(path)
                    if not replay["passed"]:
                        raise RuntimeError(f"Actor replay failed: {replay}")
                    policy_replay = (
                        replay_planning(path) if budget and seed == seeds[0] else None
                    )
                    if policy_replay and not policy_replay["passed"]:
                        raise RuntimeError(f"Policy replay failed: {policy_replay}")
                    row = {
                        "encounter": encounter,
                        "seed": seed,
                        "condition": condition["id"],
                        "policy": name,
                        "search_budget": budget,
                        "outcome": state["observation"]["outcome"],
                        "hp": state["observation"]["player"]["hp"],
                        "decisions": len(decisions),
                        "decision_ms": [d["elapsed_ms"] for d in decisions],
                        "fallback_decisions": sum(
                            bool(r["fallback_reason"]) for r in reports
                        ),
                        "fallback_reasons": dict(
                            Counter(
                                r["fallback_reason"]
                                for r in reports
                                if r["fallback_reason"]
                            )
                        ),
                        "search_calls": sum(r["model_calls"] for r in reports),
                        "belief_calls": sum(
                            r["belief"].get("model_calls", 0) for r in reports
                        ),
                        "initializations": sum(
                            r["belief"].get("initializations", 0) for r in reports
                        ),
                        "trace": str(path.relative_to(output)),
                        "trace_sha256": sha(path),
                        "actor_replay": replay,
                        "policy_replay": policy_replay,
                    }
                    report["native_sha256"] = state["metadata"]["build"][
                        "library_sha256"
                    ]
                    report["results"].append(row)
                    save()
                    print(
                        json.dumps(
                            {
                                k: row[k]
                                for k in (
                                    "encounter",
                                    "seed",
                                    "condition",
                                    "policy",
                                    "search_budget",
                                    "outcome",
                                    "hp",
                                    "fallback_decisions",
                                )
                            }
                        ),
                        flush=True,
                    )
        report["status"] = "complete"
    except BaseException as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        await lab.close()
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split", choices=["development", "heldout"], default="development"
    )
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument(
        "--recipe", type=Path, default=ROOT / "config/phase2-planning.json"
    )
    parser.add_argument("--conditions", nargs="+")
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(run(parser.parse_args()))
