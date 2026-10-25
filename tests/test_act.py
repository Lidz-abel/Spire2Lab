"""Synthetic single-act contracts and control failures; not original acceptance."""

import asyncio
import copy
import json
from pathlib import Path
import shutil
import subprocess

import httpx
import pytest

from sts2lab.act_bridge import ActBridge
from sts2lab.act_contracts import normalize_act, check_continuity
from sts2lab.act_policy import ActPolicy
from sts2lab.act_runtime import ActLab
from sts2lab.bridge import BridgeError, OutcomeUnknown
from sts2lab.contracts import StepRequest, canonical_json
from sts2lab.traces import read_trace

ROOT = Path(__file__).resolve().parents[1]


def choice(kind="choose_map_node", index=0, target=None):
    command = {"action": kind}
    if index is not None:
        command["index"] = index
    if target is not None:
        command["target"] = target
    return {"Id": f"{kind}:{index}", "Kind": kind, "Label": kind, "Command": command}


def raw_state(phase="map", token="a" * 64):
    return {
        "lab_protocol": 1,
        "lab_instance_id": "i" * 32,
        "game_assembly_sha256": "g" * 64,
        "lab_mod_sha256": "m" * 64,
        "lab_state_token": token,
        "lab_profile_id": 2,
        "lab_capabilities": ["single_act_v1", "decision_images_v1"],
        "lab_act_settled": True,
        "lab_act_ready": True,
        "lab_settled": True,
        "lab_last_request_id": None,
        "lab_act": {
            "version": "single-act-v1",
            "status": "active",
            "initializer": "normal_seeded_non_saving",
            "should_save": False,
            "outcome": "ongoing",
            "seed": "SECRETSEED",
            "request_id": "start",
        },
        "state_type": phase,
        "run": {"act": 1, "floor": 1, "ascension": 0},
        "player": {
            "hp": 80,
            "max_hp": 80,
            "gold": 99,
            "lab_character_id": "IRONCLAD",
            "deck": [
                {
                    "id": "BASH",
                    "name": "Bash",
                    "type": "Attack",
                    "cost": "2",
                    "is_upgraded": False,
                }
            ],
            "relics": [],
            "potions": [],
            "max_potion_slots": 3,
        },
        "map": {
            "nodes": [
                {"col": 0, "row": 1, "type": "Shop", "children": [[0, 2]]},
                {"col": 0, "row": 2, "type": "RestSite", "children": []},
            ],
            "visited": [],
            "next_options": [{"index": 0, "col": 0, "row": 1, "type": "Shop"}],
        },
        "lab_act_choices": [choice()],
    }


