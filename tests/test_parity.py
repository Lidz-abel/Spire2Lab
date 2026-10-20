"""Comparator logic tests; fixtures do not establish any local-game parity."""

import copy
import json

import pytest
from sts2lab.contracts import Action
from sts2lab.original import normalize_original
from sts2lab.parity import compare_observations, action_signature, compare_traces
from sts2lab.runtime import Lab
from sts2lab.contracts import StepRequest
from test_original import raw_state, SyntheticGame


def test_independent_projection_detects_dynamic_errors_and_ignores_borrowed_values():
    obs, _ = normalize_original(raw_state(), "original")
    modified = obs.model_copy(
        update={
            "hand": [
                obs.hand[0].model_copy(
                    update={"printed_damage": 999, "name": "different language"}
                ),
                *obs.hand[1:],
            ]
        }
    )
    assert compare_observations(obs, modified) is None
    modified = obs.model_copy(
        update={"player": obs.player.model_copy(update={"energy": 2})}
    )
    assert compare_observations(obs, modified)["path"] == "/player/energy"
    modified = obs.model_copy(
        update={"hand": [obs.hand[0].model_copy(update={"cost": 2}), *obs.hand[1:]]}
    )
    assert compare_observations(obs, modified)["path"] == "/hand/0/cost"
    modified = obs.model_copy(update={"legal_actions": obs.legal_actions[:-1]})
    assert compare_observations(obs, modified)["path"] == "/legal_actions"


def test_action_transport_ids_and_enemy_slot_gaps_do_not_change_semantics():
    obs, _ = normalize_original(raw_state(), "original")
    action = obs.legal_actions[0]
    renamed_enemy = obs.enemies[0].model_copy(update={"ref": "sim:enemy:2"})
    sim = obs.model_copy(update={"enemies": [renamed_enemy]})
    sim_action = action.model_copy(
        update={"action_id": "play:0:2", "target_ref": renamed_enemy.ref}
    )
    assert action_signature(obs, action.model_dump()) == action_signature(
        sim, sim_action.model_dump()
    )


def test_unavailable_fields_are_explicit_and_cannot_hide_combat_differences():
    raw = raw_state()
    obs, _ = normalize_original(raw, "before")
    bad = obs.model_copy(update={"unavailable_fields": ["player.energy"]})
    with pytest.raises(ValueError, match="cannot omit"):
        compare_observations(bad, obs)
    raw["state_type"] = "rewards"
    terminal, _ = normalize_original(raw, "after", previous=obs)
    candidate = terminal.model_copy(
        update={
            "unavailable_fields": [],
            "player": terminal.player.model_copy(update={"energy": 2, "max_energy": 3}),
            "hand": obs.hand,
        }
    )
    assert compare_observations(terminal, candidate) is None
    tampered = terminal.model_copy(
        update={"unavailable_fields": [*terminal.unavailable_fields, "player.hp"]}
    )
    with pytest.raises(ValueError, match="Unrecognized omission"):
        compare_observations(tampered, candidate)


@pytest.mark.asyncio
async def test_synthetic_original_trace_cannot_pass_acceptance(tmp_path):
    game = SyntheticGame()
    original = Lab(tmp_path / "original", original_factory=game.factory(tmp_path))
    native = Lab(tmp_path / "native")
    try:
        r = await original.new_session(backend="original_game")
        await original.step(
            StepRequest(
                request_id="test",
                decision_id=r["observation"]["decision_id"],
                action_id="play:0:0",
            )
        )
        n = await native.new_session()
        report = compare_traces(
            original.trace_path(r["metadata"]["run_id"]),
            native.trace_path(n["metadata"]["run_id"]),
        )
        assert not report["passed"] and report["status"] == "evidence_incomplete"
        assert "Synthetic" in report["error"]
        assert report["global_game_parity_proven"] is False
    finally:
        await original.close()
        await native.close()
