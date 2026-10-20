import httpx
import pytest
from sts2lab.bridge import BridgeClient, BridgeError, OutcomeUnknown


def state(token="before", ready=True, settled=True):
    # Synthetic transport fixture, explicitly NOT an original-game parity fixture.
    return {
        "lab_protocol": 1,
        "lab_instance_id": "process-1",
        "game_assembly_sha256": "hash-1",
        "lab_state_token": token,
        "lab_action_ready": ready,
        "lab_settled": settled,
        "state_type": "monster",
        "lab_last_request_id": "test-request" if token != "before" else None,
    }


@pytest.mark.asyncio
async def test_action_waits_for_a_changed_settled_state():
    posted = []
    ticks = iter(
        [state(), state("before"), state("during", False, False), state("after")]
    )

    def handle(request):
        if request.method == "POST":
            posted.append(request)
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(200, json=next(ticks))

    client = BridgeClient("hash-1", transport=httpx.MockTransport(handle))
    try:
        result = await client.submit(
            {"action": "end_turn"}, "before", request_id="test-request"
        )
        assert result["lab_state_token"] == "after"
        assert len(posted) == 1 and client.pending is None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_timeout_reconciliation_never_reposts():
    posted = []
    after = False

    def handle(request):
        if request.method == "POST":
            posted.append(request)
            raise httpx.ReadTimeout("lost response", request=request)
        return httpx.Response(200, json=state("after" if after else "before"))

    client = BridgeClient("hash-1", transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(OutcomeUnknown):
            await client.submit(
                {"action": "end_turn"}, "before", request_id="test-request"
            )
        with pytest.raises(OutcomeUnknown):
            await client.submit({"action": "end_turn"}, "before")
        assert len(posted) == 1
        after = True
        assert (await client.reconcile())["lab_state_token"] == "after"
        assert len(posted) == 1
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_unrelated_state_change_is_not_our_action_completion():
    def handle(request):
        if request.method == "POST":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(200, json=state("after"))

    client = BridgeClient("hash-1", transport=httpx.MockTransport(handle))
    from sts2lab.bridge import PendingCommand

    client.pending = PendingCommand("different-request", "before", {})
    try:
        with pytest.raises(OutcomeUnknown):
            await client.reconcile(timeout=0.05)
        assert client.pending is not None
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_different_game_and_stale_state_are_refused():
    client = BridgeClient(
        "wrong-game",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=state())),
    )
    try:
        with pytest.raises(BridgeError, match="Game DLL changed"):
            await client.read_state()
    finally:
        await client.close()
    requests = []

    def handle(r):
        requests.append(r.method)
        return httpx.Response(200, json=state("new"))

    client = BridgeClient("hash-1", transport=httpx.MockTransport(handle))
    try:
        with pytest.raises(BridgeError, match="stale_decision"):
            await client.submit({"action": "end_turn"}, "old")
        assert requests == ["GET"]
    finally:
        await client.close()
