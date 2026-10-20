"""Original-game transport with stale-state protection and no blind action retries.

Raw bridge states are privileged verification data. They are not policy observations.
The adapter requires our compiled Mod's game-assembly fingerprint and protocol.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
import uuid

import httpx


class BridgeError(RuntimeError):
    pass


@dataclass
class PendingCommand:
    request_id: str
    expected_token: str
    payload: dict


class OutcomeUnknown(BridgeError):
    """An action may have executed. Reconcile state; do not post it again."""


class BridgeClient:
    def __init__(
        self, game_sha256: str, *, base_url="http://127.0.0.1:18526", transport=None
    ):
        self.expected_game_sha = game_sha256
        self.client = httpx.AsyncClient(
            base_url=base_url, timeout=3, trust_env=False, transport=transport
        )
        self.pending: PendingCommand | None = None
        self.lock = asyncio.Lock()
        self.instance_id = None

    async def read_state(self):
        response = await self.client.get("/api/v1/singleplayer")
        response.raise_for_status()
        state = response.json()
        if state.get("lab_protocol") != 1:
            raise BridgeError(
                "Install the laboratory bridge build before controlling the game"
            )
        if state.get("game_assembly_sha256") != self.expected_game_sha:
            raise BridgeError(
                "Game DLL changed; re-verify the game version and rebuild the bridge"
            )
        if self.instance_id is None:
            self.instance_id = state["lab_instance_id"]
        elif state["lab_instance_id"] != self.instance_id:
            raise BridgeError(
                "Game process restarted; reconcile the session before another action"
            )
        return state

    async def wait_ready(self, *, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = await self.read_state()
                if state.get("lab_action_ready"):
                    return state
            except (httpx.TransportError, httpx.HTTPStatusError):
                pass
            await asyncio.sleep(0.1)
        raise BridgeError(
            "Game did not reach an actionable decision before the deadline"
        )

    async def submit(
        self, action: dict, expected_token: str, *, request_id=None, timeout=20
    ):
        async with self.lock:
            if self.pending is not None:
                raise OutcomeUnknown(
                    "Previous command is unresolved; call reconcile before submitting another"
                )
            if action.get("action") not in ("play_card", "end_turn"):
                raise BridgeError("Unsupported phase-one gameplay action")
            before = await self.read_state()
            if before["lab_state_token"] != expected_token:
                raise BridgeError("stale_decision")
            if not before.get("lab_action_ready"):
                raise BridgeError("Game is not ready for another decision")
            command = PendingCommand(
                request_id or uuid.uuid4().hex,
                expected_token,
                {
                    **action,
                    "lab_request_id": request_id or "",
                    "lab_expected_token": expected_token,
                },
            )
            command.payload["lab_request_id"] = command.request_id
            self.pending = command
            try:
                # POST occurs exactly once here. A timeout has an uncertain outcome.
                response = await self.client.post(
                    "/api/v1/singleplayer", json=command.payload
                )
                response.raise_for_status()
                result = response.json()
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                raise OutcomeUnknown(
                    f"Command {command.request_id} may have executed; reconcile the game state"
                ) from exc
            if result.get("status") != "ok":
                self.pending = None
                raise BridgeError(
                    str(result.get("error") or result.get("message") or result)
                )
            return await self.reconcile(timeout=timeout)

    async def reconcile(self, *, timeout=20):
        if self.pending is None:
            return await self.read_state()
        pending = self.pending
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = await self.read_state()
                changed = state.get("lab_state_token") != pending.expected_token
                acknowledged = state.get("lab_last_request_id") == pending.request_id
                terminal = state.get("state_type") in (
                    "rewards",
                    "card_reward",
                    "game_over",
                )
                if (
                    changed
                    and acknowledged
                    and state.get("lab_settled")
                    and (state.get("lab_action_ready") or terminal)
                ):
                    self.pending = None
                    return state
            except (httpx.TransportError, httpx.HTTPStatusError):
                pass
            await asyncio.sleep(0.1)
        raise OutcomeUnknown(
            f"Command {pending.request_id} has no verified settled result yet; no action was retried"
        )

    async def close(self):
        await self.client.aclose()
