"""Synthetic bridge contract tests, never evidence of local original-game parity."""

import asyncio
import copy
import json

import httpx
import pytest

from sts2lab.bridge import BridgeClient, OutcomeUnknown
from sts2lab.contracts import StepRequest
from sts2lab.original import (
    normalize_original,
    verify_scope,
    UnsupportedState,
    OriginalEnvironment,
    parse_intent,
)
from sts2lab.runtime import Lab
from sts2lab.simulator import ROOT
from sts2lab.traces import read_trace


def raw_state():
    def card(entry, index=None):
        item = {
            "id": entry,
            "cost": "2" if entry == "BASH" else "1",
            "is_upgraded": False,
            "lab_has_enchantment": False,
            "target_type": "Self" if entry == "DEFEND_IRONCLAD" else "AnyEnemy",
            "can_play": True,
        }
        if index is not None:
            item["index"] = index
        return item

    deck = (
        [card("STRIKE_IRONCLAD") for _ in range(5)]
        + [card("DEFEND_IRONCLAD") for _ in range(4)]
        + [card("BASH")]
    )
    hand = [
        card("STRIKE_IRONCLAD", 0),
        card("DEFEND_IRONCLAD", 1),
        card("BASH", 2),
        card("STRIKE_IRONCLAD", 3),
        card("DEFEND_IRONCLAD", 4),
    ]
    draw = [card("STRIKE_IRONCLAD") for _ in range(3)] + [
        card("DEFEND_IRONCLAD") for _ in range(2)
    ]
    return {
        "lab_protocol": 1,
        "lab_instance_id": "synthetic-process",
        "game_assembly_sha256": "synthetic-hash",
        "lab_state_token": "before",
        "lab_action_ready": True,
        "lab_settled": True,
        "lab_last_request_id": None,
        "state_type": "monster",
        "run": {"ascension": 0, "floor": 2},
        "player": {
            "lab_character_id": "IRONCLAD",
            "hp": 80,
            "max_hp": 80,
            "block": 0,
            "energy": 3,
            "max_energy": 3,
            "gold": 99,
            "status": [],
            "relics": [{"id": "BURNING_BLOOD", "counter": None}],
            "potions": [],
            "deck": deck,
            "hand": hand,
            "draw_pile": draw,
            "draw_pile_count": 5,
            "discard_pile": [],
            "discard_pile_count": 0,
            "exhaust_pile": [],
            "exhaust_pile_count": 0,
        },
        "battle": {
            "round": 1,
            "is_play_phase": True,
            "enemies": [
                {
                    "entity_id": "NIBBIT_0",
                    "hp": 42,
                    "max_hp": 42,
                    "block": 0,
                    "status": [],
                    "intents": [{"type": "Attack", "label": "12"}],
                }
            ],
        },
    }


def test_projection_is_player_visible_and_semantic():
    raw = raw_state()
    verify_scope(raw, "nibbits-weak", opening=True)
    obs, mapping = normalize_original(raw, "decision")
    assert obs.turn == 0 and obs.player.energy == 3
    assert mapping["play:0:0"] == {
        "action": "play_card",
        "card_index": 0,
        "target": "NIBBIT_0",
    }
    assert mapping["play:1:-"] == {"action": "play_card", "card_index": 1}
    assert obs.enemies[0].intents[0].magnitude == 12
    # Hidden/raw metadata and localized labels cannot affect actor inputs.
    altered = copy.deepcopy(raw)
    altered["seed"] = "SECRET"
    altered["rng"] = [999]
    altered["player"]["draw_pile_ordered"] = list(reversed(raw["player"]["draw_pile"]))
    altered["player"]["draw_pile"].reverse()
    altered["player"]["hand"][0]["description"] = "SECRET"
    altered["battle"]["enemies"][0]["name"] = "Localized enemy"
    assert normalize_original(altered, "decision")[0] == obs
    assert "SECRET" not in obs.model_dump_json()


