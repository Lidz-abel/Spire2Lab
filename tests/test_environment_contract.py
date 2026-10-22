"""Real native lifecycle checks and no-I/O original capability refusals."""

import httpx
import pytest

from sts2lab.bridge import BridgeClient
from sts2lab.contracts import semantic_state
from sts2lab.environment import Environment, UnsupportedCapability
from sts2lab.original import OriginalEnvironment
from sts2lab.simulator import Simulator


def test_native_reset_restores_declared_start_and_invalidates_old_decisions():
    with Simulator("nibbits-weak", 1) as env:
        assert isinstance(env, Environment)
        initial = env.observe()
        env.step(
            initial.legal_actions[0].action_id,
            initial.decision_id,
            request_id="controller-request",
        )
        reset = env.reset()
        assert semantic_state(reset) == semantic_state(initial)
        assert reset.decision_id != initial.decision_id and env.sequence == 0
        with pytest.raises(ValueError, match="stale_decision"):
            env.step(initial.legal_actions[0].action_id, initial.decision_id)
        changed = env.reset(encounter="slimes-weak", seed=3)
        with Simulator("slimes-weak", 3) as independently_created:
            assert semantic_state(changed) == semantic_state(
                independently_created.observe()
            )
        assert env.encounter == "slimes-weak" and env.seed == 3


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": -1},
        {"seed": 2**31},
        {"seed": True},
        {"seed": 1.5},
        {"encounter": "unsupported"},
    ],
)
def test_rejected_reset_preserves_live_environment(kwargs):
    with Simulator() as env:
        before = env.observe()
        with pytest.raises(ValueError):
            env.reset(**kwargs)
        assert env.observe() == before
        assert env.step(
            before.legal_actions[0].action_id, before.decision_id
        ).observation


def test_reset_preserves_independent_snapshot():
    with Simulator() as env, env.snapshot() as snapshot:
        before = snapshot.observe()
        env.reset(encounter="sludge-spinner", seed=5)
        assert snapshot.observe() == before
        assert snapshot.step(
            before.legal_actions[0].action_id, before.decision_id
        ).observation


@pytest.mark.asyncio
async def test_original_unsupported_operations_never_contact_the_game(tmp_path):
    requests = []

    def forbidden(request):
        requests.append(request)
        raise AssertionError("Unsupported capability must not make an HTTP request")

    client = BridgeClient("synthetic-hash", transport=httpx.MockTransport(forbidden))
    env = OriginalEnvironment(
        client,
        "nibbits-weak",
        {"evidence_kind": "synthetic_transport_fixture"},
        raw_dir=tmp_path,
    )
    try:
        assert isinstance(env, Environment)
        operations = [
            ("reset", "reset", lambda: env.reset(seed=1)),
            ("snapshot", "snapshot", env.snapshot),
            ("restore", "restore", lambda: env.restore(None)),
            ("sample_world", "sample_hidden", lambda: env.sample_world(1)),
        ]
        for operation, capability, invoke in operations:
            assert env.capabilities[capability] is False
            with pytest.raises(UnsupportedCapability) as error:
                invoke()
            assert error.value.operation == operation
            assert error.value.backend == "original_game"
        assert not requests and env.sequence == 0
    finally:
        await env.close()
