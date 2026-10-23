"""Actual native planning tests; no live original-game evidence."""

import pytest
from pydantic import ValidationError

from sts2lab.belief import HistoryBelief, action_key, public_hash
from sts2lab.contracts import semantic_state
from sts2lab.hierarchy import TacticalHierarchy
from sts2lab.planning import PlanningConfig, PlanningPolicy
from sts2lab.simulator import Simulator


def config(**kwargs):
    return PlanningConfig(
        **{
            "particles": 2,
            "init_attempts": 512,
            "search_calls": 96,
            "rollout_depth": 6,
            "max_wall_ms": None,
            **kwargs,
        }
    )


def test_search_budget_mapping_and_no_acting_environment_mutation():
    with Simulator("nibbits-weak", 1) as env:
        before = env.observe()
        policy = PlanningPolicy("rollout", 773, "nibbits-weak", config())
        try:
            decision = policy.decide(before)
            assert policy.last_report["fallback_reason"] is None
            assert 0 < policy.last_report["model_calls"] <= 96
            assert decision.selected_action_id in {
                a.action_id for a in before.legal_actions
            }
            assert env.observe() == before
            assert all(
                p is not env and p.handle != env.handle for p in policy.belief.particles
            )
            assert all(
                public_hash(p.observe()) == public_hash(before)
                for p in policy.belief.particles
            )
            assert policy.decide(before) is decision  # no duplicate planning work
            assert (
                sum(c["visits"] for c in policy.last_report["candidates"])
                == policy.last_report["rollouts"]
            )
        finally:
            particles = list(policy.belief.particles)
            policy.close()
            assert all(p.handle == -1 for p in particles)


def test_same_public_input_produces_same_search_despite_different_actual_hidden_state():
    with Simulator("nibbits-weak", 1) as env, env.sample_world(1) as hidden_variant:
        first, second = env.observe(), hidden_variant.observe()
        assert semantic_state(first) == semantic_state(second)
        assert (
            env._raw(debug=True)["debug_draw_order"]
            != hidden_variant._raw(debug=True)["debug_draw_order"]
        )
        policies = [
            PlanningPolicy("hierarchical", 773, "nibbits-weak", config())
            for _ in range(2)
        ]
        try:
            a, b = [p.decide(o) for p, o in zip(policies, [first, second])]
            assert action_key(
                first,
                next(
                    x
                    for x in first.legal_actions
                    if x.action_id == a.selected_action_id
                ),
            ) == action_key(
                second,
                next(
                    x
                    for x in second.legal_actions
                    if x.action_id == b.selected_action_id
                ),
            )
            assert [(c.action_id, c.score) for c in a.candidates] == [
                (c.action_id, c.score) for c in b.candidates
            ]
            assert (
                policies[0].last_report["model_calls"]
                == policies[1].last_report["model_calls"]
            )
            assert (
                policies[0].last_report["belief"]["history_digest"]
                == policies[1].last_report["belief"]["history_digest"]
            )
        finally:
            for p in policies:
                p.close()


@pytest.mark.parametrize("encounter", ["nibbits-weak", "slimes-weak", "sludge-spinner"])
def test_complete_planned_battle_consumes_public_confirmed_history(encounter):
    with Simulator(encounter, 1) as env:
        policy = PlanningPolicy("hierarchical", 773, encounter, config())
        events = []
        try:
            for step in range(100):
                before = env.observe()
                decision = policy.decide(before)
                assert policy.last_report["model_calls"] <= policy.config.search_calls
                assert env.observe() == before
                action = next(
                    a
                    for a in before.legal_actions
                    if a.action_id == decision.selected_action_id
                )
                result = env.step(action.action_id, before.decision_id)
                event = policy.observe_transition(before, action, result)
                if event:
                    events.append(event)
                if result.terminated or result.truncated:
                    break
            else:
                pytest.fail("Planned battle did not terminate within test bound")
            assert events[-1]["termination_reason"] == "terminal"
            assert sum(e["duration"] for e in events) == step + 1
            assert sum(e["cumulative_reward"] for e in events) == result.reward
            assert not policy.belief.particles
        finally:
            policy.close()


