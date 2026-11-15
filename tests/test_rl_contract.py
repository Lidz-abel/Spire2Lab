"""E1 contract evidence: synthetic boundaries and old development simulator cases."""

import copy
import json

import numpy as np
import pytest

from sts2lab.gym_env import CombatEnv
from sts2lab.policies import Policy
from sts2lab.rl_contract import (
    FEATURES,
    RECIPE_PATH,
    evaluation_cases,
    load_recipe,
    prepare_observation,
    validate_transition,
)
from sts2lab.simulator import CONFIG


@pytest.fixture
def initial():
    env = CombatEnv()
    try:
        obs, _ = env.reset(seed=3)
        yield obs
    finally:
        env.close()


def test_frozen_recipe_splits_and_budget():
    recipe = load_recipe()
    cases = {s: evaluation_cases(recipe, s) for s in ("train", "validation", "test")}
    assert [len(cases[s]) for s in cases] == [3000, 60, 300]
    assert len(set(sum(cases.values(), []))) == 3360
    assert recipe["smoke"]["target_valid_transitions"] == 8192
    assert recipe["formal_training"]["valid_transitions_per_seed"] is None
    assert not recipe["checkpoint"]["mid_episode_exact_resume"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r["environment_seed_ranges_inclusive"].update(test=[20010, 20030]),
        lambda r: r["environment_seed_ranges_inclusive"].update(test=[2001, 2030]),
        lambda r: r["environment_seed_ranges_inclusive"].update(test=[True, 3]),
        lambda r: r.update(vocabulary_sha256="bad"),
        lambda r: r.update(encoding_version="future"),
        lambda r: r.update(feature_version="future"),
        lambda r: r.update(excluded_historical_seed_ranges_inclusive=[]),
        lambda r: r["smoke"].update(hard_cap_valid_transitions=10001),
        lambda r: r["smoke"].update(test_split_enabled=True),
        lambda r: r["formal_training"].update(enabled=True),
    ],
)
def test_recipe_refuses_drift(tmp_path, mutation):
    recipe = json.loads(RECIPE_PATH.read_text())
    mutation(recipe)
    path = tmp_path / "recipe.json"
    path.write_text(json.dumps(recipe))
    with pytest.raises(ValueError):
        load_recipe(path)


def test_fixed_scaling_and_independent_arrays(initial):
    initial["player"][2] = 160  # intentionally > divisor: never clipped to one
    data = prepare_observation(initial)
    assert data["numeric"]["player"].dtype == np.float32
    assert data["numeric"]["player"][2] == 2
    np.testing.assert_array_equal(data["tokens"]["hand"][:, 0], initial["hand"][:, 0])
    assert data["numeric"]["hand"].shape == (10, 6)
    assert data["tokens"]["enemies"].shape == (6, 3)
    assert data["action_references"].dtype == np.int64
    initial["hand"][:] = 0
    assert data["tokens"]["hand"].any()


@pytest.mark.parametrize(
    "field", ["seed", "rng", "native_id", "decision_id", "facts", "snapshot"]
)
def test_private_fields_rejected(initial, field):
    initial[field] = 1
    with pytest.raises(ValueError, match="private metadata"):
        prepare_observation(initial)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda o: o["hand"].__setitem__((0, 0), 999),
        lambda o: o["enemies"].__setitem__((0, 4), 999),
        lambda o: o["hand"].__setitem__((9, 2), 1),
        lambda o: o["enemies"].__setitem__((0, 12), 0),
        lambda o: o["actions"].__setitem__((0, 1), 10),
        lambda o: o["actions"].__setitem__((0, 2), 5),
        lambda o: o["action_mask"].__setitem__(0, 2),
        lambda o: o["action_mask"].__setitem__(63, 1),
        lambda o: o["action_mask"].__setitem__(0, 0),
        lambda o: o["enemies"].__setitem__((0, 4), 0),
        lambda o: o.update(hand=o["hand"][:9]),
        lambda o: o.update(hand=o["hand"].astype(float)),
    ],
)
def test_bad_encoding_rejected(initial, mutation):
    mutation(initial)
    with pytest.raises(ValueError):
        prepare_observation(initial)


def test_zero_mask_is_only_value_input(initial):
    with pytest.raises(ValueError, match="boundary"):
        prepare_observation(initial, episode_done=True)
    initial["action_mask"][:] = 0
    assert not prepare_observation(initial, episode_done=True)["action_mask"].any()
    with pytest.raises(ValueError, match="boundary"):
        prepare_observation(initial)


