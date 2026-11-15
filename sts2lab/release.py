"""Bind an installed game's release metadata to its received assembly.

The compatibility hash is the signed little-endian first word of SHA-1, as
identified by read-only metadata inspection of the supplied game's AssemblyHasher.
It is not a security hash; the bundle verifier separately requires full SHA-256.
These checks establish consistency of local installation evidence, not a publisher
signature or global game correctness.
"""

from datetime import datetime
import hashlib
import json
import re


def verify_release(root, assembly, target, track):
    path = root / "artifacts/windows/release_info.json"
    if not path.exists():
        pattern = r"^v?" + re.escape(target) + r"(?:[.+-]|$)"
        if any(
            re.match(pattern, str(assembly.get(k, "")))
            for k in ("file_version", "product_version")
        ):
            return {"source": "dll_version_metadata", "version": target}
        raise ValueError(
            "Actual game DLL version does not establish target release; "
            "provide the installation's release_info.json"
        )

    # If supplied, contradictory release metadata must fail even when the DLL
    # version alone matches. Keep the original Windows report/build unchanged.
    release_sha = track(path)
    release = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(release, dict) or release.get("version") not in (
        target,
        "v" + target,
    ):
        raise ValueError("Release info version differs from the configured target")
    commit = release.get("commit")
    product = re.fullmatch(
        r"\d+\.\d+\.\d+(?:\.\d+)?\+([0-9a-f]{40})",
        str(assembly.get("product_version", "")),
    )
    if (
        not isinstance(commit, str)
        or not re.fullmatch(r"[0-9a-f]{8,40}", commit)
        or product is None
        or not product[1].startswith(commit)
    ):
        raise ValueError("Release commit does not match the DLL product version")
    raw_hash = release.get("main_assembly_hash")
    if type(raw_hash) is not int or not -(2**31) <= raw_hash < 2**31:
        raise ValueError("Release main_assembly_hash must be a signed 32-bit integer")
    dll = root / "artifacts/windows/assemblies/sts2.dll"
    binary = dll.read_bytes()
    binary_sha = hashlib.sha256(binary).hexdigest()
    if binary_sha != assembly["sha256"] or track(dll) != binary_sha:
        raise ValueError("Release assembly SHA-256 differs from the Windows report")
    compatibility_hash = int.from_bytes(
        hashlib.sha1(binary).digest()[:4], "little", signed=True
    )
    if compatibility_hash != raw_hash:
        raise ValueError("Release main_assembly_hash differs from the game DLL")
    date = release.get("date")
    if not isinstance(date, str) or datetime.fromisoformat(date).tzinfo is None:
        raise ValueError("Release date must be an ISO timestamp with a timezone")
    if not isinstance(release.get("branch"), str) or not release["branch"]:
        raise ValueError("Release branch is missing")
    return {
        "source": "release_info_with_assembly_binding",
        "version": target,
        "date": date,
        "branch": release["branch"],
        "commit": commit,
        "assembly_commit": product[1],
        "game_assembly_sha256": binary_sha,
        "release_info_sha256": release_sha,
        "main_assembly_hash": compatibility_hash,
        "compatibility_hash_algorithm": "sha1_first_int32_little_endian",
    }
