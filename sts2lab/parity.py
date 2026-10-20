"""Compare recorded decisions with an explicit, independently measured field profile.

A matching report covers this finite trace only, not every state or the hidden RNG.
Original raw captures must corroborate the normalized observations. Static values
borrowed from the simulator's catalog are never counted as game measurements.
"""

from pathlib import Path
import hashlib
import json
import re

from .contracts import Observation, PROTOCOL_VERSION, canonical_json
from .original import normalize_original, verify_scope, TERMINAL_MISSING
from .simulator import ROOT
from .traces import load_semantic_trace as _load
from .verification import first_difference, replay_trace

PROFILE = "starter-live-observables-v1"
CARD_FIELDS = ("type_id", "upgraded", "cost")
EXCLUDED = [
    "localized_names",
    "native_numeric_ids",
    "transport_references",
    "printed_card_damage_and_block",
    "catalog_card_types_and_targets",
    "unmeasured_card_modifiers",
    "hidden_rng_and_pile_order",
    "known_order_not_independently_exported",
    "unshown_relic_counters",
]


def action_signature(obs, action):
    hand = {card.ref: index for index, card in enumerate(obs.hand)}
    enemies = {enemy.ref: index for index, enemy in enumerate(obs.enemies)}
    try:
        return {
            "kind": action["kind"],
            "hand_index": hand[action["card_ref"]] if action.get("card_ref") else None,
            "living_enemy_index": (
                enemies[action["target_ref"]] if action.get("target_ref") else None
            ),
        }
    except KeyError as exc:
        raise ValueError(
            "Trace action references an entity outside its decision"
        ) from exc


def projection(obs, *, unavailable=()):
    def cards(items):
        return [{key: getattr(card, key) for key in CARD_FIELDS} for card in items]

    data = {
        "phase": obs.phase,
        "turn": obs.turn,
        "outcome": obs.outcome,
        "player": obs.player.model_dump(),
        "hand": cards(obs.hand),
        "enemies": [
            {
                key: value
                for key, value in e.model_dump().items()
                if key not in ("ref", "name")
            }
            for e in obs.enemies
        ],
        "relics": sorted(r.type_id for r in obs.relics),
        "legal_actions": sorted(
            [action_signature(obs, a.model_dump()) for a in obs.legal_actions],
            key=canonical_json,
        ),
    }
    for pile in ("draw_pile", "discard_pile", "exhaust_pile"):
        data[pile] = sorted(cards(getattr(obs, pile)), key=canonical_json)
    for path in unavailable:
        parts = path.split(".")
        target = data
        for part in parts[:-1]:
            target = target[part]
        target.pop(parts[-1], None)
    return data


def compare_observations(reference, candidate):
    unavailable = reference.unavailable_fields
    if reference.phase != "terminal" and unavailable:
        raise ValueError("Live combat comparison cannot omit required observations")
    if not set(unavailable) <= set(TERMINAL_MISSING):
        raise ValueError("Unrecognized omission in original reference")
    if candidate.unavailable_fields:
        raise ValueError("Simulator candidate must provide a full observation")
    return first_difference(
        projection(reference, unavailable=unavailable),
        projection(candidate, unavailable=unavailable),
    )


