"""Synthetic transport and journal tests; never original-game parity evidence."""

import asyncio
import copy
import json
from types import SimpleNamespace

import httpx
import pytest

from test_original import raw_state
from sts2lab.bridge import BridgeClient, BridgeError, OutcomeUnknown
from sts2lab.scenarios import ScenarioClient, ScenarioFailed

GAME, MOD = "a" * 64, "b" * 64


class StagingGame:
    def __init__(self, *, failure=None, mutation=None):
        self.state = {
            "lab_protocol": 1,
            "lab_instance_id": "synthetic-staging",
            "game_assembly_sha256": GAME,
            "lab_mod_sha256": MOD,
            "lab_state_token": "c" * 64,
            "lab_profile_id": 2,
            "lab_capabilities": ["scenario_staging_v1"],
            "lab_settled": True,
            "lab_action_ready": False,
            "state_type": "menu",
            "menu_screen": "main",
        }
        self.posts = []
        self.failure, self.mutation = failure, mutation

    def handle(self, request):
        if request.method == "GET":
            return httpx.Response(200, json=self.state)
        command = json.loads(request.content)
        self.posts.append(command)
        self.state = {
            **raw_state(),
            "lab_mod_sha256": MOD,
            "game_assembly_sha256": GAME,
            "lab_instance_id": "synthetic-staging",
            "lab_profile_id": 2,
            "lab_scenario": {
                "request_id": command["lab_request_id"],
                "status": "entered",
                "seed": command["seed"],
                "encounter": command["encounter"],
                "profile_id": 2,
                "actual_floor": 2,
                "completed_combats_before": 0,
                "initializer_version": "starter-staging-v1",
                "method": "debug_staged_non_saving_run",
                "should_save": False,
                "game_sha256": GAME,
                "mod_sha256": MOD,
                "rng_initialization": "numeric_run_seed_game_named_factories_before_combat",
            },
        }
        if self.mutation:
            self.mutation(self.state)
        if self.failure == "timeout":
            raise httpx.ReadTimeout("synthetic lost response", request=request)
        if self.failure == "cancel":
            raise asyncio.CancelledError("synthetic Ctrl+C")
        if self.failure == "malformed":
            return httpx.Response(200, json=[])
        return httpx.Response(
            200, json={"status": "ok", "lab_request_id": command["lab_request_id"]}
        )

    def bridge(self):
        return BridgeClient(
            GAME, mod_sha256=MOD, transport=httpx.MockTransport(self.handle)
        )


@pytest.mark.asyncio
async def test_prepare_records_before_single_post_and_confirms_provenance():
    game = StagingGame()
    events = []

    def record(event, data):
        if event == "request_prepared":
            assert game.posts == []
        events.append((event, copy.deepcopy(data)))

    bridge = game.bridge()
    try:
        client = ScenarioClient(bridge, record=record)
        state = await client.prepare("nibbits-weak", 1)
        assert state["run"]["floor"] == 2 and client.request is None
        assert len(game.posts) == 1
        assert [e[0] for e in events] == [
            "request_prepared",
            "response_received",
            "state_observed",
        ]
        assert events[0][1]["before"]["state_type"] == "menu"
        assert client.last_request == game.posts[0]
    finally:
        await bridge.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["timeout", "malformed"])
async def test_lost_or_malformed_response_is_reconciled_without_repost(failure):
    game = StagingGame(failure=failure)
    bridge = game.bridge()
    try:
        client = ScenarioClient(bridge)
        with pytest.raises(OutcomeUnknown):
            await client.prepare("nibbits-weak", 1)
        with pytest.raises(OutcomeUnknown):
            await client.prepare("nibbits-weak", 1)
        assert (await client.reconcile())["lab_scenario"]["status"] == "entered"
        assert len(game.posts) == 1
    finally:
        await bridge.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes,error",
    [
        ({"lab_mod_sha256": "old-mod"}, "Running Mod differs"),
        ({"lab_profile_id": 1}, "profile 2"),
        ({"lab_capabilities": []}, "does not support"),
        ({"menu_screen": "character_select"}, "main menu"),
    ],
)
async def test_wrong_build_profile_or_menu_cannot_post(changes, error):
    game = StagingGame()
    game.state.update(changes)
    bridge = game.bridge()
    try:
        with pytest.raises(BridgeError, match=error):
            await ScenarioClient(bridge).prepare("nibbits-weak", 1)
        assert not game.posts
    finally:
        await bridge.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("seed", [True, -1, 2**31, 1.5, "1"])
