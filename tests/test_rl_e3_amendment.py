"""No game actions: test missing-data and evidence-binding rules."""

import json
import pytest

from scripts.analyze_rl_e3 import case_map, complete_statistics
from sts2lab import rl_e3_amendment as amendment
from sts2lab.rl_io import file_hash
from sts2lab.rl_evaluate import selection_key


def test_incomplete_primary_not_silently_averaged():
    summary = complete_statistics([6.6, 67.55, None])
    assert summary["mean"] is None and summary["sample_std"] is None
    assert summary["available_seed_count"] == 2
    assert complete_statistics([1, 2, 3])["sample_std"] == 1


def test_initial_error_retained_but_never_selected(tmp_path):
    path = tmp_path / "cases.jsonl"
    row = {
        "encounter": "slimes-weak",
        "seed": 20015,
        "outcome": "error",
        "final_hp": None,
    }
    path.write_text(json.dumps(row) + "\n")
    assert case_map(path, allow_error=True)[("slimes-weak", 20015)]["final_hp"] is None
    with pytest.raises(ValueError):
        case_map(path)
    with pytest.raises(ValueError, match="Incomplete"):
        selection_key({"error": 1}, 512)
    path.write_text((json.dumps(row) + "\n") * 2)
    with pytest.raises(ValueError):
        case_map(path, allow_error=True)


@pytest.mark.parametrize(
    "seed,attempt,resume", [(41, 2, None), (43, 1, None), (43, 2, "old.pt")]
)
def test_exception_cannot_apply_to_other_runs(seed, attempt, resume):
    with pytest.raises(ValueError):
        amendment.amendment_metadata(seed, attempt, resume)


def test_retained_control_requires_identical_model_and_evidence(tmp_path, monkeypatch):
    monkeypatch.setattr(amendment, "ROOT", tmp_path)
    source = tmp_path / "original"
    source.mkdir()
    summary = {"error": 1, "mean_final_hp_all_cases": None, "model_sha256": "model"}
    (source / "summary.json").write_text(json.dumps(summary))
    spec = {
        "source_control": "original",
        "model_sha256": "model",
        "files": {"summary.json": file_hash(source / "summary.json")},
    }
    metadata = {"specification": spec}
    with pytest.raises(ValueError, match="model"):
        amendment.retained_control(metadata, "other", tmp_path / "bad")
    assert amendment.retained_control(metadata, "model", tmp_path / "copy") == summary
    (source / "summary.json").write_text("changed")
    with pytest.raises(ValueError, match="fingerprint"):
        amendment.retained_control(metadata, "model", tmp_path / "bad2")
