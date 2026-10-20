"""Evidence-backed acceptance for a finite, predetermined original-game suite.

The index names traces, not pass/fail claims. Every audit revalidates captures and
reexecutes the simulator. A cached status expires when an input or code file changes.
"""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

from .contracts import canonical_json, digest
from .parity import compare_traces
from .policies import Policy
from .simulator import CONFIG, ROOT, Simulator
from .traces import load_semantic_trace

SUITE_PATH = ROOT / "config/acceptance.json"
DEFAULT_INDEX = ROOT / "artifacts/acceptance/index.json"
DEFAULT_STATUS = ROOT / "artifacts/acceptance/status.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_paths(root=ROOT):
    fixed = [
        "config/phase1.json",
        "config/acceptance.json",
        "native/LabExports.cs",
        "native/Sts2Lab.csproj",
        "bridge/McpMod.Lab.cs",
        "scripts/build_bridge.py",
        "scripts/build_native.py",
        "vendor/manifest.json",
        "vendor/bridge-manifest.json",
    ]
    paths = [root / name for name in fixed]
    for directory, patterns in [
        ("sts2lab", ["*.py"]),
        ("web", ["*.js", "*.html", "*.css"]),
    ]:
        for pattern in patterns:
            paths.extend((root / directory).glob(pattern))
    return sorted(set(paths))


def expected_cases(suite, config=CONFIG):
    return {
        f"{encounter}:{seed}:{policy}": {
            "encounter": encounter,
            "seed": seed,
            "policy": policy,
        }
        for encounter in config["encounters"]
        for seed in config[f"{suite['seed_split']}_seeds"]
        for policy in suite["policies"]
    }


def coverage_of(observations, transitions):
    covered = set()
    for obs in observations:
        if obs.outcome in ("won", "lost"):
            covered.add(obs.outcome)
        if any(
            c.card_type == "Status"
            for pile in (obs.hand, obs.draw_pile, obs.discard_pile, obs.exhaust_pile)
            for c in pile
        ):
            covered.add("status_card_present")
        if any(i.type == "StatusCard" for enemy in obs.enemies for i in enemy.intents):
            covered.add("status_card_intent")
        if obs.player.powers or any(e.powers for e in obs.enemies):
            covered.add("power_present")
    for before, after, step in zip(observations, observations[1:], transitions):
        covered.add(step["action"]["kind"])
        if "turn" not in after.unavailable_fields and after.turn > before.turn:
            covered.add("turn_advance")
        # A reward screen omitting enemies is not evidence of an observed removal.
        if "enemies" not in after.unavailable_fields and len(after.enemies) < len(
            before.enemies
        ):
            covered.add("enemy_removed")
    return covered


