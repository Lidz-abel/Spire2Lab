"""Real probe HTTP loop with synthetic Godot/game objects, never live acceptance."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_runtime_probe_http_refuses_mutations_and_invalidates_failed_snapshot(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sdk = shutil.which("dotnet") or root / ".tools/dotnet/dotnet"
    if not Path(sdk).exists():
        pytest.skip("Local .NET SDK required")
    for source in (root / "bridge/probe/RuntimeProbe.cs", root / "tests/runtime_probe_harness.cs"):
        shutil.copy2(source, tmp_path / source.name)
    project = tmp_path / "ProbeTest.csproj"
    project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
                       '<OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework>'
                       '<Nullable>enable</Nullable></PropertyGroup></Project>')
    result = subprocess.run([str(sdk), "run", "--project", str(project)],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: real HTTP read-only routing" in result.stdout
