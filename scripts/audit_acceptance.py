"""Recompute the phase-one original-game acceptance matrix from original evidence."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sts2lab.acceptance import audit_acceptance, DEFAULT_INDEX, DEFAULT_STATUS

parser = argparse.ArgumentParser()
parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
parser.add_argument("--output", type=Path, default=DEFAULT_STATUS)
args = parser.parse_args()
if args.output.resolve() == args.index.resolve():
    parser.error("Audit output must not overwrite the evidence index")
report = audit_acceptance(args.index)
args.output.parent.mkdir(parents=True, exist_ok=True)
staged = args.output.with_suffix(".tmp")
staged.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
staged.replace(args.output)
print(
    json.dumps(
        {
            "passed": report["passed"],
            "required_cases": len(report["required_case_ids"]),
            "missing_cases": len(report["missing_cases"]),
            "missing_coverage": report["missing_coverage"],
            "errors": report["errors"],
            "report": str(args.output),
        },
        ensure_ascii=False,
        indent=2,
    )
)
raise SystemExit(0 if report["passed"] else 1)
