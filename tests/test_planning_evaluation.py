"""Evaluation groups and the horizon-bias regression motivating the HP utility."""

import json

import pytest

from scripts.benchmark_planning import conditions_for, summarize
from sts2lab.hierarchy import leaf_utility
from sts2lab.planning import PlanningConfig, PlanningPolicy
from sts2lab.simulator import ROOT, Simulator


def test_evaluation_does_not_merge_distinct_conditions_at_the_same_budget():
    recipe = json.loads((ROOT / "config/phase2-search-ablation.json").read_text())
    assert len(conditions_for(recipe)) == 7
    assert len(conditions_for(recipe, ["flat-depth8-256", "flat-depth32-256"])) == 2
    with pytest.raises(ValueError):
        conditions_for(recipe, ["typo"])
    rows = []
    for label, hp in [("shallow", 60), ("deep", 80)]:
        rows.append(
            {
                "policy": "rollout",
                "search_budget": 256,
                "condition": label,
                "outcome": "won",
                "hp": hp,
                "decisions": 1,
                "fallback_decisions": 0,
                "search_calls": 256,
                "belief_calls": 8,
                "initializations": 8,
                "decision_ms": [1.0],
            }
        )
    result = summarize(rows)
    assert len(result) == 2 and {r["mean_final_hp"] for r in result} == {60, 80}


def test_hp_utility_has_no_automatic_bonus_for_an_early_damaged_win():
    with Simulator() as env:
        root = env.observe()
        near_win = root.model_copy(
            update={
                "player": root.player.model_copy(update={"block": 100}),
                "enemies": [root.enemies[0].model_copy(update={"hp": 1})],
            }
        )
        damaged_win = root.model_copy(
            update={
                "outcome": "won",
                "enemies": [],
                "player": root.player.model_copy(update={"hp": 50}),
            }
        )
        assert leaf_utility(root, damaged_win) > leaf_utility(root, near_win)
        assert leaf_utility(
            root, damaged_win, version="terminal-hp-leaf-v2"
        ) < leaf_utility(root, near_win, version="terminal-hp-leaf-v2")
        loss = damaged_win.model_copy(
            update={
                "outcome": "lost",
                "player": root.player.model_copy(update={"hp": 0}),
            }
        )
        assert leaf_utility(root, loss, version="terminal-hp-leaf-v2") < leaf_utility(
            root, damaged_win, version="terminal-hp-leaf-v2"
        )


def test_search_report_binds_the_selected_leaf_variant_without_mutating_real_reward():
    with Simulator("nibbits-weak", 1) as env:
        policy = PlanningPolicy(
            "hierarchical",
            773,
            "nibbits-weak",
            PlanningConfig(
                belief_proposal="public_opening",
                utility_version="terminal-hp-leaf-v2",
                search_calls=256,
                rollout_depth=32,
                max_wall_ms=None,
            ),
        )
        try:
            before = env.observe()
            d = policy.decide(before)
            assert policy.last_report["utility_version"] == "terminal-hp-leaf-v2"
            assert env.observe() == before
            assert policy.last_report["model_calls"] <= 256
            result = env.step(d.selected_action_id, before.decision_id)
            assert result.reward_version == "terminal-win-v1"
            assert result.reward == (
                1
                if result.observation.outcome == "won"
                else -1 if result.observation.outcome == "lost" else 0
            )
        finally:
            policy.close()
