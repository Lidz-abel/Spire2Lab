"""Independent public constraints, real transitions and native proposal cleanup."""

import pytest

from sts2lab.belief import HistoryBelief, public_hash
from sts2lab.contracts import semantic_state
from sts2lab.simulator import Simulator


@pytest.mark.parametrize("encounter", ["nibbits-weak", "slimes-weak", "sludge-spinner"])
@pytest.mark.parametrize("seed", [1, 7, 10])
def test_conditioned_proposals_match_opening_without_touching_actor(encounter, seed):
    with Simulator(encounter, seed) as actor:
        before = actor.observe()
        belief = HistoryBelief(encounter, 8831, particles=8, proposal="public_opening")
        try:
            report = belief.initialize(before)
            assert report["particles"] == 8 and report["initializations"] <= 512
            assert actor.observe() == before
            assert all(
                w.handle != actor.handle
                and public_hash(w.observe()) == public_hash(before)
                for w in belief.particles
            )
            assert all(
                w.branch_provenance.operation == "public_opening"
                for w in belief.particles
            )
            assert report["exact_posterior_claim"] is False
        finally:
            worlds = list(belief.particles)
            belief.close()
            assert all(w.handle == -1 for w in worlds)


def test_public_constructor_does_not_read_or_copy_actor_hidden_order():
    with Simulator() as actor, actor.sample_world(1) as hidden:
        a, b = actor.observe(), hidden.observe()
        assert semantic_state(a) == semantic_state(b)
        assert (
            actor._raw(debug=True)["debug_draw_order"]
            != hidden._raw(debug=True)["debug_draw_order"]
        )
        left, right = [], []
        for obs, worlds in [(a, left), (b, right)]:
            for seed in range(20, 30):
                with Simulator.from_public_opening("nibbits-weak", obs, seed) as world:
                    worlds.append(world._raw(debug=True)["debug_draw_order"])
        assert left == right
        assert len({str(order) for order in left}) > 1


def test_invalid_public_constraints_reject_and_release_every_proposal():
    with Simulator() as actor:
        obs = actor.observe()
        variants = [
            obs.model_copy(
                update={
                    "enemies": [
                        obs.enemies[0].model_copy(update={"hp": 999, "max_hp": 999})
                    ]
                }
            ),
            obs.model_copy(
                update={"player": obs.player.model_copy(update={"gold": 999})}
            ),
            obs.model_copy(update={"known_top": [obs.draw_pile[0]]}),
            obs.model_copy(
                update={
                    "hand": [
                        obs.hand[0].model_copy(update={"printed_damage": 999}),
                        *obs.hand[1:],
                    ]
                }
            ),
        ]
        # More than the native pool's capacity: rejected worlds must not leak handles.
        for i in range(270):
            assert (
                Simulator.from_public_opening(
                    "nibbits-weak", variants[i % len(variants)], i
                )
                is None
            )
        assert actor.observe() == obs
        with Simulator.from_public_opening("nibbits-weak", obs, 998) as valid:
            assert public_hash(valid.observe()) == public_hash(obs)


def test_conditioned_belief_still_rejects_an_impossible_transition():
    with Simulator("slimes-weak", 7) as actor:
        before = actor.observe()
        belief = HistoryBelief(
            "slimes-weak", 8831, particles=8, proposal="public_opening"
        )
        try:
            belief.initialize(before)
            action = before.legal_actions[0]
            result = actor.step(action.action_id, before.decision_id)
            after = result.observation.model_copy(
                update={
                    "player": result.observation.player.model_copy(update={"gold": 999})
                }
            )
            report = belief.advance(before, action, after)
            assert report["particles"] == 0 and report["model_calls"] == 128
            assert report["reason"] == "history_particles_depleted"
        finally:
            belief.close()
