"""Synthetic execution timelines test the exact production C# gate, not the game."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_confirmation_waits_for_idle_execution_then_stable_state(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sdk = root / ".tools/dotnet/dotnet"
    dotnet = str(sdk) if sdk.exists() else shutil.which("dotnet")
    if not dotnet:
        pytest.skip(".NET 9 SDK required for the C# settlement gate check")
    for source in (
        root / "bridge/SettlementGate.cs",
        root / "tests/settlement_gate.cs",
    ):
        shutil.copy2(source, tmp_path / source.name)
    project = tmp_path / "Gate.csproj"
    project.write_text(
        '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup>'
        "<OutputType>Exe</OutputType><TargetFramework>net9.0</TargetFramework>"
        "<Nullable>enable</Nullable></PropertyGroup></Project>"
    )
    build = subprocess.run(
        [dotnet, "build", str(project), "-c", "Release", "--nologo"],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
    )
    assert build.returncode == 0, build.stdout + build.stderr
    # Each row is (token, execution_idle, elapsed milliseconds, expected settled).
    # The first timeline reproduces the failure: public fields stop changing
    # while a card is still in flight. No duration of busy time confirms it.
    timelines = [
        [
            ("card", False, 0, False),
            ("card", False, 1000, False),
            ("card", True, 2000, False),
            ("card", True, 2249, False),
            ("card", True, 2250, True),
        ],
        [
            ("opening", True, 0, False),
            ("opening", True, 249, False),
            ("opening", True, 250, True),
        ],
        [
            ("before", True, 0, False),
            ("before", True, 250, True),
            ("after", True, 1000, False),
            ("after", True, 1250, True),
        ],
        [
            ("same", True, 0, False),
            ("same", True, 250, True),
            ("same", False, 300, False),
            ("same", True, 800, False),
            ("same", True, 1049, False),
            ("same", True, 1050, True),
        ],
    ]
    cases = [
        {
            "frequency": frequency,
            "observations": [
                {"token": token, "idle": idle, "timestamp": ms * frequency // 1000}
                for token, idle, ms, _ in timeline
            ],
        }
        for frequency in (1000, 1_000_000_000)
        for timeline in timelines
    ]
    result = subprocess.run(
        [dotnet, str(tmp_path / "bin/Release/net9.0/Gate.dll")],
        input="\n".join(json.dumps(case) for case in cases) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    actual = [json.loads(line) for line in result.stdout.splitlines()]
    expected = [settled for timeline in timelines for *_, settled in timeline] * 2
    assert actual == expected
