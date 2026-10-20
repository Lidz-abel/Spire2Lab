"""Verify pinned upstream files against authenticated source archives before builds."""

from pathlib import Path, PurePosixPath
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"sts2": "manifest.json", "sts2mcp-v107": "bridge-manifest.json"}
GENERATED_DIRS = {".git", "__pycache__", ".pytest_cache", "obj", "bin", ".venv", "out"}
BUILD_SOURCE_SUFFIXES = {".cs", ".py", ".csproj", ".props", ".targets", ".csx"}


def archive_path(target, manifest=None):
    manifest = manifest or json.loads((ROOT / "vendor" / SOURCES[target]).read_text())
    return ROOT / ".tools/vendor-archives" / f"{target}-{manifest['commit']}.tar.gz"


def verify_source_tree(manifest, destination, archive):
    destination, archive = Path(destination), Path(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest["archive_sha256"]:
        raise ValueError(f"Source archive checksum mismatch: {archive}")
    expected = set()
    with tarfile.open(archive) as tar:
        roots = set()
        for member in tar.getmembers():
            parts = PurePosixPath(member.name).parts
            if not parts or ".." in parts or member.name.startswith("/"):
                raise ValueError("Unsafe source archive path")
            roots.add(parts[0])
            if member.isdir():
                continue
            if not member.isfile() or len(parts) < 2:
                raise ValueError("Source archives must contain regular files only")
            relative = Path(*parts[1:])
            path = destination / relative
            if (
                path.is_symlink()
                or not path.is_file()
                or not path.resolve().is_relative_to(destination.resolve())
            ):
                raise ValueError(f"Missing or unsafe pinned source: {relative}")
            stream = tar.extractfile(member)
            if path.read_bytes() != stream.read():
                raise ValueError(f"Pinned source differs from archive: {relative}")
            expected.add(relative.as_posix())
        if len(roots) != 1 or not expected:
            raise ValueError("Unexpected source archive structure")
    # .NET globbing and Python imports must not pick up untracked source injections.
    for path in destination.rglob("*"):
        relative = path.relative_to(destination)
        if any(part in GENERATED_DIRS for part in relative.parts):
            continue
        if (
            path.suffix in BUILD_SOURCE_SUFFIXES
            and path.is_file()
            and relative.as_posix() not in expected
        ):
            raise ValueError(
                f"Unexpected build source outside pinned archive: {relative}"
            )
    return {
        "repository": manifest["repository"],
        "commit": manifest["commit"],
        "archive_sha256": manifest["archive_sha256"],
        "verified_files": len(expected),
        "scope": "all_archive_files_and_no_extra_build_sources",
    }


def verify_installed_source(target):
    manifest = json.loads((ROOT / "vendor" / SOURCES[target]).read_text())
    archive = archive_path(target, manifest)
    if not archive.exists():
        raise ValueError(
            f"Pinned source archive is missing: {archive}; run scripts/bootstrap.py"
        )
    return verify_source_tree(manifest, ROOT / "vendor" / target, archive)
