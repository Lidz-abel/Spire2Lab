"""Paired belief-only replay of recorded public histories; never constructs an actor."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.belief import HistoryBelief, public_hash
from sts2lab.simulator import load_native
from sts2lab.traces import load_semantic_trace
from sts2lab.contracts import Action


def run(args):
    source = json.loads(args.input.read_text())
    if source["split"] != "development":
        raise ValueError("Belief tuning is restricted to development histories")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise ValueError("Preserve prior reports; use a new output")
    report = {
        "schema": "belief-public-replay-v2",
        "scope": "recorded public history; no acting environment input",
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "native_sha256": load_native()[2]["library_sha256"],
        "policy_seed": 773,
        "particles": 8,
        "init_attempts": 512,
        "update_attempts": args.update_attempts,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "cases": [],
    }

    def save():
        temp = args.output.with_suffix(".tmp")
        temp.write_text(json.dumps(report, indent=2) + "\n")
        temp.replace(args.output)

    save()
    try:
        for row in source["results"]:
            if row["policy"] not in ("random", "heuristic") or (
                args.pilot and row["seed"] != 1
            ):
                continue
            metadata, observations, transitions = load_semantic_trace(
                args.input.parent / row["trace"], "native_simulator"
            )
            for method in ("seed_rejection", "public_opening"):
                belief = HistoryBelief(
                    metadata["encounter"],
                    random.Random(773).randrange(2**31),
                    particles=8,
                    update_attempts=args.update_attempts,
                    proposal=method,
                )
                case = {
                    "encounter": row["encounter"],
                    "seed": row["seed"],
                    "source_policy": row["policy"],
                    "proposal": method,
                    "steps": [],
                }
                try:
                    start = time.perf_counter()
                    belief.initialize(observations[0])
                    case["opening"] = {
                        **belief.report,
                        "elapsed_ms": (time.perf_counter() - start) * 1000,
                    }
                    for i, data in enumerate(transitions):
                        assert all(
                            public_hash(p.observe()) == public_hash(observations[i])
                            for p in belief.particles
                        )
                        case["steps"].append({"before_step": i, **belief.report})
                        start = time.perf_counter()
                        belief.advance(
                            observations[i],
                            Action.model_validate(data["action"]),
                            observations[i + 1],
                        )
                        belief.report["elapsed_ms"] = (
                            time.perf_counter() - start
                        ) * 1000
                    case["depleted_decisions"] = sum(
                        s["particles"] == 0 for s in case["steps"]
                    )
                    case["decisions"] = len(case["steps"])
                    case["terminal_particles"] = len(belief.particles)
                    assert case["terminal_particles"] == 0
                    report["cases"].append(case)
                    save()
                    print(
                        json.dumps(
                            {
                                k: case[k]
                                for k in (
                                    "encounter",
                                    "seed",
                                    "source_policy",
                                    "proposal",
                                    "decisions",
                                    "depleted_decisions",
                                )
                            }
                        ),
                        flush=True,
                    )
                finally:
                    belief.close()
        report["status"] = "complete"
    except BaseException as e:
        report.update(status="failed", error=f"{type(e).__name__}: {e}")
        raise
    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument(
        "--update-attempts", type=int, default=128, choices=(128, 256, 512, 1024)
    )
    run(parser.parse_args())
