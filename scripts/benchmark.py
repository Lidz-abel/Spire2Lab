"""Evaluate the complete fixed inventory; never call simulator results game parity."""

import argparse
from datetime import datetime, timezone
import json
import platform
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.simulator import CONFIG, ROOT, Simulator
from sts2lab.policies import Policy
from sts2lab.contracts import PROTOCOL_VERSION


def run(split):
    results = []
    latencies = []
    build = None
    for encounter in CONFIG["encounters"]:
        for seed in CONFIG[f"{split}_seeds"]:
            for policy_name in ("random", "heuristic"):
                with Simulator(encounter, seed) as env:
                    build = env.manifest
                    policy = Policy(policy_name, seed=773)
                    obs = env.observe()
                    started = time.perf_counter()
                    while obs.outcome == "ongoing":
                        decision_started = time.perf_counter()
                        proposal = policy.decide(obs)
                        obs = env.step(
                            proposal.selected_action_id, obs.decision_id
                        ).observation
                        latencies.append(
                            (time.perf_counter() - decision_started) * 1000
                        )
                    elapsed = time.perf_counter() - started
                    results.append(
                        {
                            "encounter": encounter,
                            "seed": seed,
                            "policy": policy_name,
                            "outcome": obs.outcome,
                            "hp": obs.player.hp,
                            "steps": env.sequence,
                            "seconds": elapsed,
                        }
                    )
    report = {
        "scope": "simulator_only",
        "local_game_parity": "not_verified",
        "split": split,
        "benchmark_version": CONFIG["benchmark_version"],
        "protocol_version": PROTOCOL_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "config": CONFIG,
        "build": build,
        "python_version": platform.python_version(),
        "policy_seed": 773,
        "policy_versions": ["random-v1", "heuristic-v1"],
        "timing": {
            "scope": "policy_and_environment_step_in_one_process_no_rendering_excludes_reset",
            "decisions_per_second": len(latencies) / (sum(latencies) / 1000),
            "decision_ms_p50": sorted(latencies)[len(latencies) // 2],
            "decision_ms_p95": sorted(latencies)[int(len(latencies) * 0.95)],
        },
        "episodes": len(results),
        "results": results,
    }
    output = ROOT / "artifacts" / f"benchmark-{split}.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "episodes": len(results),
                "steps": sum(x["steps"] for x in results),
                "outcomes": {
                    p: {
                        o: sum(x["policy"] == p and x["outcome"] == o for x in results)
                        for o in ("won", "lost", "truncated")
                    }
                    for p in ("random", "heuristic")
                },
                "report": str(output),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--split", choices=["development", "heldout"], default="development"
    )
    run(parser.parse_args().split)