@pytest.fixture(scope="module")
def csharp(tmp_path_factory):
    folder = tmp_path_factory.mktemp("act-csharp")
    sdk = ROOT / ".tools/dotnet/dotnet"
    dotnet = str(sdk) if sdk.exists() else shutil.which("dotnet")
    if not dotnet:
        pytest.skip(".NET SDK required for production contract tests")
    for source in (ROOT / "bridge/ActContract.cs", ROOT / "tests/act_contract.cs"):
        shutil.copy2(source, folder / source.name)
    (folder / "Check.csproj").write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable></PropertyGroup></Project>'
    )
    result = subprocess.run(
        [dotnet, "build", str(folder / "Check.csproj"), "-c", "Release"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    def call(cases):
        result = subprocess.run(
            [dotnet, str(folder / "bin/Release/net9.0/Check.dll")],
            input="\n".join(json.dumps(v) for v in cases) + "\n",
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        return [json.loads(v) for v in result.stdout.splitlines()]

    return call


def test_normal_start_contract_rejects_other_profiles_overrides_and_bad_identifiers(
    csharp,
):
    base = {
        "action": "lab_start_act",
        "lab_request_id": "request-1",
        "lab_expected_token": "a" * 64,
        "expected_game_sha256": "b" * 64,
        "expected_mod_sha256": "c" * 64,
        "profile_id": 2,
        "seed": "ACT001",
    }
    bad = [{k: v for k, v in base.items() if k != key} for key in base]
    bad += [
        {**base, k: v}
        for k, v in [
            ("profile_id", 1),
            ("profile_id", "2"),
            ("seed", ""),
            ("seed", "a b"),
            ("seed", "X" * 25),
            ("seed", "ACT\n"),
            ("lab_request_id", "a\nb"),
            ("expected_mod_sha256", "D" * 64),
            ("override_gold", 999),
        ]
    ]
    result = csharp([{"mode": "start", "data": v} for v in [base] + bad])
    assert result[0]["accepted"]
    assert all(not r["accepted"] for r in result[1:])


def test_busy_choice_boundary_is_explicit_not_arbitrary_idle_hash(csharp):
    cases = []
    for phase in ("monster", "shop", "hand_select", "card_select"):
        for visible, interactive, setup in (
            (True, True, True),
            (False, True, True),
            (True, False, True),
            (True, True, False),
        ):
            cases.append(
                {
                    "mode": "boundary",
                    "phase": phase,
                    "idle": False,
                    "visible": visible,
                    "interactive": interactive,
                    "setup_idle": setup,
                }
            )
    replies = csharp(cases)
    for case, reply in zip(cases, replies):
        expected = (
            case["phase"] in ("hand_select", "card_select")
            and case["visible"]
            and case["interactive"]
            and case["setup_idle"]
        )
        assert reply["result"]["boundary"] == ("player_choice" if expected else None)


def test_catalogue_uses_real_indexes_affordability_and_visible_selection(csharp):
    shop = raw_state("shop")
    shop["shop"] = {
        "lab_inventory_open": True,
        "lab_can_close": True,
        "can_proceed": True,
        "items": [
            {
                "index": 7,
                "category": "card",
                "price": 80,
                "is_stocked": True,
                "can_afford": True,
            },
            {
                "index": 8,
                "category": "card",
                "price": 120,
                "is_stocked": True,
                "can_afford": True,
            },
            {
                "index": 9,
                "category": "relic",
                "price": 20,
                "is_stocked": False,
                "can_afford": True,
            },
        ],
    }
    closed = copy.deepcopy(shop)
    closed["shop"]["lab_inventory_open"] = False
    closed["shop"]["lab_can_close"] = False
    closed["shop"]["lab_can_open"] = True
    select = raw_state("card_select")
    select["card_select"] = {
        "cards": [
            {"index": 3, "name": "Bash", "lab_selectable": True},
            {"index": 4, "name": "Disabled", "lab_selectable": False},
        ],
        "can_confirm": False,
    }
    preview = copy.deepcopy(select)
    preview["card_select"].update(preview_showing=True, can_confirm=True)
    replies = csharp(
        [{"mode": "choices", "data": s} for s in (shop, closed, select, preview)]
    )
    assert [c["Id"] for c in replies[0]["result"]] == [
        "shop_purchase:7",
        "lab_close_shop",
    ]
    assert [c["Kind"] for c in replies[1]["result"]] == ["lab_open_shop", "proceed"]
    assert [c["Id"] for c in replies[2]["result"]] == ["select_card:3"]
    assert [c["Kind"] for c in replies[3]["result"]] == ["confirm_selection"]


def test_public_projection_drops_privileged_fields_and_order():
    a = raw_state()
    b = copy.deepcopy(a)
    for raw in (a, b):
        raw["player"]["draw_pile"] = [
            {"id": "STRIKE", "is_upgraded": False},
            {"id": "BASH", "is_upgraded": False},
        ]
    b["player"]["draw_pile"].reverse()
    b["lab_act"]["seed"] = "DIFFERENT"
    b["rng_state"] = {"future": 123}
    b["player"]["draw_pile_ordered"] = ["SECRET"]
    b["player"]["deck"][0]["hidden"] = "SECRET"
    b["map"]["nodes"][0]["future_event"] = "SECRET"
    oa, ma = normalize_act(a, "decision")
    ob, mb = normalize_act(b, "decision")
    assert oa == ob and ma == mb
    assert "SECRET" not in canonical_json(ob)
    p, q = ActPolicy().decide(oa), ActPolicy().decide(ob)
    p.pop("elapsed_ms")
    q.pop("elapsed_ms")
    assert p == q
    del b["player"]["deck"]
    with pytest.raises(ValueError, match="missing: deck"):
        normalize_act(b, "decision")


def test_terminal_and_route_checks_do_not_turn_starter_rewards_into_act_success():
    s = raw_state()
    s["lab_act"]["outcome"] = "act_complete"
    s["lab_act_choices"] = []
    with pytest.raises(ValueError, match="without observed boss"):
        normalize_act(s, "d")
    s = raw_state("rewards")
    s["rewards"] = {"items": [], "can_proceed": True}
    s["lab_act_choices"] = [choice("proceed", None)]
    obs, _ = normalize_act(s, "d")
    assert obs.outcome == "ongoing"
    earlier = obs.model_copy(update={"floor": 0})
    with pytest.raises(ValueError, match="regressed"):
        check_continuity(obs, earlier, obs.legal_actions[0])


@pytest.mark.asyncio
async def test_act_transport_timeout_never_reposts_and_requires_our_ack():
    before = raw_state()
    after = raw_state(token="b" * 64)
    posted = []
    advanced = False

    def handle(request):
        if request.method == "POST":
            posted.append(json.loads(request.content))
            raise httpx.ReadTimeout("lost reply", request=request)
        return httpx.Response(200, json=after if advanced else before)

    client = ActBridge(
        "g" * 64, mod_sha256="m" * 64, transport=httpx.MockTransport(handle)
    )
    try:
        with pytest.raises(OutcomeUnknown):
            await client.choose("choose_map_node:0", "a" * 64, request_id="r1")
        with pytest.raises(OutcomeUnknown):
            await client.choose("choose_map_node:0", "a" * 64, request_id="r1")
        advanced = True
        after["lab_last_request_id"] = "someone-else"
        with pytest.raises(OutcomeUnknown):
            await client.reconcile(timeout=0.01)
        after["lab_last_request_id"] = "r1"
        assert (await client.reconcile())["lab_state_token"] == "b" * 64
        assert len(posted) == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_act_rejects_stale_or_unadvertised_command_without_post():
    calls = []

    def handle(request):
        calls.append(request.method)
        return httpx.Response(200, json=raw_state())

    client = ActBridge("g" * 64, transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(BridgeError, match="stale"):
            await client.choose("choose_map_node:0", "old")
        with pytest.raises(BridgeError, match="illegal"):
            await client.choose("debug_add_card:0", "a" * 64)
        assert calls == ["GET", "GET"]
    finally:
        await client.close()


class FakeActBridge:
    pending = None

    def __init__(self):
        self.steps = []
        self.block = asyncio.Event()
        self.block.set()
        self.s = raw_state()

    async def start_act(self, seed, request_id):
        return copy.deepcopy(self.s)

    async def choose(self, choice_id, token, request_id):
        self.steps.append(choice_id)
        await self.block.wait()
        state = raw_state("shop", "b" * 64)
        state["run"]["floor"] = 2
        state["shop"] = {"lab_inventory_open": True, "can_proceed": True, "items": []}
        state["lab_act_choices"] = [choice("proceed", None)]
        return state

    async def capture_image(self, raw):
        raise BridgeError("synthetic fixture has no pixels")

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_act_pause_during_command_stops_next_step_and_duplicate_is_cached(
    tmp_path,
):
    bridge = FakeActBridge()
    lab = ActLab(tmp_path / "act-runs", factory=lambda: (bridge, {"fixture": True}))
    await lab.start("ACT001")
    assert lab.status == "paused" and lab.decision_image["status"] == "unavailable"
    request = StepRequest(request_id="r1", decision_id=lab.observation.decision_id)
    await lab.control(True)
    bridge.block.clear()
    task = asyncio.create_task(lab.step(request, automatic=True))
    await asyncio.sleep(0.01)
    assert lab.status == "executing"
    await lab.control(False)
    bridge.block.set()
    await task
    assert lab.status == "paused" and not lab.running and len(bridge.steps) == 1
    await lab.step(request)
    assert len(bridge.steps) == 1
    with pytest.raises(ValueError, match="conflict"):
        await lab.step(request.model_copy(update={"action_id": "a0"}))
    events = read_trace(lab.trace_path(lab.run_id))
    assert len([e for e in events if e["kind"] == "transition"]) == 1
    assert lab.history[0]["phase"] == "map"
    await lab.archive(lab.run_id)
    assert read_trace(lab.trace_path(lab.run_id))[-1]["data"]["truncated"] is True


def test_policy_goal_persists_then_records_manual_override():
    obs, _ = normalize_act(raw_state(), "d1")
    policy = ActPolicy()
    first = policy.decide(obs)
    second = policy.decide(obs.model_copy(update={"decision_id": "d2"}))
    assert first["goal"]["goal_id"] == second["goal"]["goal_id"]
    third = policy.decide(
        obs.model_copy(update={"decision_id": "d3"}), interrupted=True
    )
    assert third["ended_goal"]["termination_reason"] == "manual_override"
    assert third["goal"]["goal_id"] != first["goal"]["goal_id"]


def test_shop_exit_does_not_reopen_inventory_forever():
    state = raw_state("shop")
    state["shop"] = {"items": [], "lab_inventory_open": True, "lab_can_close": True}
    state["lab_act_choices"] = [choice("lab_close_shop", None)]
    before, _ = normalize_act(state, "d1")
    state["shop"] = {
        "items": [],
        "lab_inventory_open": False,
        "lab_can_open": True,
        "can_proceed": True,
    }
    state["lab_act_choices"] = [choice("lab_open_shop", None), choice("proceed", None)]
    after, _ = normalize_act(state, "d2")
    policy = ActPolicy()
    assert policy.decide(after)["selected_action_id"] == "a0"
    policy.observe_transition(before, before.legal_actions[0], after)
    assert policy.decide(after)["selected_action_id"] == "a1"


def test_unknown_choice_mechanic_stops_instead_of_guessing():
    state = raw_state("card_select")
    state["card_select"] = {"screen_type": "UnseenMechanic", "cards": []}
    state["lab_act_choices"] = [choice("select_card", 0)]
    obs, mapping = normalize_act(state, "d")
    assert obs.unsupported_reason and not obs.legal_actions and not mapping
    assert ActPolicy().decide(obs) is None
    state["lab_act_choices"] = [choice("debug_add_card", 0)]
    with pytest.raises(ValueError, match="Unsupported guarded action"):
        normalize_act(state, "d")


def test_act_http_ownership_and_stored_replay_do_not_touch_game(tmp_path):
    from fastapi.testclient import TestClient
    from sts2lab.server import create_app

    bridge = FakeActBridge()
    app = create_app(tmp_path / "runs", act_factory=lambda: (bridge, {"fixture": True}))
    with TestClient(app) as client:
        assert client.get("/act").status_code == 200
        started = client.post("/api/act/start", json={"seed": "ACT001"})
        assert started.status_code == 200, started.text
        view = started.json()
        assert view["status"] == "paused"
        assert (
            client.post("/api/session", json={"backend": "original_game"}).status_code
            == 409
        )
        assert client.post("/api/act/start", json={"seed": "ACT002"}).status_code == 409
        request = {
            "request_id": "http-1",
            "decision_id": view["observation"]["decision_id"],
        }
        assert client.post("/api/act/step", json=request).json()["status"] == "paused"
        assert len(bridge.steps) == 1
        run_id = view["run_id"]
        assert (
            client.post("/api/act/archive", json={"run_id": run_id}).status_code == 200
        )
        for _ in range(3):
            events = client.get(f"/api/act/runs/{run_id}").json()
            assert events[-1]["kind"] == "session_closed"
            assert (
                client.get(f"/api/act/runs/{run_id}/images/{'a'*64}.png").status_code
                == 404
            )
        assert len(bridge.steps) == 1
        assert (
            client.post(
                "/api/act/start",
                json={"seed": "ACT003"},
                headers={"Origin": "https://elsewhere.invalid"},
            ).status_code
            == 403
        )


def test_generated_state_reader_contains_no_click_or_inventory_open():
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / "scripts/build_bridge.py"),
            "--prepare-only",
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    generated = (ROOT / ".tools/bridge-src/McpMod.StateBuilder.cs").read_text()
    # Comments document the upstream behavior; executable calls must be gone.
    import re

    code = re.sub(r"//[^\n]*|/\*.*?\*/", "", generated, flags=re.S)
    assert not re.search(r"\.(ForceClick|OpenInventory)\s*\(", code)
    assert "inventory.AllEntries.ToList().IndexOf(entry)" in code
