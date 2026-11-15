"""E3 registration and accounting tests; no learning interactions."""

import copy
import json

import pytest

from sts2lab.rl_experiment import EXPERIMENT_PATH, ExperimentBudget, load_experiment
from sts2lab.rl_io import Budget


def test_frozen_experiment_reuses_e1_and_keeps_test_sealed():
    spec, base = load_experiment()
    assert spec["campaign_hard_cap"] == 3 * spec["valid_transitions_per_seed"] == 98304
    assert spec["workers"] * base["ppo"]["rollout_steps_per_worker"] == 512
    assert spec["valid_transitions_per_seed"] // 512 == 64
    assert not spec["final_test_enabled"] and not base["formal_training"]["enabled"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("workers", 8),
        ("training_run_seeds", [41]),
        ("campaign_hard_cap", 1000000),
        ("base_recipe_sha256", "bad"),
        ("final_test_enabled", True),
        ("reward_shaping", True),
        ("evaluate_initial_policy", False),
        ("valid_transitions_per_seed", 32769),
        ("device", "cuda"),
    ],
)
def test_unregistered_changes_refused(tmp_path, field, value):
    spec = json.loads(EXPERIMENT_PATH.read_text())
    spec[field] = value
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        load_experiment(path)


def test_e2_cap_does_not_expand(tmp_path):
    with pytest.raises(ValueError, match="E2 hard cap"):
        Budget(tmp_path / "e2.jsonl", 98304)


def test_experiment_budget_per_seed_resume_and_lock(tmp_path):
    spec, _ = load_experiment()
    path = tmp_path / "budget.jsonl"
    first = ExperimentBudget(path, spec, 41)
    try:
        first.reserve(32768, "synthetic-41")
        first.confirm(32764, "synthetic-41")  # uncertainty stays charged
        with pytest.raises(ValueError, match="exhausted"):
            first.reserve(4, "retry")
        with pytest.raises(BlockingIOError):
            ExperimentBudget(path, spec, 42)
    finally:
        first.close()
    for seed in (42, 43):
        budget = ExperimentBudget(path, spec, seed)
        try:
            budget.reserve(32768, f"synthetic-{seed}")
            budget.confirm(32768, f"synthetic-{seed}")
        finally:
            budget.close()
    resumed = ExperimentBudget(path, spec, 41)
    try:
        assert resumed.charged == 98304 and resumed.valid == 98300
        assert resumed.seed_charged == 32768 and resumed.seed_valid == 32764
        with pytest.raises(ValueError, match="exhausted"):
            resumed.reserve(4, "retry")
    finally:
        resumed.close()
    changed = copy.deepcopy(spec)
    changed["primary_comparison"] = "changed"
    with pytest.raises(ValueError, match="fingerprint"):
        ExperimentBudget(path, changed, 41)


def test_unregistered_seed_refused(tmp_path):
    spec, _ = load_experiment()
    with pytest.raises(ValueError, match="Unregistered"):
        ExperimentBudget(tmp_path / "ledger", spec, 44)