@pytest.mark.parametrize(
    "terminated,truncated,reward,bootstrap,trace",
    [
        (False, False, 0.0, True, True),
        (False, True, 0.0, True, False),
        (True, False, 1.0, False, False),
        (True, False, -1.0, False, False),
    ],
)
def test_transition_boundary_table(
    initial, terminated, truncated, reward, bootstrap, trace
):
    after = copy.deepcopy(initial)
    if terminated or truncated:
        after["action_mask"][:] = 0
    record = validate_transition(
        initial,
        0,
        (
            after,
            reward,
            terminated,
            truncated,
            {"reward_version": "terminal-win-v1"},
        ),
    )
    assert record.bootstrap is bootstrap
    assert record.continue_trace is trace
    # Hand-calculated one-step TD target with final V=.25; reset V=99 is unrelated.
    target = record.reward + 0.99 * record.bootstrap * 0.25
    assert target == pytest.approx(reward + (0.2475 if bootstrap else 0))
    after["player"][0] = 999
    initial["player"][0] = 999
    assert record.next_observation["player"][0] == 80
    assert record.observation["player"][0] == 80


@pytest.mark.parametrize(
    "info",
    [
        {"reward_version": "future"},
        {"reward_version": "terminal-win-v1", "training_transition": False},
        {"reward_version": "terminal-win-v1", "invalid_action": True},
        {"reward_version": "terminal-win-v1", "final_obs": {}},
        {"reward_version": "terminal-win-v1", "final_observation": {}},
    ],
)
def test_bad_result_metadata_rejected(initial, info):
    with pytest.raises(ValueError):
        validate_transition(initial, 0, (initial, 0.0, False, False, info))


@pytest.mark.parametrize(
    "reward,terminated,truncated",
    [
        (1.0, False, False),
        (0.0, True, False),
        (-1.0, False, True),
        (float("nan"), False, False),
        (float("inf"), False, False),
        (1.0, True, True),
    ],
)
def test_false_rewards_and_terminal_flags_rejected(
    initial, reward, terminated, truncated
):
    with pytest.raises(ValueError):
        validate_transition(
            initial,
            0,
            (
                initial,
                reward,
                terminated,
                truncated,
                {"reward_version": "terminal-win-v1"},
            ),
        )


@pytest.mark.parametrize("action", [-1, 64, 63, True, 0.5])
def test_invalid_selected_action_rejected(initial, action):
    with pytest.raises(ValueError, match="not legal"):
        validate_transition(
            initial,
            action,
            (initial, 0.0, False, False, {"reward_version": "terminal-win-v1"}),
        )


def test_actual_truncation_keeps_final_observation_before_reset(monkeypatch):
    monkeypatch.setitem(CONFIG, "max_steps", 1)
    env = CombatEnv()
    try:
        initial, _ = env.reset(seed=3)
        result = env.step(0)
        record = validate_transition(initial, 0, result)
        assert record.truncated and record.bootstrap and not record.continue_trace
        final_energy = record.next_observation["player"][3]
        reset, _ = env.reset(seed=3)
        assert final_energy < reset["player"][3]
        assert not record.next_observation["action_mask"].any()
        assert reset["action_mask"].any()
    finally:
        env.close()


@pytest.mark.parametrize("encounter", ["nibbits-weak", "slimes-weak", "sludge-spinner"])
@pytest.mark.parametrize("win", [True, False])
def test_old_development_battles_cross_contract(encounter, win):
    env = CombatEnv(encounter)
    policy = Policy("heuristic")
    try:
        observation, _ = env.reset(seed=3)
        for _ in range(300):
            selected = (
                policy.decide(env.sim.observe()).selected_action_id
                if win
                else "end_turn"
            )
            action = next(
                i for i, a in enumerate(env.actions) if a.action_id == selected
            )
            result = env.step(action)
            record = validate_transition(observation, action, result)
            observation = record.next_observation
            if record.terminated or record.truncated:
                assert record.terminated and not record.truncated
                assert record.reward == (1.0 if win else -1.0)
                assert not record.bootstrap and not record.continue_trace
                break
        else:
            pytest.fail("No terminal state within frozen cap")
    finally:
        env.close()


def test_feature_shapes_match_existing_gym_contract():
    env = CombatEnv()
    assert all(
        env.observation_space[k].shape == shape for k, (shape, _, _) in FEATURES.items()
    )
