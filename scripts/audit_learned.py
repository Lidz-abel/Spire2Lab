"""Audit saved PPO decisions and confirmations offline; no game actions."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sts2lab.learned_replay import audit_learned_trace
from sts2lab.rl_io import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output exists; preserve evidence and choose a new path")
    try:
        result = audit_learned_trace(args.trace)
    except Exception as exc:
        result = {
            "passed": False,
            "error": f"{type(exc).__name__}: {exc}",
            "new_game_actions": 0,
        }
    write_json(args.output, result)
    print(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
