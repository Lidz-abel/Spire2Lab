"""Offline PPO decision/confirmation audit. Never executes a game or simulator."""

from pathlib import Path

from .contracts import digest
from .images import ImageStore, png_dimensions
from .learned_policy import LearnedPolicy
from .parity import _corroborate
from .simulator import ROOT
from .traces import read_trace, load_semantic_trace


def audit_learned_trace(path, *, raw_root=None, image_root=None):
    path = Path(path)
    events = read_trace(path)
    backend = events[0]["data"]["metadata"]["backend"]
    if backend not in ("native_simulator", "original_game"):
        raise ValueError("Unknown trace backend")
    meta, observations, transitions = load_semantic_trace(path, backend)
    policy = LearnedPolicy(meta["encounter"])
    if (
        meta.get("policy") != "ppo"
        or meta.get("learned_provenance") != policy.provenance()
    ):
        raise ValueError("Learned trace provenance differs from pinned deployment")
    report, decision, obs = None, None, observations[0]
    decision_seen = False
    calls, submitted, manual = 0, 0, 0
    for event in events[1:]:
        kind, data = event["kind"], event["data"]
        if kind == "learned_report":
            if report is not None:
                raise ValueError("Duplicate learned report")
            expected = policy.decide(obs)
            if data != policy.last_report:
                raise ValueError(
                    "Recorded model prediction or observation binding differs"
                )
            report, decision = data, expected
            calls += 1
        elif kind == "decision":
            if decision_seen:
                raise ValueError("Duplicate learned decision")
            recorded = dict(data)
            recorded.pop("elapsed_ms", None)
            expected = decision.model_dump() if decision else {}
            expected.pop("elapsed_ms", None)
            if recorded != expected:
                raise ValueError("Decision does not match learned prediction")
            decision_seen = True
        elif kind == "action_submitted":
            if report is None or decision is None or not decision_seen:
                raise ValueError("Action has no bound learned proposal")
            overridden = data["action"]["action_id"] != decision.selected_action_id
            if data["manual_intervention"] != overridden:
                raise ValueError("Manual intervention flag mismatch")
            manual += int(overridden)
            submitted += 1
        elif kind == "transition":
            obs = observations[submitted]
            report, decision = None, None
            decision_seen = False
        elif kind in ("policy_rejected", "action_outcome_unknown"):
            raise ValueError(
                "Rejected or uncertain action cannot pass learned acceptance"
            )
    if submitted != len(transitions) or calls != submitted:
        raise ValueError("Incomplete learned decision/confirmation coverage")
    images = 0
    if backend == "original_game":
        captures = _corroborate(
            meta, observations, transitions, raw_root or ROOT / "artifacts/original-raw"
        )
        mapping = {o.decision_id: (o, raw) for o, raw in zip(observations, captures)}
        store = ImageStore(image_root or path.parent.parent / "images")
        seen = set()
        for event in events:
            if event["kind"] != "decision_image":
                continue
            data = event["data"]
            if data.get("status") != "available":
                continue
            if data["decision_id"] not in mapping or data["decision_id"] in seen:
                raise ValueError("Image decision missing or duplicated")
            observation, raw = mapping[data["decision_id"]]
            if data["run_id"] != meta["run_id"] or data["observation_sha256"] != digest(
                observation
            ):
                raise ValueError("Image public observation binding mismatch")
            for key in (
                "lab_instance_id",
                "lab_state_token",
                "game_assembly_sha256",
                "lab_mod_sha256",
            ):
                if data[key] != raw[key]:
                    raise ValueError(f"Image capture binding differs: {key}")
            if raw["lab_mod_sha256"] != meta["build"]["mod_sha256"]:
                raise ValueError("Installed Mod differs from trace build")
            if (
                data["source"] != "godot_root_viewport"
                or data["frame_drawn"] <= data["frame_before"]
                or png_dimensions(store.get(meta["run_id"], data["sha256"]))
                != (data["width"], data["height"])
            ):
                raise ValueError("Invalid original image evidence")
            seen.add(data["decision_id"])
        images = len(seen)
    complete = observations[-1].outcome in ("won", "lost")
    passed = (
        complete
        and not manual
        and (backend != "original_game" or images == len(observations))
    )
    return {
        "passed": passed,
        "scope": "offline_learned_decision_and_confirmation_audit",
        "backend": backend,
        "run_id": meta["run_id"],
        "model_calls": calls,
        "confirmed_actions": submitted,
        "manual_interventions": manual,
        "checkpoint_sha256": policy.provenance()["checkpoint_sha256"],
        "outcome": observations[-1].outcome,
        "final_hp": observations[-1].player.hp,
        "original_images": images,
        "new_game_actions": 0,
        "normal_original_act_acceptance": False,
    }
