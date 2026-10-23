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
        assert {c.type_id for c in obs.hand + obs.draw_pile} == {
            "STRIKE_IRONCLAD",
            "DEFEND_IRONCLAD",
            "BASH",
        }
        assert "native_id" not in obs.model_dump_json()
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
        row = next(
            row
            for row in obs["enemies"]
            if row[4] == env.vocabulary.token("intents", "StatusCard")
        )
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


def test_nibbit_slice_exposes_observed_defend_intent_without_changing_effects():
    # Minimal public facts from the local v0.107.1 capture after Bash, Strike,
    # end-turn (2026-10-23). Private raw captures stay outside the repository.
    with Simulator("nibbits-weak", 1) as env:
        policy = Policy("heuristic", 773)
        for _ in range(3):
            obs = env.observe()
            env.step(policy.decide(obs).selected_action_id, obs.decision_id)
        obs = env.observe()
        assert obs.turn == 1 and obs.player.hp == 68
        enemy = obs.enemies[0]
        assert enemy.hp == 25 and enemy.block == 0
        assert [i.type for i in enemy.intents] == ["Attack", "Defend"]
        assert enemy.intents[0].magnitude == 6
        assert enemy.intents[1].magnitude is None and enemy.intents[1].hits is None
        assert not enemy.intents[1].deals_damage
        # Merely observing must not apply the announced effect.
        assert env.observe() == obs
        after = env.step("end_turn", obs.decision_id).observation
        assert after.player.hp == 62 and after.enemies[0].block == 5
        assert [i.type for i in after.enemies[0].intents] == ["Buff"]


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


def test_starter_victory_includes_one_relic_heal_and_survives_restore():
    # Live seed-1 Nibbit trace: 68 HP before winning Strike, 74 at rewards.
    with Simulator("nibbits-weak", 1) as env:
        policy = Policy("heuristic", 773)
        for _ in range(10):
            before = env.observe()
            env.step(policy.decide(before).selected_action_id, before.decision_id)
        before = env.observe()
        assert before.player.hp == 68 and before.outcome == "ongoing"
        with env.snapshot() as pre_win:
            result = env.step(
                policy.decide(before).selected_action_id, before.decision_id
            )
            assert result.terminated and result.observation.outcome == "won"
            assert result.observation.player.hp == 74
            assert result.facts["player_hp_delta"] == 6
            assert env.observe() == result.observation
            with env.snapshot() as terminal:
                assert terminal.observe().player.hp == 74
                env.restore(terminal)
                assert env.observe().player.hp == 74
                with pytest.raises(ValueError, match="illegal_action"):
                    env.step("end_turn", env.decision_id)
            restored = env.restore(pre_win)
            again = env.step(
                policy.decide(restored).selected_action_id, restored.decision_id
            )
            assert again.observation.player.hp == 74


def test_random_victory_clears_block_only_after_winning_action():
    # Original seed-1 random policy: 64 HP and 5 block before the final Strike.
    with Simulator("nibbits-weak", 1) as env:
        policy = Policy("random", 773)
        for _ in range(16):
            before = env.observe()
            env.step(policy.decide(before).selected_action_id, before.decision_id)
        before = env.observe()
        assert before.player.hp == 64 and before.player.block == 5
        result = env.step(policy.decide(before).selected_action_id, before.decision_id)
        assert result.observation.outcome == "won"
        assert (
            result.observation.player.hp == 70 and result.observation.player.block == 0
        )


def test_starter_defeat_never_pays_victory_heal():
    with Simulator("nibbits-weak", 1) as env:
        while env.observe().outcome == "ongoing":
            env.step("end_turn", env.decision_id)
        assert env.observe().outcome == "lost" and env.observe().player.hp <= 0


def test_starter_combat_powers_expire_at_victory():
    # Original Sludge Spinner seed-1 random trace retains its combat power until
    # the winning Strike, then reports an empty power list at rewards.
    with Simulator("sludge-spinner", 1) as env:
        policy = Policy("random", 773)
        for _ in range(14):
            before = env.observe()
            env.step(policy.decide(before).selected_action_id, before.decision_id)
        before = env.observe()
        assert before.player.hp == 69 and before.player.powers
        result = env.step(policy.decide(before).selected_action_id, before.decision_id)
        assert result.observation.outcome == "won"
        assert (
            result.observation.player.hp == 75 and not result.observation.player.powers
        )


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
