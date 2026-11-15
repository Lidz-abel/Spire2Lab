"""Real simulator checks of no-op filtering and Gym episode-ending semantics."""

import numpy as np
import pytest

from sts2lab.gym_env import CombatEnv, MAX_ACTIONS
from sts2lab.policies import Policy
from sts2lab.simulator import CONFIG


def test_invalid_actions_preserve_state_and_are_excluded_from_training(monkeypatch):
    monkeypatch.setitem(CONFIG, "max_steps", 2)
    env = CombatEnv()
    try:
        initial, _ = env.reset(seed=3)
        before = env.sim.observe()
        for action in (-1, MAX_ACTIONS):
            with pytest.raises(ValueError, match="outside"):
                env.step(action)
            assert env.attempts == 0 and env.sim.observe() == before
        invalid = int(np.flatnonzero(initial["action_mask"] == 0)[0])
        encoded, reward, terminated, truncated, info = env.step(invalid)
        assert (reward, terminated, truncated) == (0.0, False, False)
        assert info["invalid_action"] and info["training_transition"] is False
        for key in initial:
            np.testing.assert_array_equal(encoded[key], initial[key])
        assert env.sim.observe() == before and env.sim.sequence == 0
        encoded, reward, terminated, truncated, info = env.step(invalid)
        assert (reward, terminated, truncated) == (0.0, False, True)
        assert info["training_transition"] is False
        assert env.sim.observe() == before and env.sim.observe().outcome == "ongoing"
        assert not encoded["action_mask"].any() and not env.action_masks().any()
        with pytest.raises(RuntimeError, match="Episode ended"):
            env.step(0)
        reset, _ = env.reset(seed=3)
        assert reset["action_mask"].any() and not env.done and env.attempts == 0
    finally:
        env.close()


@pytest.mark.parametrize("invalid_attempt_first", [False, True])
def test_time_limit_is_truncation_without_loss_reward(
    monkeypatch, invalid_attempt_first
):
    monkeypatch.setitem(CONFIG, "max_steps", 2 if invalid_attempt_first else 1)
    env = CombatEnv()
    try:
        initial, _ = env.reset(seed=3)
        if invalid_attempt_first:
            env.step(int(np.flatnonzero(initial["action_mask"] == 0)[0]))
        encoded, reward, terminated, truncated, info = env.step(0)
        assert (reward, terminated, truncated) == (0.0, False, True)
        assert info["reward_version"] == "terminal-win-v1"
        assert info.get("training_transition", True) is True
        assert not encoded["action_mask"].any() and not env.action_masks().any()
        assert env.sim.sequence == 1
        assert env.sim.truncated is (not invalid_attempt_first)
        assert env.sim.observe().outcome == (
            "ongoing" if invalid_attempt_first else "truncated"
        )
        with pytest.raises(RuntimeError, match="Episode ended"):
            env.step(0)
    finally:
        env.close()


@pytest.mark.parametrize("expected_outcome", ["won", "lost"])
def test_natural_terminal_takes_precedence_at_exact_attempt_limit(
    monkeypatch, expected_outcome
):
    def run():
        env = CombatEnv()
        policy = Policy("heuristic")
        try:
            env.reset(seed=3)
            while True:
                observation = env.sim.observe()
                action_id = (
                    "end_turn"
                    if expected_outcome == "lost"
                    else policy.decide(observation).selected_action_id
                )
                index = next(
                    i for i, a in enumerate(env.actions) if a.action_id == action_id
                )
                encoded, reward, terminated, truncated, info = env.step(index)
                if terminated or truncated:
                    assert terminated and not truncated
                    assert env.sim.observe().outcome == expected_outcome
                    assert reward == (1.0 if expected_outcome == "won" else -1.0)
                    assert info["reward_version"] == "terminal-win-v1"
                    assert (
                        not encoded["action_mask"].any()
                        and not env.action_masks().any()
                    )
                    with pytest.raises(RuntimeError, match="Episode ended"):
                        env.step(0)
                    return env.attempts
        finally:
            env.close()

    attempts = run()
    monkeypatch.setitem(CONFIG, "max_steps", attempts)
    assert run() == attempts