def test_actual_manual_action_conditions_belief_and_terminates_goal():
    with Simulator() as env:
        policy = PlanningPolicy("hierarchical", 773, "nibbits-weak", config())
        try:
            before = env.observe()
            decision = policy.decide(before)
            actual = next(
                a
                for a in before.legal_actions
                if a.action_id != decision.selected_action_id and a.kind == "play_card"
            )
            result = env.step(actual.action_id, before.decision_id)
            event = policy.observe_transition(before, actual, result, manual=True)
            assert (
                event["termination_reason"] == "manual_override"
                and event["duration"] == 1
            )
            policy.decide(result.observation)
            assert policy.belief.steps == 1
            assert all(
                public_hash(w.observe()) == public_hash(result.observation)
                for w in policy.belief.particles
            )
        finally:
            policy.close()


def test_depletion_and_low_budget_are_explicit_heuristic_fallbacks():
    with Simulator() as env:
        for cfg, reason in [
            (config(search_calls=0), "zero_search_budget"),
            (config(search_calls=1), "budget_before_all_actions"),
        ]:
            policy = PlanningPolicy("rollout", 773, "nibbits-weak", cfg)
            try:
                d = policy.decide(env.observe())
                assert d.score_semantics == "heuristic_points_fallback"
                assert policy.last_report["fallback_reason"] == reason
                assert policy.last_report["model_calls"] <= cfg.search_calls
            finally:
                policy.close()
        policy = PlanningPolicy("rollout", 773, "nibbits-weak", config())
        try:
            obs = env.observe()
            impossible = obs.model_copy(
                update={"player": obs.player.model_copy(update={"gold": 999})}
            )
            policy.decide(impossible)
            assert policy.last_report["fallback_reason"] == "initialization_depleted"
            assert policy.last_report["belief"]["initializations"] == 512
            assert not policy.belief.particles
        finally:
            policy.close()


def test_rejected_history_never_recovers_from_privileged_state():
    with Simulator() as env:
        belief = HistoryBelief(
            "nibbits-weak", 998, particles=1, init_attempts=512, update_attempts=4
        )
        try:
            before = env.observe()
            belief.initialize(before)
            action = before.legal_actions[0]
            after = env.step(action.action_id, before.decision_id).observation
            impossible = after.model_copy(
                update={"player": after.player.model_copy(update={"gold": 999})}
            )
            belief.advance(before, action, impossible)
            assert not belief.particles
            assert belief.report["reason"] == "history_particles_depleted"
            assert belief.report["model_calls"] <= 4
        finally:
            belief.close()


def test_planner_configuration_rejects_unbounded_or_nonfinite_work():
    for kwargs in [
        {"particles": 100},
        {"search_calls": -1},
        {"search_calls": True},
        {"exploration": float("nan")},
        {"max_wall_ms": 0},
    ]:
        with pytest.raises(ValidationError):
            PlanningConfig(**kwargs)


def test_goal_termination_duration_and_terminal_precedence():
    with Simulator() as env:
        obs = env.observe()
        hierarchy = TacticalHierarchy(max_actions=1)
        goal = hierarchy.select(obs)
        assert hierarchy.select(obs) is goal
        result = env.step("end_turn", obs.decision_id)
        event = hierarchy.observe_transition(
            obs, result.observation, result.reward, False
        )
        assert event["termination_reason"] == "turn_boundary" and event["duration"] == 1
        assert hierarchy.current is None


def test_failed_particle_propagation_releases_every_native_branch(monkeypatch):
    with Simulator() as env:
        created, failed = [], []

        def factory(encounter, seed):
            world = Simulator(encounter, 1)  # deliberate matched test fixture
            created.append(world)
            return world

        belief = HistoryBelief("nibbits-weak", 1, particles=2, factory=factory)
        before = env.observe()
        belief.initialize(before)
        action = before.legal_actions[0]
        after = env.step(action.action_id, before.decision_id).observation

        def broken_step(world, *args, **kwargs):
            failed.append(world)
            raise RuntimeError("injected model failure")

        monkeypatch.setattr(Simulator, "step", broken_step)
        with pytest.raises(RuntimeError, match="injected model failure"):
            belief.advance(before, action, after)
        assert failed and all(w.handle == -1 for w in created + failed)
        assert not belief.particles


def test_expired_budget_performs_no_initialization(monkeypatch):
    with Simulator() as env:
        policy = PlanningPolicy("rollout", 773, "nibbits-weak", config())
        monkeypatch.setattr(
            HistoryBelief, "expired", staticmethod(lambda deadline: True)
        )
        try:
            policy.decide(env.observe())
            assert policy.last_report["timed_out"]
            assert policy.last_report["model_calls"] == 0
            assert policy.last_report["belief"]["initializations"] == 0
            assert policy.last_report["fallback_reason"] == "initialization_depleted"
        finally:
            policy.close()
