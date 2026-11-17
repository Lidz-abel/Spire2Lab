"""E4 simulator/synthetic checks. No original game and no final-test seeds."""

import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

from sts2lab.contracts import Action, digest
from sts2lab.gym_env import CombatEnv
from sts2lab.learned_policy import (
    LearnedPolicy,
    PolicyInputError,
    encode_public_observation,
)
from sts2lab.learned_replay import audit_learned_trace
from sts2lab.rl_model import tensor_batch
from sts2lab.server import create_app
from sts2lab.traces import read_trace, TraceWriter


@pytest.fixture
def opening():
    env = CombatEnv("nibbits-weak")
    encoded, _ = env.reset(seed=3)
    try:
        yield env.sim.observe(), encoded
    finally:
        env.close()


def test_encoder_exact_and_has_no_simulator_access(opening, monkeypatch):
    from sts2lab import gym_env

    obs, expected = opening
    monkeypatch.setattr(
        gym_env, "Simulator", lambda *a, **k: pytest.fail("Policy created simulator")
    )
    encoded = encode_public_observation(obs, "nibbits-weak")
    for key in expected:
        np.testing.assert_array_equal(encoded[key], expected[key])
    assert digest(obs) == digest(obs.model_copy(deep=True))


@pytest.mark.parametrize(
    "change",
    [
        "unknown_card",
        "upgrade",
        "enchant",
        "capacity",
        "missing",
        "wrong_reference",
        "duplicate",
        "wrong_enemy",
        "unknown_power",
        "known_order",
        "terminal",
    ],
)
def test_unsupported_observations_refused(opening, change):
    obs, _ = opening
    if change == "unknown_card":
        obs = obs.model_copy(
            update={
                "hand": [obs.hand[0].model_copy(update={"type_id": "UNKNOWN"})]
                + obs.hand[1:]
            }
        )
    elif change in ("upgrade", "enchant"):
        update = (
            {"upgraded": True} if change == "upgrade" else {"enchantment": "Unknown"}
        )
        obs = obs.model_copy(
            update={"hand": [obs.hand[0].model_copy(update=update)] + obs.hand[1:]}
        )
    elif change == "capacity":
        slime = obs.hand[0].model_copy(update={"type_id": "SLIMED"})
        obs = obs.model_copy(update={"draw_pile": obs.draw_pile + [slime] * 65})
    elif change == "missing":
        obs = obs.model_copy(update={"unavailable_fields": ["draw_pile"]})
    elif change == "wrong_reference":
        obs = obs.model_copy(
            update={
                "legal_actions": [
                    Action(
                        action_id="bad",
                        kind="play_card",
                        card_ref="missing",
                        label="bad",
                    )
                ]
            }
        )
    elif change == "duplicate":
        obs = obs.model_copy(update={"legal_actions": obs.legal_actions * 2})
    elif change == "wrong_enemy":
        obs = obs.model_copy(
            update={
                "enemies": [
                    obs.enemies[0].model_copy(update={"type_id": "SludgeSpinner"})
                ]
            }
        )
    elif change == "unknown_power":
        from sts2lab.contracts import Power

        obs = obs.model_copy(
            update={
                "player": obs.player.model_copy(
                    update={"powers": [Power(type_id="Unknown", amount=1)]}
                )
            }
        )
    elif change == "known_order":
        obs = obs.model_copy(update={"known_top": obs.draw_pile[:1]})
    else:
        obs = obs.model_copy(update={"phase": "terminal", "outcome": "won"})
    with pytest.raises(PolicyInputError):
        encode_public_observation(obs, "nibbits-weak")


def test_model_matches_training_inference_and_renamed_public_references(opening):
    obs, encoded = opening
    policy = LearnedPolicy("nibbits-weak")
    with torch.inference_mode():
        logits, _ = policy.model(tensor_batch([encoded]))
    chosen = int(logits.argmax(-1).item())
    decision = policy.decide(obs)
    assert decision.selected_action_id == obs.legal_actions[chosen].action_id
    renamed = obs.model_copy(
        update={
            "decision_id": "different-public-id",
            "legal_actions": [
                a.model_copy(update={"action_id": f"renamed-{i}"})
                for i, a in enumerate(obs.legal_actions)
            ],
        }
    )
    assert policy.decide(renamed).selected_action_id == f"renamed-{chosen}"
    assert policy.last_report["observation_sha256"] == digest(renamed)
    assert not policy.last_report["fallback"]


