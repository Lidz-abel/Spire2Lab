"""Generate and compare a simulator candidate using one predeclared seed."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.reference_replay import replay_reference

parser = argparse.ArgumentParser()
parser.add_argument("reference", type=Path)
parser.add_argument(
    "--seed",
    type=int,
    required=True,
    help="Declared simulator seed; never searched against results",
)
parser.add_argument(
    "--candidate",
    type=Path,
    required=True,
    help="New output trace path, must not already exist",
)
parser.add_argument("--report", type=Path, required=True)
args = parser.parse_args()
if args.report.resolve() in {args.reference.resolve(), args.candidate.resolve()}:
    parser.error("Report must have a separate path")
if args.report.exists() or args.candidate.exists():
    parser.error(
        "Use new candidate/report paths; previous attempts must remain reviewable"
    )
result = replay_reference(args.reference, args.candidate, args.seed)
args.report.parent.mkdir(parents=True, exist_ok=True)
with args.report.open("x") as report_file:
    report_file.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result["passed"] else 1)
