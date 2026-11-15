"""Materialize and fingerprint E1 manifests without running any evaluation case."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sts2lab.contracts import digest
from sts2lab.rl_contract import RECIPE_PATH, evaluation_cases, load_recipe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    recipe = load_recipe()
    binary = ROOT / ".tools/native/Sts2Emulator.so"
    actual = hashlib.sha256(binary.read_bytes()).hexdigest()
    if actual != recipe["native_sha256"]:
        raise ValueError("Native fingerprint mismatch")
    manifests = {
        split: evaluation_cases(recipe, split)
        for split in ("train", "validation", "test")
    }
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scope": "static contract and seed manifest check; no training/evaluation execution",
        "recipe_sha256": hashlib.sha256(RECIPE_PATH.read_bytes()).hexdigest(),
        "files_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in (
                "sts2lab/rl_contract.py",
                "docs/RL-MVP.md",
                "requirements-rl.lock",
                "config/content-v1.json",
            )
        },
        "native_sha256": actual,
        "split_counts": {k: len(v) for k, v in manifests.items()},
        "split_sha256": {k: digest(v) for k, v in manifests.items()},
        "manifests": manifests,
        "training_started": False,
        "validation_cases_executed": 0,
        "test_cases_executed": 0,
        "original_game_evidence_added": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Never replace an earlier evidence record.
    with args.output.open("x") as out:
        json.dump(report, out, ensure_ascii=False, indent=2)
        out.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k != "manifests"}, indent=2))


if __name__ == "__main__":
    main()