def test_sha_failure_precedes_deserialization(monkeypatch):
    from sts2lab import learned_policy

    monkeypatch.setattr(learned_policy, "file_hash", lambda p: "wrong")
    monkeypatch.setattr(
        torch, "load", lambda *a, **k: pytest.fail("Unverified pickle loaded")
    )
    with pytest.raises(ValueError, match="SHA mismatch"):
        LearnedPolicy("nibbits-weak")


def test_nonfinite_predictions_stop_and_ties_use_first_index(opening, monkeypatch):
    obs, _ = opening
    policy = LearnedPolicy("nibbits-weak")
    monkeypatch.setattr(
        policy.model, "forward", lambda batch: (torch.zeros(1, 64), torch.zeros(1))
    )
    assert policy.decide(obs).selected_action_id == obs.legal_actions[0].action_id
    monkeypatch.setattr(
        policy.model,
        "forward",
        lambda batch: (torch.full((1, 64), float("nan")), torch.zeros(1)),
    )
    with pytest.raises(PolicyInputError, match="Non-finite"):
        policy.decide(obs)
    assert policy.last_report is None
    policy.calls = 300
    with pytest.raises(PolicyInputError, match="cap"):
        policy.decide(obs)


@pytest.mark.parametrize("encounter", ["nibbits-weak", "slimes-weak", "sludge-spinner"])
def test_model_api_full_combat_dedup_and_offline_audit(tmp_path, encounter):
    with TestClient(create_app(tmp_path / "runs")) as client:
        response = client.post(
            "/api/session", json={"policy": "ppo", "encounter": encounter, "seed": 3}
        )
        assert response.status_code == 200, response.text
        state = response.json()
        assert state["status"] == "paused" and state["learned"]["inference_call"] == 1
        for i in range(300):
            if state["status"] == "finished":
                break
            request = {
                "request_id": f"test-{i}",
                "decision_id": state["observation"]["decision_id"],
            }
            response = client.post("/api/step", json=request)
            assert response.status_code == 200, response.text
            state = response.json()
            assert client.post("/api/step", json=request).json() == state
        assert state["status"] == "finished"
        path = tmp_path / "runs" / (state["metadata"]["run_id"] + ".jsonl")
        before = path.read_bytes()
        assert client.get(f"/api/runs/{path.stem}").status_code == 200
        proof = audit_learned_trace(path)
        assert proof["passed"] and proof["new_game_actions"] == 0
        assert proof["model_calls"] == len(state["history"])
        assert path.read_bytes() == before
        # Re-hash altered semantic logs: integrity alone must not certify inference.
        events = read_trace(path)
        changed = False
        writer = TraceWriter(tmp_path / "tampered.jsonl")
        for event in events:
            data = event["data"]
            if event["kind"] == "learned_report" and not changed:
                data["logits"][0] += 1
                changed = True
            writer.append(event["kind"], data)
        writer.close()
        with pytest.raises(ValueError, match="prediction"):
            audit_learned_trace(tmp_path / "tampered.jsonl")


def test_rejected_next_decision_stops_automatic_actions(tmp_path, monkeypatch):
    app = create_app(tmp_path / "runs")
    with TestClient(app) as client:
        state = client.post("/api/session", json={"policy": "ppo", "seed": 3}).json()

        def reject(obs):
            raise PolicyInputError("synthetic unsupported next observation")

        monkeypatch.setattr(app.state.lab.policy, "decide", reject)
        request = {
            "request_id": "confirmed-then-rejected",
            "decision_id": state["observation"]["decision_id"],
        }
        assert client.post("/api/step", json=request).status_code == 409
        state = client.get("/api/state").json()
        assert state["status"] == "error" and state["decision"] is None
        assert len(state["history"]) == 1 and state["pending_request_id"] is None
        assert client.post("/api/step", json=request).status_code == 409
        assert client.post("/api/control", json={"running": True}).status_code == 409
        assert len(client.get("/api/state").json()["history"]) == 1
        events = read_trace(
            tmp_path / "runs" / (state["metadata"]["run_id"] + ".jsonl")
        )
        assert sum(e["kind"] == "action_submitted" for e in events) == 1
        assert any(e["kind"] == "policy_rejected" for e in events)
