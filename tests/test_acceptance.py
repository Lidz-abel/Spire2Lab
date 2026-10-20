"""Acceptance bookkeeping tests. All synthetic evidence remains in temporary dirs."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sts2lab import acceptance as a
from sts2lab.server import create_app


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def project(tmp_path):
    for source in a.source_paths():
        destination = tmp_path / source.relative_to(a.ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    return tmp_path


def windows_stub(root):
    # Tests only byte/version binding; these bytes are not loadable game/Mod binaries.
    assemblies = {}
    for name in ("sts2.dll", "GodotSharp.dll", "0Harmony.dll"):
        path = root / "artifacts/windows/assemblies" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic " + name)
        assemblies[name] = {
            "sha256": a.sha(path),
            "file_version": "0.107.1.0",
            "product_version": "0.107.1",
        }
    report = {
        "steam_app_id": "2868840",
        "assemblies": assemblies,
        "target_game_version": "0.107.1",
    }
    report_path = root / "artifacts/windows/report.json"
    write_json(report_path, report)
    folder = root / "artifacts/windows/mod"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "STS2_MCP.dll").write_text("synthetic mod")
    (folder / "mod_manifest.json").write_text("{}")
    build = {
        "compiled": True,
        "reference_report_sha256": a.sha(report_path),
        "game_assembly_sha256": assemblies["sts2.dll"]["sha256"],
        "mod_sha256": a.sha(folder / "STS2_MCP.dll"),
        "manifest_sha256": a.sha(folder / "mod_manifest.json"),
        "lab_extension_sha256": a.sha(root / "bridge/McpMod.Lab.cs"),
        "build_script_sha256": a.sha(root / "scripts/build_bridge.py"),
    }
    write_json(folder / "build.json", build)
    native = root / ".tools/native"
    native.mkdir(parents=True, exist_ok=True)
    (native / "Sts2Emulator.so").write_text("synthetic native")
    write_json(
        native / "build.json", {"library_sha256": a.sha(native / "Sts2Emulator.so")}
    )
    return report, build


def test_missing_windows_evidence_cannot_pass(tmp_path):
    root = project(tmp_path)
    report = a.audit_acceptance(root / "index.json", root=root)
    assert report["passed"] is False and len(report["missing_cases"]) == 60
    assert "windows/report.json" in report["errors"][0]
    path = root / "status.json"
    write_json(path, report)
    assert a.read_acceptance_status(path, root=root)["verified"] is False


def test_target_label_is_not_actual_version_evidence(tmp_path):
    root = project(tmp_path)
    report, build = windows_stub(root)
    report["assemblies"]["sts2.dll"].update(
        file_version="1.0.0.0", product_version="unknown"
    )
    write_json(root / "artifacts/windows/report.json", report)
    build["reference_report_sha256"] = a.sha(root / "artifacts/windows/report.json")
    write_json(root / "artifacts/windows/mod/build.json", build)
    with pytest.raises(ValueError, match="Actual game DLL version"):
        a.verify_windows_bundle(root, a.sha)


def test_complete_matrix_is_cached_only_until_evidence_changes(tmp_path, monkeypatch):
    root = project(tmp_path)
    windows_stub(root)
    suite = json.loads((root / "config/acceptance.json").read_text())
    expected = a.expected_cases(suite)
    index = {
        "suite_version": suite["suite_version"],
        "cases": [{"id": key} for key in expected],
    }
    write_json(root / "index.json", index)

    # Isolate aggregation/cache logic; this stub is NEVER production parity evidence.
    def validate(entry, expectation, root, build, track):
        files = []
        for kind in ("reference", "candidate", "capture"):
            path = root / "synthetic-unit-test" / f"{entry['id']}-{kind}.txt"
            path.parent.mkdir(exist_ok=True)
            path.write_text(entry["id"] + kind)
            track(path)
            files.append(str(path.relative_to(root)))
        return {
            "id": entry["id"],
            "passed": True,
            "original_run_id": entry["id"],
            "original_capture_id": entry["id"],
            "reference_path": files[0],
            "candidate_path": files[1],
            "capture_files": [files[2]],
            "reference_sha256": a.sha(root / files[0]),
            "candidate_sha256": a.sha(root / files[1]),
            "coverage": suite["required_coverage"],
        }

    monkeypatch.setattr(a, "_validate_case", validate)
    report = a.audit_acceptance(Path("index.json"), root=root)
    assert report["passed"] is True and len(report["cases"]) == 60
    status = root / "status.json"
    write_json(status, report)
    assert a.read_acceptance_status(status, root=root)["verified"] is True
    changed = root / report["cases"][0]["capture_files"][0]
    changed.write_text("changed after audit")
    assert a.read_acceptance_status(status, root=root)["status"] == "stale_evidence"
    index["cases"].append(index["cases"][0])
    write_json(root / "index.json", index)
    report = a.audit_acceptance(root / "index.json", root=root)
    assert not report["passed"] and any(
        "Duplicate case ID" in e for e in report["errors"]
    )


def test_passed_boolean_without_evidence_is_rejected(tmp_path):
    root = project(tmp_path)
    path = root / "status.json"
    write_json(path, {"passed": True})
    assert not a.read_acceptance_status(path, root=root)["verified"]


def test_api_uses_scoped_acceptance_status(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        status = client.get("/api/acceptance").json()
        health = client.get("/api/health").json()
        assert health["original_game_verified"] is status["verified"]
        assert health["global_game_parity_proven"] is False
        assert health["verification_scope"] == status["scope"]
