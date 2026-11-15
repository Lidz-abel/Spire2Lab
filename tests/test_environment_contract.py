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


def test_branch_lineage_tracks_source_decisions_and_survives_parent_reset():
    with Simulator() as env:
        root = env.branch_provenance
        assert root.operation == "root"
        assert root.parent_branch_id is None and root.parent_decision_id is None
        env.step("end_turn", env.decision_id)
        source_decision = env.decision_id
        with env.snapshot() as checkpoint, env.sample_world(17) as sampled:
            records = [checkpoint.branch_provenance, sampled.branch_provenance]
            assert {r.operation for r in records} == {"snapshot", "sample_world"}
            assert len({root.branch_id, *(r.branch_id for r in records)}) == 3
            for branch in (checkpoint, sampled):
                provenance = branch.branch_provenance
                assert provenance.parent_branch_id == root.branch_id
                assert provenance.parent_decision_id == source_decision
                assert branch.decision_id.startswith(provenance.branch_id + ":")
                assert "parent_branch_id" not in branch.observe().model_dump_json()
                assert set(provenance.model_dump()) == {
                    "branch_id",
                    "parent_branch_id",
                    "parent_decision_id",
                    "operation",
                }
            sampled.step("end_turn", sampled.decision_id)
            sampled_decision = sampled.decision_id
            with sampled.snapshot() as descendant:
                assert (
                    descendant.branch_provenance.parent_branch_id
                    == records[1].branch_id
                )
                assert (
                    descendant.branch_provenance.parent_decision_id == sampled_decision
                )
                before = descendant.observe()
                env.reset(seed=2)
                assert env.branch_provenance.operation == "root"
                assert env.branch_provenance.parent_branch_id is None
                assert env.branch_provenance.branch_id != root.branch_id
                assert checkpoint.branch_provenance == records[0]
                assert sampled.branch_provenance == records[1]
                assert descendant.observe() == before


def test_restore_creates_new_lineage_without_changing_checkpoint_or_sibling():
    from pydantic import ValidationError

    with (
        Simulator() as env,
        env.snapshot() as checkpoint,
        env.sample_world(3) as sibling,
    ):
        checkpoint_before = checkpoint.observe()
        checkpoint_lineage = checkpoint.branch_provenance
        sibling_before = sibling.observe()
        original_id = env.branch_provenance.branch_id
        env.step("end_turn", env.decision_id)
        restored = env.restore(checkpoint)
        first_lineage = env.branch_provenance
        assert first_lineage.operation == "restore"
        assert first_lineage.parent_branch_id == checkpoint_lineage.branch_id
        assert first_lineage.parent_decision_id == checkpoint_before.decision_id
        assert first_lineage.branch_id not in {
            original_id,
            checkpoint_lineage.branch_id,
        }
        assert semantic_state(restored) == semantic_state(checkpoint_before)
        env.restore(checkpoint)
        assert env.branch_provenance.branch_id != first_lineage.branch_id
        assert env.branch_provenance.parent_branch_id == checkpoint_lineage.branch_id
        assert checkpoint.observe() == checkpoint_before
        assert checkpoint.branch_provenance == checkpoint_lineage
        assert sibling.observe() == sibling_before
        with pytest.raises(ValidationError, match="frozen"):
            first_lineage.parent_branch_id = "rewrite-history"


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
        assert env.branch_provenance is None
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
