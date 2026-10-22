"""Read-only main-menu acceptance; never certifies combat or simulator parity."""

import asyncio
from datetime import datetime, timezone
import time

from .bridge import BridgeClient


async def check_main_menu(game_sha256, *, samples=5, interval=0.4, transport=None):
    """Sample the real BridgeClient contract and preserve failure evidence.

    A supplied transport is marked synthetic. Tests of this function cannot count
    as original-game evidence. Only GET / and GET /api/v1/singleplayer are used.
    """
    if not 2 <= samples <= 20 or not 0.25 <= interval <= 5:
        raise ValueError("Use 2-20 samples and an interval of 0.25-5 seconds")
    report = {
        "schema_version": 1,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "scope": "bridge_main_menu_readonly",
        "evidence_kind": "synthetic_transport" if transport else "live_bridge_readonly",
        "requests_get_only": True,
        "expected_game_assembly_sha256": game_sha256,
        "requested_samples": samples,
        "interval_seconds": interval,
        "samples": [],
        "checks": {},
        "passed": False,
        "combat_verified": False,
        "semantic_release_verified": False,
    }
    bridge = BridgeClient(game_sha256, transport=transport)
    try:
        response = await bridge.client.get("/")
        response.raise_for_status()
        report["greeting"] = response.json()
        for number in range(samples):
            started = time.monotonic()
            state = await bridge.read_state()
            report["samples"].append(
                {
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "latency_ms": round((time.monotonic() - started) * 1000, 2),
                    "state": state,
                }
            )
            if number + 1 < samples:
                await asyncio.sleep(interval)
        states = [sample["state"] for sample in report["samples"]]
        report["checks"] = {
            "greeting_ok": report["greeting"].get("status") == "ok",
            "protocol_and_fingerprint": True,  # Enforced by BridgeClient.read_state.
            "same_instance": len({state["lab_instance_id"] for state in states}) == 1,
            "stable_state_token": len({state["lab_state_token"] for state in states})
            == 1,
            "main_menu": all(
                state.get("state_type") == "menu" and state.get("menu_screen") == "main"
                for state in states
            ),
            "final_sample_settled": states[-1].get("lab_settled") is True,
            "menu_not_actionable": all(
                state.get("lab_action_ready") is False for state in states
            ),
        }
        report["passed"] = all(report["checks"].values())
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
    finally:
        await bridge.close()
    return report
