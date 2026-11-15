"""Offline audit of original act evidence. Never issues HTTP or game commands."""

import hashlib
import json
from pathlib import Path

from .act_contracts import ActObservation, normalize_act, check_continuity
from .act_policy import ActPolicy
from .contracts import digest
from .images import ImageStore, png_dimensions
from .traces import read_trace


def inventory(player):
    return {
        "deck": sorted((c["id"], bool(c.get("is_upgraded"))) for c in player["deck"]),
        "relics": sorted(c["id"] for c in player["relics"]),
        "potions": sorted(c["id"] for c in player["potions"]),
    }


def audit_act(path, *, root=None, verify_sources=True):
    path = Path(path)
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    events = read_trace(path)
    if not events or events[0]["kind"] != "session_started":
        raise ValueError("Act trace has no session header")
    metadata = events[0]["data"]["metadata"]
    if (
        metadata.get("protocol_version") != "single-act-v1"
        or metadata.get("backend") != "original_game"
    ):
        raise ValueError("Not an original act trace")
    run_id = metadata["run_id"]
    if path.stem != run_id:
        raise ValueError("Run ID differs from trace filename")
    if verify_sources:
        required = {
            "sts2lab/act_contracts.py",
            "sts2lab/act_policy.py",
            "sts2lab/act_bridge.py",
            "sts2lab/act_runtime.py",
            "config/single-act-v1.json",
        }
        if not required <= metadata.get("source_sha256", {}).keys():
            raise ValueError("Frozen source inventory is incomplete")
        for name, expected in metadata["source_sha256"].items():
            source = (root / name).resolve()
            if (
                not source.is_relative_to(root.resolve())
                or hashlib.sha256(source.read_bytes()).hexdigest() != expected
            ):
                raise ValueError("Frozen source mismatch: " + name)
    recipe = json.loads((root / "config/single-act-v1.json").read_text())
    assets = path.parent.parent
    images = ImageStore(assets / "act-images")
    policy = ActPolicy()
    observations, captures, image_decisions, decisions = [], [], set(), set()
    pending, starting, instance, observation = None, None, None, None
    last_raw, closed, expected_destination, visited = None, False, None, []
    transitions, overrides, errors = [], [], []
    shop_before = rest_before = None
    coverage = {
        "map": 0,
        "reward": 0,
        "rest_operation": 0,
        "shop_operation": 0,
        "combat": 0,
    }
    boss_seen = False
    interrupted = False

    def captured(data):
        capture_path = (assets / data["path"]).resolve()
        allowed = (assets / "act-raw" / run_id).resolve()
        if not capture_path.is_relative_to(allowed):
            raise ValueError("Capture escapes this act's private directory")
        content = capture_path.read_bytes()
        if hashlib.sha256(content).hexdigest() != data["capture_sha256"]:
            raise ValueError("Private capture hash mismatch")
        raw = json.loads(content)
        build = metadata["bridge"]
        if raw.get("game_assembly_sha256") != build.get(
            "game_assembly_sha256"
        ) or raw.get("lab_mod_sha256") != build.get("mod_sha256"):
            raise ValueError("Capture build differs from trace")
        act = raw.get("lab_act", {})
        if act.get("seed") != metadata["seed"] or act.get("request_id") != starting:
            raise ValueError("Capture belongs to a different act start")
        if not raw.get("lab_act_settled"):
            raise ValueError("Unsettled capture was recorded as a decision")
        obs = ActObservation.model_validate(data["observation"])
        normalized, _ = normalize_act(raw, obs.decision_id)
        if normalized != obs:
            raise ValueError("Public observation differs from its original capture")
        return raw, obs

    for event in events[1:]:
        kind, data = event["kind"], event["data"]
        if closed:
            raise ValueError("Event after act closure")
        if kind == "start_submitted":
            if starting is not None or observations:
                raise ValueError("More than one run startup in a continuous act")
            starting = data["request_id"]
        elif kind == "action_submitted":
            if pending or observation is None or observation.outcome != "ongoing":
                raise ValueError("Overlapping command or action after terminal")
            if data["decision_id"] != observation.decision_id:
                raise ValueError("Command uses a stale public decision")
            if data["action"] not in [
                a.model_dump() for a in observation.legal_actions
            ]:
                raise ValueError("Submitted action is not public/legal")
            pending = data
        elif kind in ("observation", "transition"):
            raw, obs = captured(data)
            if obs.decision_id != f"{run_id}:{len(observations)}":
                raise ValueError("Nonconsecutive act decisions")
            if instance is not None and raw["lab_instance_id"] != instance:
                raise ValueError("Original game restarted inside a continuous act")
            instance = raw["lab_instance_id"]
            if kind == "observation" and observation is not None:
                raise ValueError("Act opening was replaced")
            if kind == "transition":
                if (
                    pending is None
                    or data["request_id"] != pending["request_id"]
                    or data["action"] != pending["action"]
                ):
                    raise ValueError("Transition has no matching submitted command")
                if (
                    raw.get("lab_last_request_id") != pending["request_id"]
                    or raw["lab_state_token"] == last_raw["lab_state_token"]
                ):
                    raise ValueError(
                        "Transition has no acknowledged changed original state"
                    )
                action = next(
                    a
                    for a in observation.legal_actions
                    if a.action_id == data["action"]["action_id"]
                )
                check_continuity(observation, obs, action)
                reward = (
                    1
                    if obs.outcome == "act_complete"
                    else -1 if obs.outcome == "lost" else 0
                )
                if (
                    data["reward"] != reward
                    or data["terminated"] != (obs.outcome != "ongoing")
                    or data["truncated"]
                ):
                    raise ValueError("Act reward or termination was fabricated")
                if pending["override"]:
                    overrides.append(pending["request_id"])
                else:
                    expected = policy.decide(observation)
                    if (
                        expected is None
                        or action.action_id != expected["selected_action_id"]
                    ):
                        raise ValueError("Automatic action differs from public policy")
                interrupted = pending["override"]
                policy.observe_transition(observation, action, obs)
                if action.kind == "choose_map_node":
                    selected = next(
                        n
                        for n in observation.screen["next_options"]
                        if n["index"] == action.index
                    )
                    expected_destination = (selected["col"], selected["row"])
                    coverage["map"] += 1
                if action.kind == "claim_reward":
                    coverage["reward"] += 1
                if action.kind in ("play_card", "end_turn"):
                    coverage["combat"] += 1
                if action.kind == "shop_purchase":
                    shop_before = observation.player
                if action.kind == "choose_rest_option":
                    rest_before = observation.player
                if shop_before and obs.phase == "shop":
                    if obs.player["gold"] < shop_before["gold"] and inventory(
                        obs.player
                    ) != inventory(shop_before):
                        coverage["shop_operation"] += 1
                    shop_before = None
                if rest_before and obs.phase == "rest_site":
                    old_cards = inventory(rest_before)["deck"]
                    new_cards = inventory(obs.player)["deck"]
                    upgraded = sum(c[1] for c in new_cards) > sum(
                        c[1] for c in old_cards
                    )
                    if obs.player["hp"] > rest_before["hp"] or upgraded:
                        coverage["rest_operation"] += 1
                    rest_before = None
                transitions.append(data)
                pending = None
            if obs.phase == "map":
                route = [(n["col"], n["row"]) for n in obs.screen["visited"]]
                if route[: len(visited)] != visited or (
                    expected_destination
                    and expected_destination not in route[len(visited) :]
                ):
                    raise ValueError(
                        "Actual map route did not continue through selected destination"
                    )
                visited, expected_destination = route, None
            if obs.phase == "boss" and obs.battle:
                boss_seen = True
            if obs.outcome == "act_complete" and not boss_seen:
                raise ValueError("Act completion has no prior boss battle")
            observation, last_raw = obs, raw
            observations.append(obs)
            captures.append(data["capture_sha256"])
        elif kind == "decision":
            if observation is None or observation.decision_id in decisions:
                raise ValueError("Decision has no unique observation")
            expected = policy.decide(observation, interrupted=interrupted)
            interrupted = False
            actual = {k: v for k, v in data.items() if k != "elapsed_ms"}
            if expected is None or actual != {
                k: v for k, v in expected.items() if k != "elapsed_ms"
            }:
                raise ValueError("Policy/goal replay differs")
            decisions.add(observation.decision_id)
        elif kind == "decision_image" and data.get("status") == "available":
            if (
                observation is None
                or data.get("run_id") != run_id
                or data.get("decision_id") != observation.decision_id
                or data.get("observation_sha256") != digest(observation)
            ):
                raise ValueError("Image refers to a different public decision")
            for key in (
                "lab_instance_id",
                "lab_state_token",
                "game_assembly_sha256",
                "lab_mod_sha256",
            ):
                if data.get(key) != last_raw[key]:
                    raise ValueError("Image differs from original capture binding")
            dimensions = png_dimensions(images.get(run_id, data["sha256"]))
            if (
                dimensions != (data["width"], data["height"])
                or data["frame_drawn"] <= data["frame_before"]
            ):
                raise ValueError("Invalid rendered frame evidence")
            image_decisions.add(observation.decision_id)
        elif kind == "infrastructure_error":
            errors.append(data)
        elif kind == "session_closed":
            closed = True

    outcome = observation.outcome if observation else "not_started"
    missing = [key for key, value in coverage.items() if not value]
    reasons = []
    if outcome != "act_complete":
        reasons.append("first_act_not_completed")
    if not closed:
        reasons.append("trace_not_archived")
    if pending:
        reasons.append("unresolved_action")
    if missing:
        reasons.append("missing_required_families")
    if overrides:
        reasons.append("manual_overrides")
    if len(image_decisions) != len(observations):
        reasons.append("missing_decision_images")
    if decisions != {
        o.decision_id
        for o in observations
        if o.legal_actions and o.outcome == "ongoing"
    }:
        reasons.append("missing_policy_reports")
    if not verify_sources:
        reasons.append("source_verification_disabled")
    if metadata["seed"] not in recipe["seeds_in_attempt_order"]:
        reasons.append("seed_outside_frozen_recipe")
    if not metadata["bridge"].get("compiled") or metadata["bridge"].get("fixture"):
        reasons.append("not_original_build_evidence")
    if any(o.unsupported_reason for o in observations):
        reasons.append("unsupported_state")
    if len(transitions) > recipe["max_confirmed_actions"]:
        reasons.append("action_budget_exceeded")
    return {
        "schema": "single-act-audit-v1",
        "run_id": run_id,
        "seed": metadata["seed"],
        "passed": not reasons,
        "failure_reasons": reasons,
        "outcome": outcome,
        "confirmed_actions": len(transitions),
        "public_observations": len(observations),
        "policy_replays": len(decisions),
        "images": len(image_decisions),
        "coverage": coverage,
        "missing_families": missing,
        "manual_overrides": len(overrides),
        "infrastructure_events": len(errors),
        "visited_map_coordinates": visited,
        "final_hp": observation.player["hp"] if observation else None,
        "source_verified": verify_sources,
        "capture_hashes": captures,
        "game_assembly_sha256": metadata["bridge"].get("game_assembly_sha256"),
        "mod_sha256": metadata["bridge"].get("mod_sha256"),
        "scope": "recorded original normal act; no full-game simulator parity or policy-performance claim",
    }
