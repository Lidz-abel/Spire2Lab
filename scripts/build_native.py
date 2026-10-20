"""Build a read-only observation extension without editing upstream game mechanics."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.source_integrity import verify_installed_source

source_proof = verify_installed_source("sts2")

source = ROOT / "vendor/sts2/src/Sts2Emulator/Interop/NativeExports.cs"
text = source.read_text()
needle = "public static class NativeExports"
assert text.count(needle) == 1, "Upstream NativeExports changed; review before building"
generated = ROOT / "native/generated"
generated.mkdir(exist_ok=True)
(generated / "NativeExports.cs").write_text(
    text.replace(needle, "public static partial class NativeExports", 1)
)
sdk = shutil.which("dotnet") or str(ROOT / ".tools/dotnet/dotnet")
stage = tempfile.TemporaryDirectory(prefix="native-build-", dir=ROOT / ".tools")
output = Path(stage.name)
subprocess.run(
    [
        sdk,
        "publish",
        str(ROOT / "native/Sts2Lab.csproj"),
        "-c",
        "Release",
        "-r",
        "linux-x64",
        "--self-contained",
        "-o",
        str(output),
        "-p:CppCompilerAndLinker=gcc",
    ],
    check=True,
    env={**os.environ, "DOTNET_CLI_TELEMETRY_OPTOUT": "1"},
)
inputs = [ROOT / "native/LabExports.cs", ROOT / "native/Sts2Lab.csproj", source]
manifest = json.loads((ROOT / "vendor/manifest.json").read_text())
manifest["source_verification"] = source_proof
manifest["extension_sources"] = {
    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs
}
manifest["library_sha256"] = hashlib.sha256(
    (output / "Sts2Emulator.so").read_bytes()
).hexdigest()
(output / "build.json").write_text(json.dumps(manifest, indent=2) + "\n")
# Replacing a file preserves existing memory mappings. Publishing directly over
# a loaded .so can corrupt a running process. Readers verify binary/manifest hashes,
# so the small interval between these two renames fails closed instead of mixing builds.
destination = ROOT / ".tools/native"
destination.mkdir(parents=True, exist_ok=True)
old_manifest = destination / "build.json"
if old_manifest.exists():
    old = json.loads(old_manifest.read_text())
    old_binary = destination / "Sts2Emulator.so"
    if hashlib.sha256(old_binary.read_bytes()).hexdigest() != old["library_sha256"]:
        raise SystemExit(
            "Existing native build is inconsistent; preserve and inspect it before replacing"
        )
    history = ROOT / ".tools/native-history" / old["library_sha256"]
    history.mkdir(parents=True, exist_ok=True)
    shutil.copy2(old_binary, history / "Sts2Emulator.so")
    shutil.copy2(old_manifest, history / "build.json")
os.replace(output / "Sts2Emulator.so", destination / "Sts2Emulator.so")
os.replace(output / "build.json", destination / "build.json")
stage.cleanup()
print(f"Published native library atomically: {manifest['library_sha256']}")
