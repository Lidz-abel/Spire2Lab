"""Synthetic records test rejection/auditing only; they are not original evidence."""

import copy
import json

import pytest

from sts2lab.act_replay import audit_act
from sts2lab.act_runtime import ActLab
from sts2lab.contracts import StepRequest, canonical_json, digest
from sts2lab.traces import read_trace, TraceWriter
from test_act import FakeActBridge


class EvidenceFixture(FakeActBridge):
    async def start_act(self, seed, request_id):
        self.s["lab_act"].update(seed=seed, request_id=request_id)
        return copy.deepcopy(self.s)

    async def choose(self, choice_id, token, request_id):
        raw = await super().choose(choice_id, token, request_id)
        raw["lab_act"] = copy.deepcopy(self.s["lab_act"])
        raw["lab_last_request_id"] = request_id
        return raw


async def record(tmp_path):
    bridge = EvidenceFixture()
    build = {
        "fixture": True,
        "compiled": False,
        "game_assembly_sha256": "g" * 64,
        "mod_sha256": "m" * 64,
    }
    lab = ActLab(tmp_path / "act-runs", factory=lambda: (bridge, build))
    await lab.start("SPIRE2LABACT001")
    await lab.step(
        StepRequest(request_id="r1", decision_id=lab.observation.decision_id)
    )
    assert lab.status == "paused", lab.error
    await lab.archive(lab.run_id)
    return lab.trace_path(lab.run_id)


def rewrite(path, events):
    path.unlink()
    writer = TraceWriter(path)
    for event in events:
        writer.append(event["kind"], event["data"])
    writer.close()


@pytest.mark.asyncio
async def test_incomplete_synthetic_record_cannot_pass_as_an_original_act(tmp_path):
    path = await record(tmp_path)
    result = audit_act(path)
    assert result["passed"] is False
    assert result["confirmed_actions"] == 1 and result["policy_replays"] == 2
    assert result["coverage"]["map"] == 1
    assert {
        "first_act_not_completed",
        "missing_decision_images",
        "not_original_build_evidence",
    } <= set(result["failure_reasons"])


@pytest.mark.asyncio
async def test_rehashed_trace_cannot_substitute_another_public_observation(tmp_path):
    path = await record(tmp_path)
    events = read_trace(path)
    transition = next(e for e in events if e["kind"] == "transition")
    transition["data"]["observation"]["player"]["hp"] = 1
    rewrite(path, events)
    with pytest.raises(ValueError, match="differs from its original capture"):
        audit_act(path)


@pytest.mark.asyncio
async def test_changed_private_capture_is_detected_even_with_trace_hash_intact(
    tmp_path,
):
    path = await record(tmp_path)
    events = read_trace(path)
    data = next(e["data"] for e in events if e["kind"] == "observation")
    private = tmp_path / data["path"]
    raw = json.loads(private.read_text())
    raw["lab_state_token"] = "c" * 64
    private.write_text(canonical_json(raw))
    with pytest.raises(ValueError, match="capture hash mismatch"):
        audit_act(path)


@pytest.mark.asyncio
async def test_policy_and_action_ack_are_independently_audited(tmp_path):
    path = await record(tmp_path)
    events = read_trace(path)
    decision = next(e for e in events if e["kind"] == "decision")
    decision["data"]["goal"]["name"] = "changed"
    rewrite(path, events)
    with pytest.raises(ValueError, match="Policy/goal replay differs"):
        audit_act(path)
    # Restore the trace but change both raw bytes and their trace hash. A wrong
    # acknowledgement still cannot become a confirmed transition.
    decision["data"]["goal"]["name"] = "advance_first_act"
    transition = next(e["data"] for e in events if e["kind"] == "transition")
    private = tmp_path / transition["path"]
    raw = json.loads(private.read_text())
    raw["lab_last_request_id"] = "another-request"
    private.write_text(canonical_json(raw))
    transition["capture_sha256"] = digest(raw)
    rewrite(path, events)
    with pytest.raises(ValueError, match="acknowledged changed"):
        audit_act(path)
