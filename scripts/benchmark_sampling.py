"""Measure reproducibility, latency and memory for 1/2/4 spawned workers."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.sampling import benchmark


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, nargs="+", default=[1, 2, 4])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--episodes-per-case", type=int, default=5)
    parser.add_argument(
        "--split", choices=["development", "heldout"], default="development"
    )
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.repeats < 1 or args.episodes_per_case < 1 or args.timeout <= 0:
        parser.error("Repetitions and timeout must be positive")
    if (
        any(w < 1 or w > 32 for w in args.workers)
        or len(set(args.workers)) != len(args.workers)
        or 1 not in args.workers
    ):
        parser.error(
            "Use unique worker counts in 1..32, including the one-worker baseline"
        )
    report = benchmark(
        workers=args.workers,
        repeats=args.repeats,
        episodes_per_case=args.episodes_per_case,
        split=args.split,
        timeout=args.timeout,
    )
    output = args.output or ROOT / "artifacts" / f"sampling-{args.split}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    staged = output.with_suffix(output.suffix + ".tmp")
    staged.write_text(json.dumps(report, indent=2) + "\n")
    staged.replace(output)
    print(
        json.dumps(
            {
                "report": str(output),
                "reproducibility": report["reproducibility"],
                "summary": report["summary"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