def test_missing_fields_are_never_invented():
    raw = raw_state()
    before, _ = normalize_original(raw, "before")
    del raw["player"]["draw_pile"][0]["id"]
    with pytest.raises(UnsupportedState, match="required field: id"):
        normalize_original(raw, "bad")
    raw = raw_state()
    raw["state_type"] = "rewards"
    for key in (
        "energy",
        "max_energy",
        "hand",
        "draw_pile",
        "discard_pile",
        "exhaust_pile",
    ):
        del raw["player"][key]
    terminal, mapping = normalize_original(raw, "after", previous=before)
    assert terminal.outcome == "won" and not mapping
    assert terminal.player.energy is None and "hand" in terminal.unavailable_fields
    with pytest.raises(UnsupportedState, match="Attach at a live"):
        normalize_original(raw, "bad")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw["run"].update(ascension=8),
        lambda raw: raw["player"].update(lab_character_id="THE_SILENT"),
        lambda raw: raw["player"]["deck"].pop(),
        lambda raw: raw["battle"]["enemies"].append(
            copy.deepcopy(raw["battle"]["enemies"][0])
        ),
    ],
)
def test_out_of_scope_openings_are_refused(mutation):
    raw = raw_state()
    mutation(raw)
    with pytest.raises(UnsupportedState):
        verify_scope(raw, "nibbits-weak", opening=True)


def test_attack_and_unshown_intents_from_upstream_capture():
    # This is an upstream A8 capture, NOT this user's game or an A0 acceptance trace.
    raw = json.loads(
        (
            ROOT / "vendor/sts2/tests/fixtures/combat/QS2GYXRKWN-nibbits-a8.json"
        ).read_text()
    )
    enemies = raw["battle"]["enemies"]
    attack, defend = map(parse_intent, enemies[0]["intents"])
    buff = parse_intent(enemies[1]["intents"][0])
    assert attack.magnitude == 6 and attack.hits == 1
    assert defend.magnitude is None and buff.magnitude is None
    assert parse_intent({"type": "Attack", "label": "5×2"}).magnitude == 10
    with pytest.raises(UnsupportedState):
        parse_intent({"type": "Attack", "label": "?"})

    slimes = json.loads(
        (
            ROOT / "vendor/sts2/tests/fixtures/combat/QS2GYXRKWN-large-slimes-a8.json"
        ).read_text()
    )
    status_intents = [
        parse_intent(e["intents"][0]) for e in slimes["battle"]["enemies"][:2]
    ]
    assert [i.type for i in status_intents] == ["StatusCard", "StatusCard"]
    assert [i.magnitude for i in status_intents] == [1, 2]
    assert all(not i.deals_damage for i in status_intents)


class SyntheticGame:
    def __init__(self, *, lose_response=False, gate=None):
        self.raw = raw_state()
        self.posts = []
        self.lose_response = lose_response
        self.gate = gate
        self.post_started = asyncio.Event()

    async def handle(self, request):
        if request.method == "GET":
            return httpx.Response(200, json=self.raw)
        command = json.loads(request.content)
        self.posts.append(command)
        self.post_started.set()
        if self.gate is not None:
            await self.gate.wait()
        assert command["action"] == "play_card" and command["card_index"] == 0
        assert command["target"] == "NIBBIT_0"
        p = self.raw["player"]
        used = p["hand"].pop(0)
        for index, c in enumerate(p["hand"]):
            c["index"] = index
        p["discard_pile"].append(used)
        p["discard_pile_count"] = 1
        p["energy"] = 2
        self.raw["battle"]["enemies"][0]["hp"] = 36
        self.raw.update(
            lab_state_token="after", lab_last_request_id=command["lab_request_id"]
        )
        if self.lose_response:
            raise httpx.ReadTimeout("synthetic lost response", request=request)
        return httpx.Response(200, json={"status": "ok"})

    def factory(self, tmp_path):
        async def attach(encounter):
            return await OriginalEnvironment.attach(
                encounter,
                client=BridgeClient(
                    "synthetic-hash", transport=httpx.MockTransport(self.handle)
                ),
                manifest={
                    "game_assembly_sha256": "synthetic-hash",
                    "evidence_kind": "synthetic_transport_fixture",
                },
                raw_dir=tmp_path / "private-raw",
            )

        return attach


