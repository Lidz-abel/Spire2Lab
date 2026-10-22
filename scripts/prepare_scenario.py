"""Prepare one declared original-game opening; no gameplay or seed searching."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.acceptance import verify_windows_bundle, sha
from sts2lab.bridge import BridgeClient
from sts2lab.scenarios import ScenarioClient, ScenarioFailed, compare_opening


def load_unresolved(path):
    """Recover a journal after process termination, or a completed error report."""
    if path.suffix == ".jsonl":
        events = []
        lines = path.read_text().splitlines()
        for index, line in enumerate(lines):
            try:
                events.append(json.loads(line))
            except ValueError:
                if index != len(lines) - 1:
                    raise ValueError("Corrupt scenario journal")
                # A process can stop partway through its final journal write.
        requests = [
            e["data"]
            for e in events
            if e.get("event") in ("request_prepared", "read_only_resume")
        ]
        if len(requests) != 1 or not requests[0].get("before"):
            raise ValueError(
                "Journal needs exactly one durable request and pre-request state"
            )
        return requests[0]
    previous = json.loads(path.read_text())
    if (
        previous.get("scope") != "original_scenario_preparation"
        or previous.get("status") != "outcome_unknown"
    ):
        raise ValueError("Resume requires a prior unresolved preparation report")
    if sha(path.with_suffix(".jsonl")) != previous.get("journal_sha256"):
        raise ValueError("Scenario journal changed after recording")
    return previous


async def run(args, output):
    build = verify_windows_bundle(ROOT, sha)
    report = {
        "scope": "original_scenario_preparation",
        "evidence_kind": "live_game_staging",
        "passed": False,
        "full_battle_verified": False,
        "build": build,
    }
    journal_path = output.with_suffix(".jsonl")
    with journal_path.open("x", encoding="utf-8") as journal:

        def record(event, data):
            journal.write(
                json.dumps(
                    {
                        "time": datetime.now(timezone.utc).isoformat(),
                        "event": event,
                        "data": data,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            journal.flush()
            os.fsync(journal.fileno())

        bridge = BridgeClient(
            build["game_assembly_sha256"], mod_sha256=build["mod_sha256"]
        )
        client = ScenarioClient(bridge, record=record)
        try:
            record("verification", build)
            if args.resume:
                previous = load_unresolved(args.resume)
                client.request = previous["request"]
                client.last_request = dict(client.request)
                client.before = previous["before"]
                if (
                    client.request["expected_mod_sha256"] != build["mod_sha256"]
                    or client.request["expected_game_sha256"]
                    != build["game_assembly_sha256"]
                ):
                    raise ValueError("Unresolved request belongs to another build")
                bridge.instance_id = client.before["lab_instance_id"]
                record(
                    "read_only_resume",
                    {
                        "previous_report": str(args.resume),
                        "previous_sha256": sha(args.resume),
                        "request": client.request,
                        "before": client.before,
                    },
                )
                raw = await client.reconcile(timeout=args.timeout)
                encounter, seed = (
                    client.last_request["encounter"],
                    client.last_request["seed"],
                )
            else:
                encounter, seed = args.encounter, args.seed
                raw = await client.prepare(encounter, seed, timeout=args.timeout)
            report["opening"] = raw
            report["comparison"] = compare_opening(raw, encounter, seed)
            report["passed"] = report["comparison"]["passed"]
            report["status"] = report["comparison"]["status"]
        except (Exception, asyncio.CancelledError) as exc:
            report["status"] = (
                "failed"
                if isinstance(exc, ScenarioFailed)
                else "outcome_unknown" if client.request else "rejected"
            )
            report["error"] = {"type": type(exc).__name__, "message": str(exc)}
            report["interrupted"] = isinstance(exc, asyncio.CancelledError)
            record("error", report["error"])
        finally:
            report.update(
                request=client.last_request,
                before=client.before,
                last_state=client.last_state,
            )
            await bridge.close()
    report["journal_sha256"] = sha(journal_path)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(
        json.dumps(
            {k: report[k] for k in ("passed", "status", "full_battle_verified")}
            | {"error": report.get("error"), "evidence": str(output)},
            indent=2,
        )
    )
    return 130 if report.get("interrupted") else 0 if report["passed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--encounter",
        choices=("nibbits-weak", "slimes-weak", "sludge-spinner"),
        default="nibbits-weak",
    )
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument(
        "--resume",
        type=Path,
        help="Reconcile an unresolved .json report or interrupted .jsonl journal with GETs only",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 0 <= args.seed < 2**31 or not 1 <= args.timeout <= 300:
        parser.error("Use a nonnegative int32 seed and a timeout of 1-300 seconds")
    output = args.output or ROOT / "artifacts/windows" / (
        "scenario-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + ".json"
    )
    if (
        output.suffix != ".json"
        or output.exists()
        or output.with_suffix(".jsonl").exists()
    ):
        parser.error(
            "Choose a new .json output path; previous evidence is never overwritten"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    return asyncio.run(run(args, output))


if __name__ == "__main__":
    raise SystemExit(main())
