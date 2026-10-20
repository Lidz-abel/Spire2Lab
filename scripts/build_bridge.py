"""Build the original-game bridge on Linux using the user's private reference DLLs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument(
    "--prepare-only",
    action="store_true",
    help="Verify and prepare pinned source hooks without game DLLs",
)
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.source_integrity import verify_installed_source

source_proof = verify_installed_source("sts2mcp-v107")

source = ROOT / "vendor/sts2mcp-v107"
references = ROOT / "artifacts/windows/assemblies"
report_file = ROOT / "artifacts/windows/report.json"
build_dir = ROOT / ".tools/bridge-src"
build_dir.mkdir(parents=True, exist_ok=True)
for path in source.glob("*.cs"):
    shutil.copy2(path, build_dir / path.name)
shutil.copy2(source / "STS2_MCP.csproj", build_dir / "STS2_MCP.csproj")
shutil.copy2(ROOT / "bridge/McpMod.Lab.cs", build_dir / "McpMod.Lab.cs")
main = build_dir / "McpMod.cs"
text = main.read_text()
for old, new in [
    (
        "RunOnMainThread(() => BuildGameState())",
        "RunOnMainThread(() => BuildLabGameState())",
    ),
    (
        "RunOnMainThread(() => ExecuteAction(action, parsed))",
        "RunOnMainThread(() => ExecuteLabAction(action, parsed))",
    ),
]:
    if text.count(old) != 1:
        raise SystemExit(f"Pinned bridge hook changed: {old}")
    text = text.replace(old, new, 1)
main.write_text(text)
# Add IDs and upgrade flags to inspectable pile records; never rely on localized titles.
builder = build_dir / "McpMod.StateBuilder.cs"
text = builder.read_text()
start = text.index("private static List<Dictionary<string, object?>> BuildPileCardList")
end = text.index(
    "private static List<Dictionary<string, object?>> BuildOrderedPileList", start
)
section = text[start:end]
needle = '["name"] = SafeGetText(() => card.Title),'
assert section.count(needle) == 1
section = section.replace(
    needle,
    '["id"] = card.Id.Entry,\n                ["is_upgraded"] = card.IsUpgraded,\n                ["lab_has_enchantment"] = LabHasEnchantment(card),\n                '
    + needle,
)
text = text[:start] + section + text[end:]
start = text.index("private static Dictionary<string, object?> BuildCardInfo")
end = text.index("private static Dictionary<string, object?> BuildCardState", start)
section = text[start:end]
needle = '["is_upgraded"] = card.IsUpgraded,'
assert section.count(needle) == 1
section = section.replace(
    needle, needle + '\n            ["lab_has_enchantment"] = LabHasEnchantment(card),'
)
text = text[:start] + section + text[end:]
needle = 'state["character"] = SafeGetText(() => player.Character.Title);'
assert text.count(needle) == 1
text = text.replace(
    needle, needle + '\n        state["lab_character_id"] = player.Character.Id.Entry;'
)
needle = "catch { /* skip this power - game engine state may be inconsistent */ }"
assert text.count(needle) == 1
text = text.replace(
    needle,
    "catch { throw; } // Lab: never report an incomplete power list as authoritative",
)
builder.write_text(text)
if args.prepare_only:
    print(
        "Pinned bridge sources prepared and all hooks verified. Not compiled or game-verified."
    )
    raise SystemExit(0)
if not report_file.exists():
    raise SystemExit(
        "Windows references are missing. Run scripts/Connect-Windows.ps1 on the Steam PC first."
    )
report = json.loads(report_file.read_text(encoding="utf-8-sig"))
for name in ("sts2.dll", "GodotSharp.dll", "0Harmony.dll"):
    path = references / name
    if (
        not path.exists()
        or hashlib.sha256(path.read_bytes()).hexdigest()
        != report["assemblies"][name]["sha256"]
    ):
        raise SystemExit(f"Reference hash mismatch or missing reference: {name}")

sdk = shutil.which("dotnet") or str(ROOT / ".tools/dotnet/dotnet")
output = ROOT / "artifacts/windows/mod"
subprocess.run(
    [
        sdk,
        "build",
        str(build_dir / "STS2_MCP.csproj"),
        "-c",
        "Release",
        "-o",
        str(output),
        f"-p:STS2GameDataDir={references}",
    ],
    check=True,
    env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
)
shutil.copy2(source / "mod_manifest.json", output / "mod_manifest.json")
shutil.copy2(source / "LICENSE", output / "LICENSE.txt")
manifest = json.loads((ROOT / "vendor/bridge-manifest.json").read_text())
manifest.update(
    {
        "game_assembly_sha256": report["assemblies"]["sts2.dll"]["sha256"],
        "mod_sha256": hashlib.sha256(
            (output / "STS2_MCP.dll").read_bytes()
        ).hexdigest(),
        "compiled": True,
        "build_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_verification": source_proof,
        "in_game_verified": False,
        "manifest_sha256": hashlib.sha256(
            (output / "mod_manifest.json").read_bytes()
        ).hexdigest(),
        "lab_extension_sha256": hashlib.sha256(
            (ROOT / "bridge/McpMod.Lab.cs").read_bytes()
        ).hexdigest(),
        "reference_report_sha256": hashlib.sha256(report_file.read_bytes()).hexdigest(),
    }
)
(output / "build.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Compiled bridge at {output}. Compilation is not a claim of in-game validation.")
