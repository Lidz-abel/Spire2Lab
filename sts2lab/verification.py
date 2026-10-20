"""Re-execute semantic traces and report the first real mismatch."""

from .contracts import Observation, digest, semantic_state
from .simulator import Simulator
from .traces import load_semantic_trace


def first_difference(expected, actual, path=""):
    if type(expected) is not type(actual):
        return {"path": path, "expected": expected, "actual": actual}
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            return {
                "path": path,
                "expected_keys": sorted(expected),
                "actual_keys": sorted(actual),
            }
        for key in expected:
            difference = first_difference(expected[key], actual[key], f"{path}/{key}")
            if difference:
                return difference
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            return {
                "path": path,
                "expected_length": len(expected),
                "actual_length": len(actual),
            }
        for i, (a, b) in enumerate(zip(expected, actual)):
            difference = first_difference(a, b, f"{path}/{i}")
            if difference:
                return difference
    elif expected != actual:
        return {"path": path, "expected": expected, "actual": actual}
    return None


def replay_trace(path):
    metadata, observations, transitions = load_semantic_trace(path, "native_simulator")
    count = 0
    with Simulator(metadata["encounter"], metadata["seed"]) as sim:
        if metadata["build"]["library_sha256"] != sim.manifest["library_sha256"]:
            raise ValueError(
                "Library version mismatch; use a differential migration check"
            )
        expected = observations[0]
        difference = first_difference(
            semantic_state(expected), semantic_state(sim.observe())
        )
        if difference:
            return {"passed": False, "step": 0, "difference": difference}
        for data in transitions:
            count += 1
            result = sim.step(data["action"]["action_id"], sim.decision_id)
            expected = Observation.model_validate(data["observation"])
            difference = first_difference(
                semantic_state(expected), semantic_state(result.observation)
            )
            if difference:
                return {"passed": False, "step": count, "difference": difference}
            if (
                result.reward != data["reward"]
                or result.terminated != data["terminated"]
                or result.truncated != data["truncated"]
            ):
                return {
                    "passed": False,
                    "step": count,
                    "difference": {"path": "/transition_result"},
                }
        return {
            "passed": True,
            "steps": count,
            "outcome": sim.observe().outcome,
            "scope": "simulator_reexecution",
        }
