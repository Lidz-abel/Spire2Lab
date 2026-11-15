"""Recompute planning choices from recorded public observations, without an actor."""

from .contracts import Action, Observation, StepResult
from .planning import PlanningConfig, PlanningPolicy
from .traces import load_semantic_trace, read_trace
from .verification import first_difference


def replay_planning(path):
    events = read_trace(path)
    metadata = events[0]["data"]["metadata"]
    load_semantic_trace(path, metadata["backend"])
    config = PlanningConfig.model_validate(metadata["planning_config"])
    if metadata.get("planning_provenance") != PlanningPolicy.provenance():
        raise ValueError(
            "Planning source/model fingerprint mismatch; use a declared migration"
        )
    if config.max_wall_ms is not None:
        raise ValueError(
            "Exact planning replay requires max_wall_ms=null; wall-clock cutoffs vary"
        )
    policy = PlanningPolicy(
        metadata["policy"], metadata["policy_seed"], metadata["encounter"], config
    )
    obs = Observation.model_validate(events[0]["data"]["observation"])
    count, proposal, report = 0, None, None
    try:
        for event in events[1:]:
            kind, data = event["kind"], event["data"]
            if kind == "planning_report":
                if proposal is not None:
                    raise ValueError("Repeated report without its decision")
                proposal = policy.decide(obs)
                report = policy.last_report
                difference = first_difference(
                    {k: v for k, v in data.items() if k != "elapsed_ms"},
                    {k: v for k, v in report.items() if k != "elapsed_ms"},
                )
                if difference:
                    return {
                        "passed": False,
                        "decision": count,
                        "difference": difference,
                    }
            elif kind == "decision":
                if proposal is None:
                    raise ValueError("Decision lacks a planning report")
                difference = first_difference(
                    {k: v for k, v in data.items() if k != "elapsed_ms"},
                    proposal.model_dump(exclude={"elapsed_ms"}),
                )
                if difference:
                    return {
                        "passed": False,
                        "decision": count,
                        "difference": difference,
                    }
                count += 1
                proposal = None
            elif kind == "transition":
                result = StepResult.model_validate(
                    {k: data[k] for k in StepResult.model_fields}
                )
                policy.observe_transition(
                    obs,
                    Action.model_validate(data["action"]),
                    result,
                    manual=data["facts"].get("manual_intervention", False),
                )
                obs = result.observation
        if proposal is not None or count == 0:
            raise ValueError("Incomplete planning trace")
        return {
            "passed": True,
            "decisions": count,
            "scope": "public_history_policy_reexecution_excluding_elapsed_time",
        }
    finally:
        policy.close()
