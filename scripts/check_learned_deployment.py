"""Run three old development-seed simulator cases and audit saved PPO decisions."""

import argparse
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sts2lab.contracts import StepRequest
from sts2lab.gym_env import CombatEnv
from sts2lab.learned_policy import LearnedPolicy, encode_public_observation
from sts2lab.learned_replay import audit_learned_trace
from sts2lab.rl_io import source_version, write_json, file_hash
from sts2lab.runtime import Lab
from sts2lab.verification import replay_trace
from sts2lab.traces import load_semantic_trace
from sts2lab.parity import _corroborate
from sts2lab.simulator import ROOT


def check_historical(output):
    results = []
    # First archived reference per encounter in this checkout; previously used
    # cases, not new original executions or new held-out evaluations.
    for relative in (
        "artifacts/live-cases/20261023T082638297591/reference.jsonl",
        "artifacts/live-cases/20261023T082758051402/reference.jsonl",
        "artifacts/live-cases/20261023T083527094616/reference.jsonl",
    ):
        path = ROOT / relative
        meta, observations, transitions = load_semantic_trace(path, "original_game")
        _corroborate(meta, observations, transitions, ROOT / "artifacts/original-raw")
        policy = LearnedPolicy(meta["encounter"])
        predictions = []
        for obs in observations:
            if obs.phase == "terminal":
                continue
            policy.decide(obs)
            predictions.append(policy.last_report)
        results.append(
            {
                "trace": relative,
                "trace_sha256": file_hash(path),
                "encounter": meta["encounter"],
                "public_observations_checked": len(predictions),
                "predictions": predictions,
            }
        )
    write_json(
        output / "historical-public-inputs.json",
        {
            "scope": "offline_predictions_on_historical_original_public_inputs_not_live_model_execution",
            "original_game_actions": 0,
            "cases": results,
        },
    )
    return [{k: v for k, v in row.items() if k != "predictions"} for row in results]


async def run(output):
    source = source_version()
    if source["dirty"]:
        raise ValueError("Commit implementation before deployment evidence capture")
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "manifest.json",
        {
            "source": source,
            "scope": "simulator_deployment_engineering_check",
            "seed": 3,
            "new_training_steps": 0,
            "final_test_cases": 0,
        },
    )
    lab = Lab(output / "runs")
    results = []
    try:
        for encounter in ("nibbits-weak", "slimes-weak", "sludge-spinner"):
            state = await lab.new_session(encounter=encounter, seed=3, policy="ppo")
            steps = 0
            while state["status"] != "finished":
                if steps >= 300:
                    raise AssertionError("Unbounded simulator demonstration")
                # The expected encoder reads the simulator; the deployed adapter
                # independently receives only its public Observation value.
                template = CombatEnv(encounter)
                expected = CombatEnv._encode(
                    SimpleNamespace(
                        sim=lab.env,
                        observation_space=template.observation_space,
                        vocabulary=template.vocabulary,
                    )
                )
                actual = encode_public_observation(lab.observation, encounter)
                for key in expected:
                    np.testing.assert_array_equal(actual[key], expected[key])
                state = await lab.step(
                    StepRequest(
                        request_id=f"demo-{encounter}-{steps}",
                        decision_id=lab.observation.decision_id,
                    )
                )
                steps += 1
            path = output / "runs" / f"{state['metadata']['run_id']}.jsonl"
            await lab.archive(state["metadata"]["run_id"])
            proof = audit_learned_trace(path)
            replay = replay_trace(path)
            if not proof["passed"] or not replay["passed"]:
                raise AssertionError("Saved deployment trace failed audit")
            results.append(
                {
                    "encounter": encounter,
                    "seed": 3,
                    "trace": str(path),
                    "encoded_decisions_exact": steps,
                    "policy_audit": proof,
                    "simulator_reexecution": replay,
                }
            )
        historical = check_historical(output)
        result = {
            "passed": True,
            "scope": "simulator_engineering_only_not_original_game",
            "cases": results,
            "historical_public_input_checks": historical,
            "new_training_steps": 0,
            "final_test_cases": 0,
            "original_game_actions": 0,
        }
        write_json(output / "result.json", result)
        print(
            {
                "passed": True,
                "cases": len(results),
                "confirmed_actions": sum(
                    r["policy_audit"]["confirmed_actions"] for r in results
                ),
            }
        )
    except BaseException as exc:
        write_json(output / "failure.json", {"error": f"{type(exc).__name__}: {exc}"})
        raise
    finally:
        await lab.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.output))


if __name__ == "__main__":
    main()
