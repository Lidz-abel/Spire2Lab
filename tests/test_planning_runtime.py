"""Planning lifecycle, trace evidence and responsiveness without a Windows game."""

import asyncio
import threading

import pytest
from fastapi.testclient import TestClient

from sts2lab.contracts import StepRequest
from sts2lab.planning import PlanningPolicy
from sts2lab.planning_replay import replay_planning
from sts2lab.runtime import Lab
from sts2lab.server import create_app
from sts2lab.traces import read_trace
from sts2lab.verification import replay_trace

CONFIG = {
    "particles": 2,
    "init_attempts": 512,
    "search_calls": 96,
    "rollout_depth": 6,
    "max_wall_ms": None,
}


def test_planning_reports_and_goal_durations_survive_complete_trace(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        response = client.post(
            "/api/session",
            json={
                "policy": "hierarchical",
                "policy_seed": 773,
                "planning_config": CONFIG,
            },
        )
        assert response.status_code == 200, response.text
        state = response.json()
        assert (
            state["metadata"]["planning_information"] == "confirmed_public_history_only"
        )
        assert state["planning"]["model_calls"] > 0
        for i in range(100):
            response = client.post(
                "/api/step",
                json={
                    "request_id": f"planned-{i}",
                    "decision_id": state["observation"]["decision_id"],
                },
            )
            assert response.status_code == 200, response.text
            state = response.json()
            if state["status"] == "finished":
                break
        assert state["status"] == "finished"
        path = tmp_path / f"{state['metadata']['run_id']}.jsonl"
        events = read_trace(path)
        reports = [e["data"] for e in events if e["kind"] == "planning_report"]
        goals = [e["data"] for e in events if e["kind"] == "goal_completed"]
        assert len(reports) == len(state["history"])
        assert sum(g["duration"] for g in goals) == len(state["history"])
        assert goals[-1]["termination_reason"] == "terminal"
        assert replay_trace(path)["passed"]
        assert replay_planning(path)["passed"]
        assert (
            client.post(
                "/api/archive", json={"run_id": state["metadata"]["run_id"]}
            ).json()["status"]
            == "closed"
        )
        assert client.app.state.lab.policy.closed


@pytest.mark.asyncio
async def test_planning_keeps_loop_responsive_and_accepts_pause(tmp_path, monkeypatch):
    lab = Lab(tmp_path)
    await lab.new_session(
        policy="rollout", policy_seed=773, planning_config={**CONFIG, "search_calls": 0}
    )
    entered, release = threading.Event(), threading.Event()
    original = PlanningPolicy.decide

    def delayed(policy, obs):
        entered.set()
        if not release.wait(3):
            raise RuntimeError("Test did not release planning worker")
        return original(policy, obs)

    monkeypatch.setattr(PlanningPolicy, "decide", delayed)
    await lab.control(True)
    before = lab.observation
    action = asyncio.create_task(
        lab.step(
            StepRequest(request_id="slow-search", decision_id=before.decision_id),
            automatic=True,
        )
    )
    try:
        for _ in range(100):
            if entered.is_set():
                break
            await asyncio.sleep(0.01)
        assert entered.is_set() and lab.view()["status"] == "planning"
        assert len(lab.view()["history"]) == 1  # execution confirmed before planning
        paused = await asyncio.wait_for(lab.control(False), timeout=0.25)
        assert paused["resume_after_step"] is False
        with pytest.raises(ValueError, match="progress"):
            await lab.new_session()
        release.set()
        result = await action
        assert result["status"] == "paused" and len(result["history"]) == 1
    finally:
        release.set()
        if not action.done():
            await action
        await lab.close()


def test_baselines_refuse_unused_search_configuration(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        old = client.get("/api/state").json()
        r = client.post(
            "/api/session", json={"policy": "heuristic", "planning_config": CONFIG}
        )
        assert r.status_code == 409
        assert (
            client.get("/api/state").json()["metadata"]["run_id"]
            == old["metadata"]["run_id"]
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["archive", "reset", "close"])
async def test_active_goal_is_recorded_before_session_closure(tmp_path, mode):
    lab = Lab(tmp_path)
    await lab.new_session(
        policy="hierarchical",
        policy_seed=773,
        planning_config={**CONFIG, "search_calls": 0},
    )
    path = lab.trace_path(lab.run_id)
    if mode == "archive":
        await lab.archive(lab.run_id)
    elif mode == "reset":
        await lab.new_session()
    else:
        await lab.close()
    events = read_trace(path)
    assert events[-2]["kind"] == "goal_completed"
    goal = events[-2]["data"]
    assert goal["duration"] == 0 and goal["cumulative_reward"] == 0
    assert (
        goal["termination_reason"]
        == {
            "archive": "session_archived",
            "reset": "session_reset",
            "close": "server_shutdown",
        }[mode]
    )
    assert replay_trace(path)["passed"]
    await lab.close()


@pytest.mark.asyncio
async def test_planning_replay_detects_changed_scores_and_refuses_wall_clock_claim(
    tmp_path,
):
    from sts2lab.traces import TraceWriter

    lab = Lab(tmp_path)
    await lab.new_session(policy="rollout", policy_seed=773, planning_config=CONFIG)
    path = lab.trace_path(lab.run_id)
    await lab.archive(lab.run_id)
    assert replay_planning(path)["passed"]
    events = read_trace(path)
    modified = tmp_path / "changed-score.jsonl"
    writer = TraceWriter(modified)
    for event in events:
        if event["kind"] == "decision":
            event["data"]["candidates"][0]["score"] += 0.5
        writer.append(event["kind"], event["data"])
    writer.close()
    assert replay_planning(modified)["passed"] is False
    await lab.new_session(
        policy="rollout",
        planning_config={**CONFIG, "search_calls": 0, "max_wall_ms": 100},
    )
    path = lab.trace_path(lab.run_id)
    await lab.archive(lab.run_id)
    with pytest.raises(ValueError, match="wall-clock"):
        replay_planning(path)
    await lab.close()
