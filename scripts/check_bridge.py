"""Verify the live main-menu bridge using GETs only; preserve each probe separately."""

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sts2lab.bridge_check import check_main_menu


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or ROOT / "artifacts/windows" / (
        "bridge-check-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        + ".json"
    )
    if output.exists():
        parser.error(
            "Output exists; choose a new filename to preserve previous evidence"
        )
    try:
        folder = ROOT / "artifacts/windows"
        report = json.loads((folder / "report.json").read_text(encoding="utf-8-sig"))
        build = json.loads((folder / "mod/build.json").read_text())
        sha = hashlib.sha256((folder / "assemblies/sts2.dll").read_bytes()).hexdigest()
        if not (
            sha
            == report["assemblies"]["sts2.dll"]["sha256"]
            == build["game_assembly_sha256"]
        ):
            parser.error("Received game DLL, Windows report and bridge build differ")
    except (OSError, ValueError, KeyError) as exc:
        parser.error(f"Cannot verify Windows references: {exc}")
    result = asyncio.run(check_main_menu(sha))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": result["passed"],
                "scope": result["scope"],
                "checks": result["checks"],
                "error": result.get("error"),
                "evidence": str(output),
                "combat_verified": False,
            },
            indent=2,
        )
    )
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
