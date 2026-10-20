import json
import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from sts2lab.contracts import semantic_state, digest
from sts2lab.simulator import Simulator, CONFIG
from sts2lab.policies import Policy
from sts2lab.gym_env import CombatEnv


def make_vector_env():
    return CombatEnv()


def test_initial_conditions_and_hidden_information_boundary():
    with Simulator() as env:
        obs = env.observe()
        assert obs.player.hp == 80
        assert len(obs.hand) + len(obs.draw_pile) == 10
        assert [r.type_id for r in obs.relics] == ["BurningBlood"]
        assert all(c.native_id != 10001 for c in obs.hand + obs.draw_pile)
        assert len({c.ref for c in obs.hand}) == len(obs.hand)
        assert "debug_seed" not in obs.model_dump_json()
        assert "debug_draw_order" not in obs.model_dump_json()
        # Same information set remains identical under hidden-state resampling.
        orders = set()
        original = digest(semantic_state(obs))
        for seed in range(20):
            with env.sample_world(seed) as fork:
                assert digest(semantic_state(fork.observe())) == original
                orders.add(
                    json.dumps(
                        fork._raw(debug=True)["debug_draw_order"], sort_keys=True
                    )
                )
        assert len(orders) > 1


def test_stale_and_illegal_commands_do_not_mutate():
    with Simulator() as env:
        before = env.observe()
        with pytest.raises(ValueError, match="illegal_action"):
            env.step("unknown", before.decision_id)
        assert semantic_state(before) == semantic_state(env.observe())
        env.step(before.legal_actions[0].action_id, before.decision_id)
        current = semantic_state(env.observe())
        with pytest.raises(ValueError, match="stale_decision"):
            env.step("end_turn", before.decision_id)
        assert current == semantic_state(env.observe())


def test_slime_visible_status_intent_survives_semantic_and_training_encoding():
    with Simulator("slimes-weak", 1) as env:
        statuses = [
            i
            for e in env.observe().enemies
            for i in e.intents
            if i.type == "StatusCard"
        ]
        assert len(statuses) == 1 and statuses[0].magnitude == 2
        assert statuses[0].hits is None and not statuses[0].deals_damage
    env = CombatEnv("slimes-weak")
    try:
        obs, _ = env.reset(seed=1)
        row = next(row for row in obs["enemies"] if row[4] == 6)
        assert list(row[5:8]) == [2, 0, 0]
    finally:
        env.close()


def test_exact_clone_restore_and_branch_isolation():
    with Simulator() as env, env.snapshot() as snapshot, env.snapshot() as fork:
        initial = semantic_state(env.observe())
        action = env.observe().legal_actions[0].action_id
        result = fork.step(action, fork.decision_id)
        assert semantic_state(env.observe()) == initial
        result2 = env.step(action, env.decision_id)
        assert semantic_state(result.observation) == semantic_state(result2.observation)
        old_id = env.decision_id
        restored = env.restore(snapshot)
        assert restored.decision_id != old_id
        assert semantic_state(restored) == initial


@pytest.mark.parametrize("encounter", CONFIG["encounters"])
@pytest.mark.parametrize("policy_name", ["random", "heuristic"])
def test_complete_legal_battle(encounter, policy_name):
    with Simulator(encounter, 3) as env:
        obs = env.observe()
        policy = Policy(policy_name)
        while obs.outcome == "ongoing":
            decision = policy.decide(obs)
            assert decision.selected_action_id in {
                a.action_id for a in obs.legal_actions
            }
            obs = env.step(decision.selected_action_id, obs.decision_id).observation
        assert obs.outcome in ("won", "lost")
        assert not obs.legal_actions


def test_gym_contract_and_masks():
    env = CombatEnv()
    try:
        check_env(env, skip_render_check=True)
        obs, info = env.reset(seed=3)
        assert env.observation_space.contains(obs)
        while True:
            action = int(np.flatnonzero(env.action_masks())[0])
            obs, reward, terminated, truncated, info = env.step(action)
            assert env.observation_space.contains(obs)
            if terminated or truncated:
                assert not obs["action_mask"].any()
                break
    finally:
        env.close()


def test_process_vector_sampling_is_isolated():
    from gymnasium.vector import AsyncVectorEnv

    vector = AsyncVectorEnv([make_vector_env, make_vector_env], context="spawn")
    try:
        obs, _ = vector.reset(seed=[2, 3])
        assert obs["hand"].shape == (2, 10, 7)
        for _ in range(6):
            actions = np.array([np.flatnonzero(mask)[0] for mask in obs["action_mask"]])
            obs, rewards, terminated, truncated, info = vector.step(actions)
        assert np.all(np.isfinite(rewards))
    finally:
        vector.close()
