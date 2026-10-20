"""Reproduce project-local dependencies and pinned source archives on Linux x86_64."""

import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.source_integrity import archive_path, verify_source_tree

TOOLS = ROOT / ".tools"
TOOLS.mkdir(exist_ok=True)


def command(args):
    subprocess.run([str(x) for x in args], cwd=ROOT, check=True)


def download(url, target):
    command(
        [
            "curl",
            "-fsSL",
            "--retry",
            "2",
            "--connect-timeout",
            "15",
            "--max-time",
            "240",
            url,
            "-o",
            target,
        ]
    )


def vendor(manifest_name, target_name):
    manifest = json.loads((ROOT / "vendor" / manifest_name).read_text())
    destination = ROOT / "vendor" / target_name
    repository = manifest["repository"].removeprefix("https://github.com/")
    archive = archive_path(target_name, manifest)
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        download(
            f"https://codeload.github.com/{repository}/tar.gz/{manifest['commit']}",
            archive,
        )
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive_sha256"]:
        raise SystemExit(f"Archive checksum mismatch: {archive}")
    if destination.exists():
        proof = verify_source_tree(manifest, destination, archive)
        print(
            f"Verified existing pinned source: {destination} ({proof['verified_files']} files)"
        )
        return
    with tarfile.open(archive) as tar:
        unpack = TOOLS / f"unpack-{target_name}"
        unpack.mkdir(exist_ok=True)
        tar.extractall(unpack, filter="data")
        roots = list(unpack.iterdir())
        if len(roots) != 1:
            raise SystemExit("Unexpected source archive structure")
        shutil.move(str(roots[0]), destination)
        unpack.rmdir()
    verify_source_tree(manifest, destination, archive)


if platform.system() != "Linux" or platform.machine() != "x86_64":
    raise SystemExit("This server bootstrap currently targets Linux x86_64")
for tool in ("curl", "gcc"):
    if not shutil.which(tool):
        raise SystemExit(f"Required native build tool is missing: {tool}")
venv = ROOT / ".venv"
if not (venv / "bin/python").exists():
    command([sys.executable, "-m", "venv", venv])
if not (venv / "bin/uv").exists():
    command([venv / "bin/python", "-m", "pip", "install", "uv==0.13.1"])
command([venv / "bin/uv", "pip", "sync", "requirements.lock"])
vendor("manifest.json", "sts2")
vendor("bridge-manifest.json", "sts2mcp-v107")
sdk = TOOLS / "dotnet/dotnet"
if not sdk.exists():
    installer = TOOLS / "dotnet-install.sh"
    download("https://dot.net/v1/dotnet-install.sh", installer)
    command(
        [
            "bash",
            installer,
            "--version",
            "9.0.319",
            "--install-dir",
            TOOLS / "dotnet",
            "--no-path",
        ]
    )
command([venv / "bin/python", ROOT / "scripts/build_native.py"])
command([venv / "bin/python", "-m", "pytest", "-q"])
print("Linux environment installed. Start with: bash scripts/start.sh")
print("Original-game verification still requires the Windows connection workflow.")
