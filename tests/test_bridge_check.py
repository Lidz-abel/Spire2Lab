"""Synthetic diagnostics only; no original-game acceptance evidence."""

import httpx
import pytest

from sts2lab.bridge_check import check_main_menu


def state(**changes):
    return {
        "state_type": "menu",
        "menu_screen": "main",
        "lab_protocol": 1,
        "game_assembly_sha256": "test-hash",
        "lab_instance_id": "test-instance",
        "lab_state_token": "test-token",
        "lab_settled": True,
        "lab_action_ready": False,
        **changes,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "second,passed",
    [
        (state(), True),
        (state(lab_settled=False), False),
        (state(lab_state_token="changed"), False),
        (state(lab_instance_id="restarted"), False),
        (state(game_assembly_sha256="wrong"), False),
        (state(lab_protocol=2), False),
        (state(state_type="monster", lab_action_ready=True), False),
    ],
)
async def test_readonly_diagnostic_refuses_changed_or_incompatible_state(
    second, passed
):
    observed = []
    samples = iter([state(lab_settled=False), second])

    def handle(request):
        observed.append((request.method, request.url.path))
        data = {"status": "ok"} if request.url.path == "/" else next(samples)
        return httpx.Response(200, json=data)

    report = await check_main_menu(
        "test-hash", samples=2, interval=0.25, transport=httpx.MockTransport(handle)
    )
    assert report["passed"] is passed
    assert report["evidence_kind"] == "synthetic_transport"
    assert report["combat_verified"] is False
    assert observed == [
        ("GET", "/"),
        ("GET", "/api/v1/singleplayer"),
        ("GET", "/api/v1/singleplayer"),
    ]


@pytest.mark.asyncio
async def test_timeout_is_recorded_without_retry_or_action():
    calls = []

    def handle(request):
        calls.append(request.method)
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    report = await check_main_menu("test-hash", transport=httpx.MockTransport(handle))
    assert report["passed"] is False and report["samples"] == []
    assert report["error"]["type"] == "ReadTimeout"
    assert calls == ["GET"]
