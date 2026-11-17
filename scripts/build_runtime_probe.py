"""Build an isolated read-only probe for the received v0.111.1 game assembly."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GAME_SHA = "3fb1fa1bf0249087b706a5d0f062a60579e2f5b08df4ee477ddd6f2607f654d5"
VERSION = "0.111.1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    refs, output = args.references.resolve(), args.output.resolve()
    private_root = (ROOT / "artifacts/windows/probes").resolve()
    if not output.is_relative_to(private_root) or output == private_root:
        raise SystemExit("Output must be a new directory below artifacts/windows/probes")
    if output.exists():
        raise SystemExit("Output exists; preserve previous attempts and choose a new directory")
    release = json.loads((refs / "release_info.json").read_text(encoding="utf-8-sig"))
    if release.get("version") != "v" + VERSION or sha(refs / "sts2.dll") != GAME_SHA:
        raise SystemExit("Probe supports only the received v0.111.1 fingerprint")
    receipt = json.loads((refs / "receipt.json").read_text())
    for name in ("sts2.dll", "GodotSharp.dll", "0Harmony.dll", "release_info.json"):
        if sha(refs / name) != receipt["files"][name]["sha256"]:
            raise SystemExit(f"Received reference changed: {name}")
    output.mkdir(parents=True, mode=0o700)
    work = output / "source"
    work.mkdir()
    source = ROOT / "bridge/probe/RuntimeProbe.cs"
    shutil.copy2(source, work / source.name)
    (work / "ProbeBuild.cs").write_text(
        'namespace Spire2Lab.Probe; internal static class ProbeBuild {'
        f' public const string ExpectedGameSha = "{GAME_SHA}";'
        f' public const string ExpectedVersion = "{VERSION}"; }}\n'
    )
    (work / "Probe.csproj").write_text('''<Project Sdk="Microsoft.NET.Sdk">
<PropertyGroup><TargetFramework>net9.0</TargetFramework><Nullable>enable</Nullable>
<AssemblyName>STS2_MCP</AssemblyName></PropertyGroup>
<ItemGroup><Reference Include="sts2"><HintPath>$(ProbeReferences)/sts2.dll</HintPath><Private>false</Private></Reference>
<Reference Include="GodotSharp"><HintPath>$(ProbeReferences)/GodotSharp.dll</HintPath><Private>false</Private></Reference></ItemGroup>
</Project>''')
    sdk = shutil.which("dotnet") or str(ROOT / ".tools/dotnet/dotnet")
    command = [sdk, "build", str(work / "Probe.csproj"), "-c", "Release",
               "-o", str(output / "compiled"), f"-p:ProbeReferences={refs}"]
    with (output / "build.log").open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"})
    (output / "build-attempt.json").write_text(json.dumps({
        "command": command, "exit_code": result.returncode,
        "source_sha256": sha(source), "builder_sha256": sha(Path(__file__)),
        "receipt_sha256": sha(refs / "receipt.json"), "live_verified": False,
    }, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(f"Probe build failed; see {output / 'build.log'}")
    shutil.copy2(output / "compiled/STS2_MCP.dll", output / "STS2_MCP.dll")
    shutil.copy2(ROOT / "LICENSE", output / "LICENSE.txt")
    (output / "mod_manifest.json").write_text(json.dumps({
        "id": "STS2_MCP", "name": "Spire2Lab Read-only Runtime Probe",
        "author": "Dongze Li", "description": "Version and connection diagnostics only; no game control.",
        "version": "0.1.0", "has_pck": False, "has_dll": True, "affects_gameplay": False,
    }, indent=2) + "\n")
    (output / "build.json").write_text(json.dumps({
        "status": "diagnostic_probe_compiled_live_pending", "read_only": True,
        "configured_target_game_version": VERSION, "game_assembly_sha256": GAME_SHA,
        "mod_sha256": sha(output / "STS2_MCP.dll"),
        "manifest_sha256": sha(output / "mod_manifest.json"),
        "source_sha256": sha(source), "capabilities": ["runtime_diagnostics_only"],
        "in_game_verified": False,
    }, indent=2) + "\n")
    print(f"Read-only probe built: {output}; not game-control or live acceptance evidence.")


if __name__ == "__main__":
    main()
