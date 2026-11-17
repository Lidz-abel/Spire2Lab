"""Mocked SSH/SCP only; not a real Windows upload acceptance."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_log_upload_integrity_retention_and_no_local_copy(tmp_path):
    root = Path(__file__).resolve().parents[1]
    pwsh = os.environ.get("SPIRE2LAB_PWSH") or shutil.which("pwsh")
    local = root / ".tools/powershell/bin/pwsh"
    if not pwsh and local.exists():
        pwsh = str(local)
    if not pwsh:
        pytest.skip("PowerShell required for mocked log-upload check")
    result = subprocess.run(
        [
            pwsh,
            "-NoProfile",
            "-File",
            str(root / "tests/windows_log_upload.ps1"),
            "-Root",
            str(root),
            "-Sandbox",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
