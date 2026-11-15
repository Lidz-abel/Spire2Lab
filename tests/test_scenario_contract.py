"""Exercise the exact C# contract with synthetic inputs; no game runtime."""

import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest


def test_compiled_scenario_contract_accepts_only_declared_experiments(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sdk = root / ".tools/dotnet/dotnet"
    dotnet = str(sdk) if sdk.exists() else shutil.which("dotnet")
    if not dotnet:
        pytest.skip(".NET 9 SDK required for the C# scenario contract check")
    for source in (
        root / "bridge/ScenarioContract.cs",
        root / "tests/scenario_contract.cs",
    ):
        shutil.copy2(source, tmp_path / source.name)
    project = tmp_path / "Contract.csproj"
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
    base = {
        "action": "lab_prepare",
        "lab_request_id": "request_001-accepted",
        "lab_expected_token": "c" * 64,
        "expected_game_sha256": "a" * 64,
        "expected_mod_sha256": "b" * 64,
        "seed": 1,
        "encounter": "nibbits-weak",
        "profile_id": 2,
    }
    accepted = [
        {**base, "seed": n, "encounter": encounter}
        for n in (0, 1, 2**31 - 1)
        for encounter in ("nibbits-weak", "slimes-weak", "sludge-spinner")
    ]
    rejected = [{k: v for k, v in base.items() if k != missing} for missing in base]
    rejected += [
        {**base, key: value}
        for key, value in [
            ("seed", -1),
            ("seed", 2**31),
            ("seed", True),
            ("seed", "1"),
            ("seed", 1.5),
            ("profile_id", 1),
            ("profile_id", 3),
            ("profile_id", "2"),
            ("action", "end_turn"),
            ("encounter", "unknown"),
            ("lab_request_id", ""),
            ("lab_request_id", "x" * 129),
            ("lab_request_id", "request\n"),
            ("lab_request_id", "a b"),
            ("lab_expected_token", "a" * 63),
            ("expected_game_sha256", "g" * 64),
            ("expected_mod_sha256", "A" * 64),
            ("expected_mod_sha256", "a" * 64 + "\n"),
            ("hidden_draw_override", [1, 2, 3]),
        ]
    ]
    result = subprocess.run(
        [dotnet, str(tmp_path / "bin/Release/net9.0/Contract.dll")],
        input="\n".join(json.dumps(v) for v in accepted + rejected) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert len(replies) == len(accepted + rejected)
    for case, reply in zip(accepted, replies):
        assert reply == {
            "accepted": True,
            "seed": case["seed"],
            "encounter": case["encounter"],
            "profile": 2,
        }
    assert all(reply["accepted"] is False for reply in replies[len(accepted) :])
