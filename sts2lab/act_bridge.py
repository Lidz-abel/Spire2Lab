"""Guarded single-act transport. One POST per request, then read reconciliation."""

import asyncio
import time
import uuid

import httpx

from .bridge import BridgeClient, BridgeError, OutcomeUnknown, PendingCommand


class ActBridge(BridgeClient):
    async def wait_boundary(self, *, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = await self.read_state()
            if "single_act_v1" not in state.get("lab_capabilities", []):
                raise BridgeError("Install the single-act bridge build")
            if state.get("lab_act", {}).get("status") == "failed":
                raise BridgeError("Normal act startup failed; inspect private capture")
            if state.get("lab_act_settled"):
                return state
            await asyncio.sleep(0.15)
        raise BridgeError("No settled act boundary within the deadline")

    async def start_act(self, seed, *, request_id=None, timeout=45):
        async with self.lock:
            if self.pending:
                raise OutcomeUnknown("Reconcile the previous request first")
            before = await self.read_state()
            if (
                before.get("menu_screen") != "main"
                or before.get("state_type") != "menu"
                or before.get("lab_profile_id") != 2
                or not before.get("lab_settled")
            ):
                raise BridgeError("Settled main menu in experiment profile 2 required")
            if "single_act_v1" not in before.get("lab_capabilities", []):
                raise BridgeError("Install the single-act bridge build")
            payload = {
                "action": "lab_start_act",
                "seed": seed,
                "profile_id": 2,
                "expected_game_sha256": self.expected_game_sha,
                "expected_mod_sha256": self.expected_mod_sha,
            }
            return await self._post_once(
                payload, before["lab_state_token"], request_id, timeout
            )

    async def choose(self, choice_id, expected_token, *, request_id=None, timeout=35):
        async with self.lock:
            if self.pending:
                raise OutcomeUnknown("Reconcile the previous request first")
            before = await self.read_state()
            if before["lab_state_token"] != expected_token:
                raise BridgeError("stale_decision")
            if not before.get("lab_act_ready"):
                raise BridgeError("Act is not ready for a command")
            if choice_id not in [c["Id"] for c in before.get("lab_act_choices", [])]:
                raise BridgeError("illegal_act_choice")
            return await self._post_once(
                {"action": "lab_act", "choice_id": choice_id},
                expected_token,
                request_id,
                timeout,
            )

    async def _post_once(self, payload, token, request_id, timeout):
        request_id = request_id or uuid.uuid4().hex
        payload = {**payload, "lab_request_id": request_id, "lab_expected_token": token}
        self.pending = PendingCommand(request_id, token, payload)
        try:
            response = await self.client.post("/api/v1/singleplayer", json=payload)
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OutcomeUnknown(
                f"Act request {request_id} may have executed; reconcile without retry"
            ) from exc
        if result.get("status") == "unknown":
            raise OutcomeUnknown(f"Act handler outcome unknown for {request_id}")
        if result.get("status") != "ok":
            self.pending = None
            raise BridgeError(
                str(result.get("error") or result.get("message") or result)
            )
        return await self.reconcile(timeout=timeout)

    async def reconcile(self, *, timeout=35):
        if self.pending is None:
            return await self.wait_boundary(timeout=timeout)
        pending = self.pending
        starting = pending.payload["action"] == "lab_start_act"
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = await self.read_state()
                act = state.get("lab_act", {})
                acknowledged = (
                    act.get("request_id")
                    if starting
                    else state.get("lab_last_request_id")
                ) == pending.request_id
                if starting and acknowledged and act.get("status") == "failed":
                    raise OutcomeUnknown(
                        "Act startup failed; do not submit another start"
                    )
                if (
                    acknowledged
                    and state.get("lab_state_token") != pending.expected_token
                    and state.get("lab_act_settled")
                    and act.get("status") == "active"
                    and (
                        starting
                        or state.get("lab_act_ready")
                        or act.get("outcome") in ("act_complete", "lost")
                    )
                ):
                    self.pending = None
                    return state
            except (httpx.TransportError, httpx.HTTPStatusError):
                pass
            await asyncio.sleep(0.15)
        raise OutcomeUnknown(
            f"Act request {pending.request_id} has no confirmed next decision; no retry was made"
        )

    async def capture_image(self, expected):
        return await super().capture_image(expected, mode="act")
