"""Explicit, evidence-bound exception for E3's failed initial control only."""

import json
from pathlib import Path
import shutil

from .rl_contract import ROOT
from .rl_io import file_hash

AMENDMENT = ROOT / "config/rl-e3-v1-amendment1.json"


def amendment_metadata(seed, attempt, resume):
    if (seed, attempt) != (43, 2) or resume is not None:
        raise ValueError("Amendment applies only to fresh seed43 attempt2")
    return {
        "specification": json.loads(AMENDMENT.read_text()),
        "files": {
            str(p.relative_to(ROOT)): file_hash(p) for p in (AMENDMENT, Path(__file__))
        },
    }


def retained_control(amendment, model_sha256, output):
    spec = amendment["specification"]
    if model_sha256 != spec["model_sha256"]:
        raise ValueError("Initial model differs from retained control")
    source = ROOT / spec["source_control"]
    for name, expected in spec["files"].items():
        if file_hash(source / name) != expected:
            raise ValueError("Retained initial evidence fingerprint mismatch")
    summary = json.loads((source / "summary.json").read_text())
    if (
        summary["error"] != 1
        or summary["mean_final_hp_all_cases"] is not None
        or summary["model_sha256"] != model_sha256
    ):
        raise ValueError("Unexpected initial control")
    shutil.copytree(source, output)
    return summary
