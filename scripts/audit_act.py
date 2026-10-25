"""Audit a recorded act offline; an incomplete attempt exits nonzero and is retained."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.act_replay import audit_act

parser = argparse.ArgumentParser()
parser.add_argument("trace", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
result = audit_act(args.trace)
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(
    json.dumps(
        {k: v for k, v in result.items() if k != "capture_hashes"}, ensure_ascii=False
    )
)
raise SystemExit(0 if result["passed"] else 1)
