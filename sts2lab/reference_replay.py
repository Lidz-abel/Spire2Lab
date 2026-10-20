"""Replay real commands using one declared seed, without searching or fitting outcomes.

This is a validation path. It can inspect the private original opening draw order;
that privileged data never enters a policy, and never changes the simulator state.
"""

from pathlib import Path
import hashlib
import time
import uuid

from .contracts import canonical_json, digest, semantic_state, StepRequest
from .parity import (
    _load,
    _corroborate,
    action_signature,
    compare_observations,
    compare_traces,
)
from .simulator import CONFIG, ROOT, Simulator
from .traces import TraceWriter
from .verification import first_difference


def _generate_candidate(meta, observations, transitions, opening, seed, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "passed": False,
        "scope": "declared_seed_reference_replay",
        "seed": seed,
        "candidate_path": str(path),
        "seed_search_performed": False,
        "simulator_state_overridden": False,
        "hidden_rng_alignment_proven": False,
        "source_evidence_kind": meta["build"].get(
            "evidence_kind", "original_game_capture"
        ),
    }
    if meta["config"] != CONFIG:
        return {**report, "status": "configuration_mismatch"}
    with Simulator(meta["encounter"], seed) as env:
        initial = env.observe()
        difference = compare_observations(observations[0], initial)
        if difference:
            return {
                **report,
                "status": "initial_state_mismatch",
                "step": 0,
                "difference": difference,
            }
        ordered = opening["player"].get("draw_pile_ordered")
        if ordered is None:
            return {
                **report,
                "status": "initial_evidence_missing",
                "error": "Original opening draw order is missing",
            }
        expected = [{"id": c["id"], "is_upgraded": c["is_upgraded"]} for c in ordered]
        actual = [
            {"id": c["type_id"], "is_upgraded": c["upgraded"]}
            for c in env._raw(debug=True)["debug_draw_order"]
        ]
        if expected != actual:
            # Private order is not copied into a public trace or policy-facing error.
            return {**report, "status": "initial_hidden_order_mismatch", "step": 0}
        report["opening_draw_order_matched"] = True
        writer = TraceWriter(path)
        try:
            metadata = {
                "run_id": uuid.uuid4().hex,
                "backend": "native_simulator",
                "reference_status": "unverified_locally",
                "config": CONFIG,
                "encounter": meta["encounter"],
                "seed": seed,
                "policy": "recorded_reference_actions",
                "policy_seed": None,
                "build": env.manifest,
                "capabilities": env.capabilities,
                "initialization": {
                    "method": "declared_seed_no_search_no_overrides",
                    "opening_draw_order_matched": True,
                },
                "reference_run_id": meta["run_id"],
                "source_evidence_kind": report["source_evidence_kind"],
            }
            writer.append(
                "session_started",
                {"metadata": metadata, "observation": initial.model_dump()},
            )
            report["replayed_steps"] = 0
            for index, transition in enumerate(transitions, 1):
                current = env.observe()
                wanted = action_signature(observations[index - 1], transition["action"])
                matches = [
                    a
                    for a in current.legal_actions
                    if action_signature(current, a.model_dump()) == wanted
                ]
                if len(matches) != 1:
                    return {
                        **report,
                        "status": "action_mapping_mismatch",
                        "step": index,
                    }
                action = matches[0]
                req = StepRequest(
                    request_id=uuid.uuid4().hex,
                    decision_id=current.decision_id,
                    action_id=action.action_id,
                )
                writer.append(
                    "action_submitted",
                    {
                        "request": req.model_dump(),
                        "action": action.model_dump(),
                        "manual_intervention": True,
                    },
                )
                started = time.perf_counter()
                result = env.step(action.action_id, current.decision_id)
                data = result.model_dump()
                data["facts"]["manual_intervention"] = True
                data["facts"]["action_source"] = "recorded_reference"
                data["execution_ms"] = (time.perf_counter() - started) * 1000
                data["semantic_hash"] = digest(semantic_state(result.observation))
                writer.append(
                    "transition",
                    {
                        "request_id": req.request_id,
                        "action": action.model_dump(),
                        **data,
                    },
                )
                report["replayed_steps"] = index
                difference = compare_observations(
                    observations[index], result.observation
                )
                if difference:
                    writer.append(
                        "validation_difference",
                        {"step": index, "difference": difference},
                    )
                    return {
                        **report,
                        "status": "state_mismatch",
                        "step": index,
                        "difference": difference,
                    }
                fields = ("reward", "reward_version", "terminated", "truncated")
                difference = first_difference(
                    {k: transition[k] for k in fields}, {k: data[k] for k in fields}
                )
                if difference:
                    return {
                        **report,
                        "status": "transition_mismatch",
                        "step": index,
                        "difference": difference,
                    }
            return {
                **report,
                "status": "candidate_generated",
                "outcome": env.observe().outcome,
            }
        finally:
            writer.append(
                "session_closed",
                {
                    "reason": "reference_replay_stopped",
                    "outcome": env.observe().outcome,
                },
            )
            writer.close()


def replay_reference(reference, candidate, seed, *, raw_root=None):
    """Validate real evidence, generate a candidate, then run independent comparison."""
    report = {
        "passed": False,
        "scope": "declared_seed_reference_replay",
        "seed": seed,
        "seed_search_performed": False,
        "simulator_state_overridden": False,
    }
    try:
        meta, observations, transitions = _load(reference, "original_game")
        captures = _corroborate(
            meta, observations, transitions, raw_root or ROOT / "artifacts/original-raw"
        )
        generated = _generate_candidate(
            meta, observations, transitions, captures[0], seed, candidate
        )
        generated["reference_sha256"] = hashlib.sha256(
            Path(reference).read_bytes()
        ).hexdigest()
        if generated["status"] != "candidate_generated":
            return generated
        proof = compare_traces(reference, candidate, raw_root=raw_root)
        return {
            **generated,
            "passed": proof["passed"],
            "status": proof["status"],
            "comparison": proof,
        }
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        return {**report, "status": "evidence_incomplete", "error": str(exc)}