@pytest.mark.asyncio
async def test_runtime_reconciles_once_without_reposting(tmp_path):
    game = SyntheticGame(lose_response=True)
    lab = Lab(tmp_path / "runs", original_factory=game.factory(tmp_path))
    try:
        state = await lab.new_session(backend="original_game", seed=777)
        assert state["metadata"]["seed"] is None
        req = StepRequest(
            request_id="one-command",
            decision_id=state["observation"]["decision_id"],
            action_id="play:0:0",
        )
        with pytest.raises(OutcomeUnknown):
            await lab.step(req)
        assert lab.view()["status"] == "awaiting_confirmation"
        with pytest.raises(OutcomeUnknown):
            await lab.step(req)
        with pytest.raises(OutcomeUnknown):
            await lab.new_session()
        result = await lab.reconcile()
        assert result["status"] == "paused" and len(result["history"]) == 1
        assert result["observation"]["enemies"][0]["hp"] == 36
        assert result["pending_request_id"] is None and len(game.posts) == 1
        assert await lab.step(req) == result
        events = read_trace(lab.trace_path(result["metadata"]["run_id"]))
        assert sum(e["kind"] == "transition" for e in events) == 1
        assert sum(e["kind"] == "action_outcome_unknown" for e in events) == 1
        assert len(list((tmp_path / "private-raw").glob("*.json"))) == 2
    finally:
        await lab.close()


@pytest.mark.asyncio
async def test_inflight_view_pause_and_reset_are_safe(tmp_path):
    gate = asyncio.Event()
    game = SyntheticGame(gate=gate)
    lab = Lab(tmp_path / "runs", original_factory=game.factory(tmp_path))
    task = None
    try:
        state = await lab.new_session(backend="original_game")
        await lab.control(True)
        req = StepRequest(
            request_id="delayed",
            decision_id=state["observation"]["decision_id"],
            action_id="play:0:0",
        )
        task = asyncio.create_task(lab.step(req, automatic=True))
        await asyncio.wait_for(game.post_started.wait(), timeout=1)
        assert lab.view()["status"] == "executing"
        paused = await asyncio.wait_for(lab.control(False), timeout=0.2)
        assert paused["resume_after_step"] is False
        with pytest.raises(ValueError, match="in progress"):
            await lab.new_session()
        gate.set()
        result = await task
        assert result["status"] == "paused" and len(game.posts) == 1
    finally:
        gate.set()
        if task and not task.done():
            await task
        await lab.close()


def test_original_api_uses_adapter_and_reconcile_route(tmp_path):
    from fastapi.testclient import TestClient
    from sts2lab.server import create_app

    game = SyntheticGame(lose_response=True)
    with TestClient(
        create_app(tmp_path / "runs", original_factory=game.factory(tmp_path))
    ) as client:
        response = client.post("/api/session", json={"backend": "original_game"})
        assert response.status_code == 200
        state = response.json()
        command = {
            "request_id": "api-lost",
            "decision_id": state["observation"]["decision_id"],
            "action_id": "play:0:0",
        }
        result = client.post("/api/step", json=command)
        assert result.status_code == 409 and result.json()["outcome_unknown"]
        assert client.get("/api/state").json()["status"] == "awaiting_confirmation"
        confirmed = client.post("/api/reconcile", json={})
        assert confirmed.status_code == 200 and confirmed.json()["status"] == "paused"
        assert client.get("/api/runs").json()[0]["backend"] == "original_game"
        assert len(game.posts) == 1


@pytest.mark.asyncio
async def test_archive_preserves_unknown_outcome_without_game_actions(tmp_path):
    from sts2lab.parity import _load

    game = SyntheticGame(lose_response=True)
    lab = Lab(tmp_path / "runs", original_factory=game.factory(tmp_path))
    try:
        state = await lab.new_session(backend="original_game")
        rid = state["metadata"]["run_id"]
        req = StepRequest(
            request_id="archive-unknown",
            decision_id=state["observation"]["decision_id"],
            action_id="play:0:0",
        )
        with pytest.raises(OutcomeUnknown):
            await lab.step(req)
        with pytest.raises(ValueError, match="stale_session"):
            await lab.archive("0" * 32)
        archived = await lab.archive(rid)
        assert archived["status"] == "closed" and archived["decision"] is None
        assert archived["observation"]["outcome"] == "ongoing"
        assert not archived["history"] and len(game.posts) == 1
        events = read_trace(lab.trace_path(rid))
        ending = events[-1]
        assert ending["kind"] == "session_archived"
        assert ending["data"]["game_outcome"] == "unknown"
        assert ending["data"]["unresolved_request_id"] == req.request_id
        with pytest.raises(ValueError, match="unresolved command"):
            _load(lab.trace_path(rid), "original_game")
        with pytest.raises(ValueError):
            await lab.step(req)
        new = await lab.new_session()
        assert (
            new["metadata"]["backend"] == "native_simulator"
            and new["status"] == "paused"
        )
        assert len(game.posts) == 1
    finally:
        await lab.close()