def contained(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute():
        raise ValueError("Acceptance evidence paths must be project-relative")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Evidence path escapes the project")
    return path


def verify_windows_bundle(root, track):
    report_path = root / "artifacts/windows/report.json"
    build_path = root / "artifacts/windows/mod/build.json"
    report = json.loads(report_path.read_text(encoding="utf-8-sig"))
    build = json.loads(build_path.read_text())
    track(report_path)
    track(build_path)
    if report.get("steam_app_id") != "2868840":
        raise ValueError("Windows report is for a different Steam app")
    for name in ("sts2.dll", "GodotSharp.dll", "0Harmony.dll"):
        path = root / "artifacts/windows/assemblies" / name
        if track(path) != report["assemblies"][name]["sha256"]:
            raise ValueError(f"Windows reference hash differs: {name}")
    if not build.get("compiled") or build["reference_report_sha256"] != sha(
        report_path
    ):
        raise ValueError("Bridge does not bind the current Windows report")
    if build["game_assembly_sha256"] != report["assemblies"]["sts2.dll"]["sha256"]:
        raise ValueError("Bridge and Windows game fingerprints differ")
    if track(root / "artifacts/windows/mod/STS2_MCP.dll") != build["mod_sha256"]:
        raise ValueError("Compiled bridge binary hash differs")
    if (
        track(root / "artifacts/windows/mod/mod_manifest.json")
        != build["manifest_sha256"]
    ):
        raise ValueError("Compiled bridge manifest hash differs")
    if track(root / "bridge/McpMod.Lab.cs") != build["lab_extension_sha256"]:
        raise ValueError("Bridge extension changed after compilation")
    if track(root / "scripts/build_bridge.py") != build["build_script_sha256"]:
        raise ValueError("Bridge build/patch script changed after compilation")
    # The target label in the report is not proof. Require actual DLL version metadata.
    version = CONFIG["game_version"]
    actual = report["assemblies"]["sts2.dll"]
    pattern = r"^v?" + re.escape(version) + r"(?:[.+-]|$)"
    if not any(
        re.match(pattern, str(actual.get(k, "")))
        for k in ("file_version", "product_version")
    ):
        raise ValueError(
            "Actual game DLL version does not establish target release; inspect the Windows build before acceptance"
        )
    return build


def _validate_case(entry, expected, root, build, track):
    reference, candidate = contained(root, entry["reference"]), contained(
        root, entry["candidate"]
    )
    track(reference)
    track(candidate)
    rm, observations, transitions = load_semantic_trace(reference, "original_game")
    cm, _, _ = load_semantic_trace(candidate, "native_simulator")
    if rm["config"] != CONFIG or cm["config"] != CONFIG:
        raise ValueError("Trace configuration differs from the current benchmark")
    if rm["build"].get("evidence_kind") not in (None, "original_game_capture"):
        raise ValueError("Synthetic or unrecognized evidence is excluded")
    for key in ("game_assembly_sha256", "mod_sha256", "lab_extension_sha256"):
        if rm["build"].get(key) != build[key]:
            raise ValueError(f"Reference uses a different bridge/game build: {key}")
    if expected:
        if (
            rm["encounter"] != expected["encounter"]
            or cm["seed"] != expected["seed"]
            or rm["policy"] != expected["policy"]
        ):
            raise ValueError("Trace does not match its predetermined case")
        if any(t["facts"].get("manual_intervention") is not False for t in transitions):
            raise ValueError(
                "Baseline case contains manual intervention; register it as a boundary probe"
            )
        if type(rm.get("policy_seed")) is not int:
            raise ValueError("Baseline policy seed is missing")
        policy = Policy(expected["policy"], rm["policy_seed"])
        for obs, transition in zip(observations, transitions):
            if (
                policy.decide(obs).selected_action_id
                != transition["action"]["action_id"]
            ):
                raise ValueError(
                    "Recorded action differs from the declared baseline policy"
                )
    elif not entry["id"].startswith("probe:"):
        raise ValueError("Unexpected reference case")
    refs = [rm.get("opening_capture")] + [
        t["facts"].get("original_capture") for t in transitions
    ]
    captures = []
    for ref in refs:
        if (
            not ref
            or Path(ref["file"]).name != ref["file"]
            or not re.fullmatch(r"[0-9a-f]{32}", rm["raw_capture_id"])
        ):
            raise ValueError("Invalid raw capture reference")
        path = root / "artifacts/original-raw" / rm["raw_capture_id"] / ref["file"]
        if track(path) != ref["sha256"]:
            raise ValueError("Raw capture changed")
        captures.append(json.loads(path.read_text()))
    # Validate the private opening order directly, not an assertion in a candidate header.
    with Simulator(cm["encounter"], cm["seed"]) as sim:
        expected_order = captures[0]["player"]["draw_pile_ordered"]
        actual_order = [
            {"id": c["type_id"], "is_upgraded": c["upgraded"]}
            for c in sim._raw(debug=True)["debug_draw_order"]
        ]
        if expected_order != actual_order:
            raise ValueError("Original and simulator opening draw order differ")
    proof = compare_traces(
        reference, candidate, raw_root=root / "artifacts/original-raw"
    )
    if not proof["passed"]:
        raise ValueError(f"Reference comparison failed: {canonical_json(proof)}")
    return {
        "id": entry["id"],
        "passed": True,
        "original_run_id": rm["run_id"],
        "original_capture_id": rm["raw_capture_id"],
        "reference_sha256": sha(reference),
        "candidate_sha256": sha(candidate),
        "reference_path": str(reference.relative_to(root)),
        "candidate_path": str(candidate.relative_to(root)),
        "capture_files": [
            str(
                (
                    root / "artifacts/original-raw" / rm["raw_capture_id"] / ref["file"]
                ).relative_to(root)
            )
            for ref in refs
        ],
        "steps": proof["compared_steps"],
        "coverage": sorted(coverage_of(observations, transitions)),
        "comparison": proof,
    }


def audit_acceptance(index_path=DEFAULT_INDEX, *, root=ROOT):
    root, index_path = Path(root).resolve(), Path(index_path)
    index_path = (
        index_path.resolve()
        if index_path.is_absolute()
        else (root / index_path).resolve()
    )
    suite = json.loads((root / "config/acceptance.json").read_text())
    expected = expected_cases(suite)
    report = {
        "schema_version": 1,
        "suite_version": suite["suite_version"],
        "scope": suite["scope"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "passed": False,
        "global_game_parity_proven": False,
        "required_case_ids": sorted(expected),
        "cases": [],
        "missing_cases": sorted(expected),
        "missing_coverage": suite["required_coverage"],
        "errors": [],
        "dependencies": {},
        "source_files": [],
        "required_artifacts": [],
    }

    def track(path):
        relative = str(Path(path).relative_to(root))
        report["dependencies"][relative] = sha(path)
        return report["dependencies"][relative]

    for path in source_paths(root):
        report["source_files"].append(str(path.relative_to(root)))
        try:
            track(path)
        except OSError as exc:
            report["errors"].append(str(exc))
    for name in (
        "artifacts/windows/report.json",
        "artifacts/windows/mod/build.json",
        ".tools/native/build.json",
        ".tools/native/Sts2Emulator.so",
    ):
        report["required_artifacts"].append(name)
    try:
        if len(expected) != suite["minimum_complete_cases"]:
            raise ValueError("Suite count differs from the fixed benchmark matrix")
        build = verify_windows_bundle(root, track)
        native = json.loads((root / ".tools/native/build.json").read_text())
        track(root / ".tools/native/build.json")
        if track(root / ".tools/native/Sts2Emulator.so") != native["library_sha256"]:
            raise ValueError("Native build hash differs")
        track(index_path)
        index = json.loads(index_path.read_text())
        if index.get("suite_version") != suite["suite_version"]:
            raise ValueError("Acceptance index uses a different suite version")
        seen_ids, seen_refs, seen_runs, seen_captures, covered = (
            set(),
            set(),
            set(),
            set(),
            set(),
        )
        for entry in index["cases"]:
            case_id = entry["id"]
            if case_id in seen_ids:
                report["errors"].append(f"Duplicate case ID: {case_id}")
                continue
            seen_ids.add(case_id)
            try:
                if (
                    case_id not in expected
                    and not suite["allow_additional_boundary_probes"]
                ):
                    raise ValueError("Suite does not allow extra boundary probes")
                result = _validate_case(
                    entry, expected.get(case_id), root, build, track
                )
                if (
                    result["reference_sha256"] in seen_refs
                    or result["original_run_id"] in seen_runs
                    or result["original_capture_id"] in seen_captures
                ):
                    raise ValueError(
                        "One original capture cannot count as multiple reference cases"
                    )
                seen_refs.add(result["reference_sha256"])
                seen_runs.add(result["original_run_id"])
                seen_captures.add(result["original_capture_id"])
                covered.update(result["coverage"])
                report["cases"].append(result)
            except (ValueError, KeyError, OSError, RuntimeError, TypeError) as exc:
                report["cases"].append(
                    {"id": case_id, "passed": False, "error": str(exc)}
                )
        passed_ids = {c["id"] for c in report["cases"] if c["passed"]}
        report["missing_cases"] = sorted(set(expected) - passed_ids)
        report["missing_coverage"] = sorted(set(suite["required_coverage"]) - covered)
        report["passed"] = (
            not report["errors"]
            and not report["missing_cases"]
            and not report["missing_coverage"]
            and all(c["passed"] for c in report["cases"])
        )
    except (ValueError, KeyError, OSError, RuntimeError, TypeError) as exc:
        report["errors"].append(str(exc))
    report["status"] = "verified_scope" if report["passed"] else "incomplete"
    return report


def read_acceptance_status(path=DEFAULT_STATUS, *, root=ROOT):
    """Read-only status; expired evidence always returns unverified."""
    root, path = Path(root), Path(path)
    base = {
        "verified": False,
        "scope": "phase1 finite reference suite",
        "status": "not_audited",
    }
    try:
        report = json.loads(path.read_text())
        suite = json.loads((root / "config/acceptance.json").read_text())
        expected = set(expected_cases(suite))
        if (
            report.get("schema_version") != 1
            or report.get("suite_version") != suite["suite_version"]
            or set(report.get("required_case_ids", [])) != expected
        ):
            return {**base, "status": "invalid_report"}
        if not report.get("passed"):
            return {
                **base,
                "status": "incomplete",
                "missing_cases": len(report.get("missing_cases", [])),
                "missing_coverage": report.get("missing_coverage", []),
            }
        if (
            report.get("missing_cases")
            or report.get("missing_coverage")
            or report.get("errors")
        ):
            return {**base, "status": "invalid_report"}
        cases = report.get("cases", [])
        if not expected <= {c["id"] for c in cases if c.get("passed")} or not all(
            c.get("passed") for c in cases
        ):
            return {**base, "status": "invalid_report"}
        if len({c["id"] for c in cases}) != len(cases):
            return {**base, "status": "invalid_report"}
        coverage = set().union(*(set(c.get("coverage", [])) for c in cases))
        if not set(suite["required_coverage"]) <= coverage:
            return {**base, "status": "invalid_report"}
        current_sources = {str(p.relative_to(root)) for p in source_paths(root)}
        dependencies = report.get("dependencies", {})
        mandatory = {
            "artifacts/windows/report.json",
            "artifacts/windows/mod/build.json",
            ".tools/native/build.json",
            ".tools/native/Sts2Emulator.so",
        }
        if set(
            report.get("source_files", [])
        ) != current_sources or not current_sources | mandatory <= set(dependencies):
            return {**base, "status": "invalid_report"}
        for case in cases:
            if not case.get("capture_files") or not {
                case["reference_path"],
                case["candidate_path"],
                *case["capture_files"],
            } <= set(dependencies):
                return {**base, "status": "invalid_report"}
            if (
                dependencies[case["reference_path"]] != case["reference_sha256"]
                or dependencies[case["candidate_path"]] != case["candidate_sha256"]
            ):
                return {**base, "status": "invalid_report"}
        for relative, expected_hash in dependencies.items():
            if sha(contained(root, relative)) != expected_hash:
                return {**base, "status": "stale_evidence", "changed": relative}
        return {
            "verified": True,
            "status": "verified_scope",
            "scope": suite["scope"],
            "complete_cases": len(cases),
            "global_game_parity_proven": False,
        }
    except (OSError, ValueError, KeyError, TypeError):
        return {**base, "status": "missing_or_invalid_evidence"}