async def test_invalid_seed_cannot_post(seed):
    game = StagingGame()
    bridge = game.bridge()
    try:
        with pytest.raises(ValueError):
            await ScenarioClient(bridge).prepare("nibbits-weak", seed)
        assert not game.posts
    finally:
        await bridge.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s["lab_scenario"].update(seed=2),
        lambda s: s["lab_scenario"].update(should_save=True),
        lambda s: s["lab_scenario"].pop("initializer_version"),
        lambda s: s["lab_scenario"].update(mod_sha256="different"),
        lambda s: s["lab_scenario"].update(completed_combats_before=1),
        lambda s: s["run"].update(floor=1),
        lambda s: s["lab_scenario"].update(
            status="failed", error="synthetic setup failure"
        ),
    ],
)
async def test_failed_or_wrong_opening_is_preserved_as_failure(mutation):
    game = StagingGame(mutation=mutation)
    bridge = game.bridge()
    try:
        client = ScenarioClient(bridge)
        with pytest.raises(ScenarioFailed):
            await client.prepare("nibbits-weak", 1)
        assert client.request and client.last_state == game.state
        assert len(game.posts) == 1
    finally:
        await bridge.close()


@pytest.mark.asyncio
async def test_unrelated_setup_and_process_restart_are_not_confirmation():
    game = StagingGame(
        mutation=lambda s: s["lab_scenario"].update(request_id="someone-else")
    )
    bridge = game.bridge()
    try:
        client = ScenarioClient(bridge)
        with pytest.raises(OutcomeUnknown):
            await client.prepare("nibbits-weak", 1, timeout=0.01)
        game.state["lab_instance_id"] = "restarted"
        with pytest.raises(BridgeError, match="restarted"):
            await client.reconcile()
        assert len(game.posts) == 1 and client.request is not None
    finally:
        await bridge.close()


@pytest.mark.asyncio
async def test_interrupted_cli_preserves_report_and_resumes_with_reads_only(
    tmp_path, monkeypatch
):
    from scripts import prepare_scenario as cli

    game = StagingGame(failure="cancel")
    build = {"game_assembly_sha256": GAME, "mod_sha256": MOD}
    monkeypatch.setattr(cli, "verify_windows_bundle", lambda *a: build)
    monkeypatch.setattr(cli, "BridgeClient", lambda *a, **kw: game.bridge())
    # This test isolates persistence/transport, not simulator or original parity.
    monkeypatch.setattr(
        cli,
        "compare_opening",
        lambda *a: {"passed": True, "status": "synthetic_test_only"},
    )
    args = SimpleNamespace(resume=None, encounter="nibbits-weak", seed=1, timeout=1)
    first = tmp_path / "interrupted.json"
    assert await cli.run(args, first) == 130
    report = json.loads(first.read_text())
    assert report["status"] == "outcome_unknown" and report["interrupted"]
    assert cli.load_unresolved(first)["request"] == game.posts[0]
    journal = first.with_suffix(".jsonl")
    with journal.open("a") as stream:
        stream.write('{"interrupted_partial_record":')
    with pytest.raises(ValueError, match="journal changed"):
        cli.load_unresolved(first)
    # A durable journal can recover even when a process never wrote its report.
    args.resume = journal
    assert await cli.run(args, tmp_path / "resumed.json") == 0
    assert len(game.posts) == 1


def test_missing_durable_request_is_not_resumable(tmp_path):
    from scripts.prepare_scenario import load_unresolved

    path = tmp_path / "before-post.jsonl"
    path.write_text(json.dumps({"event": "verification", "data": {}}) + "\n")
    with pytest.raises(ValueError, match="durable request"):
        load_unresolved(path)
