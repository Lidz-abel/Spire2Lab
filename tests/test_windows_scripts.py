"""Mocked PowerShell operations; not evidence from an actual Steam PC."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_windows_helpers_with_mocked_transport_and_synthetic_files(tmp_path):
    root = Path(__file__).resolve().parents[1]
    pwsh = os.environ.get("SPIRE2LAB_PWSH") or shutil.which("pwsh")
    local = root / ".tools/powershell/bin/pwsh"
    if not pwsh and local.exists():
        pwsh = str(local)
    if not pwsh:
        pytest.skip(
            "PowerShell is required; set SPIRE2LAB_PWSH to run mocked script checks"
        )
    result = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(root / "tests/windows_scripts.ps1"),
            "-Root",
            str(root),
            "-Sandbox",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: relocated checkout" in result.stdout