def _corroborate(meta, observations, transitions, raw_root):
    if meta["build"].get("evidence_kind") == "synthetic_transport_fixture":
        raise ValueError("Synthetic transport fixtures are not original-game evidence")
    game_sha = meta["build"].get("game_assembly_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", game_sha) or not meta["build"].get("compiled"):
        raise ValueError("Missing actual compiled bridge/game fingerprint")
    capture_id = meta.get("raw_capture_id", "")
    if not re.fullmatch(r"[0-9a-f]{32}", capture_id):
        raise ValueError("Invalid original capture identifier")
    refs = [meta.get("opening_capture")] + [
        t["facts"].get("original_capture") for t in transitions
    ]
    instance = None
    captures = []
    for index, (reference, obs) in enumerate(zip(refs, observations)):
        if not reference or Path(reference["file"]).name != reference["file"]:
            raise ValueError("Missing or invalid raw capture reference")
        path = Path(raw_root) / capture_id / reference["file"]
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
            raise ValueError("Original raw capture hash mismatch")
        raw = json.loads(payload)
        if (
            raw.get("game_assembly_sha256") != game_sha
            or raw.get("lab_protocol") != 1
            or not raw.get("lab_settled")
        ):
            raise ValueError("Raw capture has incompatible or unsettled provenance")
        if instance is None:
            instance = raw["lab_instance_id"]
        if not instance or raw["lab_instance_id"] != instance:
            raise ValueError("Game restarted during the trace")
        if (
            index
            and raw.get("lab_last_request_id") != transitions[index - 1]["request_id"]
        ):
            raise ValueError("Raw capture does not acknowledge the recorded command")
        verify_scope(raw, meta["encounter"], opening=index == 0)
        normalized, _ = normalize_original(
            raw, obs.decision_id, previous=observations[index - 1] if index else None
        )
        # Artificial step limits belong to the lab, not to the game capture.
        if obs.outcome == "truncated" and normalized.outcome == "ongoing":
            normalized = normalized.model_copy(
                update={
                    "phase": "terminal",
                    "outcome": "truncated",
                    "legal_actions": [],
                }
            )
        if normalized != obs:
            raise ValueError(
                f"Raw capture and normalized trace disagree at step {index}"
            )
        captures.append(raw)
    return captures


def compare_traces(reference_path, candidate_path, *, raw_root=None):
    report = {
        "profile": PROFILE,
        "scope": "recorded_original_vs_simulator_observations",
        "passed": False,
        "compared_steps": 0,
        "excluded_fields": EXCLUDED,
        "global_game_parity_proven": False,
        "hidden_rng_alignment_proven": False,
    }
    try:
        rm, ro, rt = _load(reference_path, "original_game")
        cm, co, ct = _load(candidate_path, "native_simulator")
        if rm["encounter"] != cm["encounter"] or rm["config"] != cm["config"]:
            raise ValueError("Trace configurations differ")
        _corroborate(rm, ro, rt, raw_root or ROOT / "artifacts/original-raw")
        report["original_capture_corroborated"] = True
        candidate_proof = replay_trace(candidate_path)
        if not candidate_proof["passed"]:
            return {
                **report,
                "status": "candidate_reexecution_failed",
                "candidate_proof": candidate_proof,
            }
        report["candidate_reexecuted"] = True
        report["coverage"] = {
            "combat_fields": list(projection(ro[0])),
            "card_fields": list(CARD_FIELDS),
            "terminal_unavailable_fields": ro[-1].unavailable_fields,
        }
        difference = compare_observations(ro[0], co[0])
        if difference:
            return {
                **report,
                "status": "initial_state_mismatch",
                "step": 0,
                "difference": difference,
            }
        if len(rt) != len(ct):
            return {
                **report,
                "status": "trace_length_mismatch",
                "reference_steps": len(rt),
                "candidate_steps": len(ct),
            }
        for i, (r, c) in enumerate(zip(rt, ct), 1):
            difference = first_difference(
                action_signature(ro[i - 1], r["action"]),
                action_signature(co[i - 1], c["action"]),
            )
            if difference:
                return {
                    **report,
                    "status": "action_mismatch",
                    "step": i,
                    "difference": difference,
                }
            difference = compare_observations(ro[i], co[i])
            if difference:
                return {
                    **report,
                    "status": "state_mismatch",
                    "step": i,
                    "difference": difference,
                }
            fields = ("reward", "reward_version", "terminated", "truncated")
            difference = first_difference(
                {k: r[k] for k in fields}, {k: c[k] for k in fields}
            )
            if difference:
                return {
                    **report,
                    "status": "transition_mismatch",
                    "step": i,
                    "difference": difference,
                }
            report["compared_steps"] = i
        complete = bool(rt) and ro[-1].outcome in ("won", "lost")
        return {
            **report,
            "status": "matched_complete_trace" if complete else "matched_partial_trace",
            "passed": complete,
            "outcome": ro[-1].outcome,
        }
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        return {**report, "status": "evidence_incomplete", "error": str(exc)}
