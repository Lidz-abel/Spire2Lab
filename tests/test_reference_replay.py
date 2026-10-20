"""Reference replay mechanics on explicitly synthetic simulator-generated inputs."""

import copy
import pytest
from sts2lab.contracts import StepRequest
from sts2lab.parity import _load
from sts2lab.reference_replay import _generate_candidate, replay_reference
from sts2lab.runtime import Lab
from sts2lab.simulator import Simulator
from sts2lab.traces import read_trace
from sts2lab.verification import replay_trace
from test_original import SyntheticGame


@pytest.mark.asyncio
async def test_fixed_seed_replay_and_first_difference_preserve_evidence(tmp_path):
    lab = Lab(tmp_path / "runs")
    try:
        state = await lab.new_session(seed=4, encounter="slimes-weak")
        with Simulator("slimes-weak", 4) as sim:
            opening = {
                "player": {
                    "draw_pile_ordered": [
                        {"id": c["type_id"], "is_upgraded": c["upgraded"]}
                        for c in sim._raw(debug=True)["debug_draw_order"]
                    ]
                }
            }
        while state["status"] != "finished":
            state = await lab.step(
                StepRequest(
                    request_id=state["observation"]["decision_id"],
                    decision_id=state["observation"]["decision_id"],
                )
            )
        meta, obs, transitions = _load(
            lab.trace_path(state["metadata"]["run_id"]), "native_simulator"
        )
        meta["build"] = {
            **meta["build"],
            "evidence_kind": "synthetic_transport_fixture",
        }
        candidate = tmp_path / "candidate.jsonl"
        result = _generate_candidate(meta, obs, transitions, opening, 4, candidate)
        assert result["status"] == "candidate_generated" and result["passed"] is False
        assert result["source_evidence_kind"] == "synthetic_transport_fixture"
        assert result["seed_search_performed"] is False
        assert replay_trace(candidate)["passed"]
        assert result["replayed_steps"] == len(transitions)
        bad = list(obs)
        bad[1] = obs[1].model_copy(
            update={
                "player": obs[1].player.model_copy(update={"hp": obs[1].player.hp - 1})
            }
        )
        mismatch = tmp_path / "mismatch.jsonl"
        result = _generate_candidate(meta, bad, transitions, opening, 4, mismatch)
        assert result["status"] == "state_mismatch" and result["step"] == 1
        assert result["difference"]["path"] == "/player/hp"
        assert len([e for e in read_trace(mismatch) if e["kind"] == "transition"]) == 1
        private_mismatch = copy.deepcopy(opening)
        private_mismatch["player"]["draw_pile_ordered"][0]["id"] = "DIFFERENT"
        result = _generate_candidate(
            meta, obs, transitions, private_mismatch, 4, tmp_path / "not-created.jsonl"
        )
        assert result["status"] == "initial_hidden_order_mismatch"
        assert not (tmp_path / "not-created.jsonl").exists()
        assert "DIFFERENT" not in str(result)
    finally:
        await lab.close()


@pytest.mark.asyncio
async def test_public_reference_replay_refuses_synthetic_transport(tmp_path):
    game = SyntheticGame()
    lab = Lab(tmp_path / "runs", original_factory=game.factory(tmp_path))
    try:
        state = await lab.new_session(backend="original_game")
        path = lab.trace_path(state["metadata"]["run_id"])
        report = replay_reference(path, tmp_path / "candidate.jsonl", 1)
        assert report["status"] == "evidence_incomplete" and not report["passed"]
        assert "Synthetic" in report["error"]
        assert not (tmp_path / "candidate.jsonl").exists()
    finally:
        await lab.close()
