"""Compare a captured original-game trace with a simulator trace of the same actions."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.parity import compare_traces

parser = argparse.ArgumentParser()
parser.add_argument("reference", type=Path)
parser.add_argument("candidate", type=Path)
parser.add_argument("--output", type=Path)
args = parser.parse_args()
report = compare_traces(args.reference, args.candidate)
text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
if args.output:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text)
print(text, end="")
raise SystemExit(0 if report["passed"] else 1)
