import json
import pytest
from fastapi.testclient import TestClient
from sts2lab.server import create_app
from sts2lab.traces import read_trace
from sts2lab.verification import replay_trace


def test_request_dedup_replay_and_conflict(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        before = client.get("/api/state").json()
        request = {
            "request_id": "dedup-1",
            "decision_id": before["observation"]["decision_id"],
        }
        first = client.post("/api/step", json=request)
        assert first.status_code == 200
        assert client.post("/api/step", json=request).json() == first.json()
        assert len(client.get("/api/state").json()["history"]) == 1
        assert (
            client.post(
                "/api/step", json={**request, "action_id": "end_turn"}
            ).status_code
            == 409
        )
        assert (
            client.post(
                "/api/step", json={**request, "request_id": "stale-2"}
            ).status_code
            == 409
        )
        state = first.json()
        while state["status"] != "finished":
            state = client.post(
                "/api/step",
                json={
                    "request_id": state["observation"]["decision_id"],
                    "decision_id": state["observation"]["decision_id"],
                },
            ).json()
        path = tmp_path / f"{state['metadata']['run_id']}.jsonl"
        proof = replay_trace(path)
        assert proof["passed"] and proof["steps"] == len(state["history"])
        assert proof["scope"] == "simulator_reexecution"
        trace = read_trace(path)
        assert any(e["kind"] == "decision" for e in trace)
        assert (
            client.post(
                "/api/control",
                json={"running": True},
                headers={"Origin": "https://unrelated.example"},
            ).status_code
            == 403
        )


def test_trace_tampering_is_detected(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        state = client.get("/api/state").json()
        path = tmp_path / f"{state['metadata']['run_id']}.jsonl"
    lines = path.read_text().splitlines()
    first = json.loads(lines[0])
    first["data"]["observation"]["player"]["hp"] = 999
    lines[0] = json.dumps(first)
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(ValueError, match="integrity"):
        read_trace(path)
