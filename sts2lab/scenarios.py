"""Control explicit original-game initialization; never retry a staging POST.

This setup path may inspect private opening evidence. The policy path continues
to consume only normalize_original() observations, with no RNG or hidden order.
"""

import asyncio
import time
import uuid

import httpx

from .bridge import BridgeError, OutcomeUnknown
from .original import normalize_original, verify_scope, UnsupportedState
from .parity import compare_observations
from .simulator import CONFIG, Simulator


class ScenarioFailed(BridgeError):
    pass


class ScenarioClient:
    def __init__(self, bridge, *, record=None):
        if not bridge.expected_mod_sha:
            raise ValueError("Scenario setup requires a verified Mod fingerprint")
        self.bridge = bridge
        self.request = None
        self.before = None
        self.last_state = None
        self.last_request = None
        self.record = record or (lambda event, data: None)
        self.lock = asyncio.Lock()

    async def prepare(self, encounter, seed, *, timeout=90):
        async with self.lock:
            return await self._prepare(encounter, seed, timeout=timeout)

    async def _prepare(self, encounter, seed, *, timeout):
        if self.request is not None:
            raise OutcomeUnknown(
                "Previous staging request is unresolved; reconcile without resubmitting"
            )
        if self.bridge.pending is not None:
            raise OutcomeUnknown("Resolve the pending gameplay command before staging")
        if (
            encounter not in CONFIG["encounters"]
            or type(seed) is not int
            or not 0 <= seed < 2**31
        ):
            raise ValueError("Use a supported encounter and integer seed in [0, 2^31)")
        before = await self.bridge.read_state()
        if not before.get("lab_settled"):
            await asyncio.sleep(0.3)
            before = await self.bridge.read_state()
        if before.get("lab_profile_id") != 2:
            raise BridgeError("Switch to dedicated experiment profile 2 before staging")
        if "scenario_staging_v1" not in before.get("lab_capabilities", []):
            raise BridgeError("The installed Mod does not support controlled staging")
        if (
            before.get("menu_screen") != "main"
            or before.get("state_type") != "menu"
            or before.get("lab_settled") is not True
        ):
            raise BridgeError("Scenario setup requires a settled main menu")
        self.before = before
        self.request = {
            "action": "lab_prepare",
            "lab_request_id": uuid.uuid4().hex,
            "lab_expected_token": before["lab_state_token"],
            "expected_game_sha256": self.bridge.expected_game_sha,
            "expected_mod_sha256": self.bridge.expected_mod_sha,
            "seed": seed,
            "encounter": encounter,
            "profile_id": 2,
        }
        self.last_request = dict(self.request)
        self.record("request_prepared", {"request": self.request, "before": before})
        try:
            response = await self.bridge.client.post(
                "/api/v1/singleplayer", json=self.request
            )
            response.raise_for_status()
            result = response.json()
            self.record("response_received", result)
        except (httpx.HTTPError, ValueError) as exc:
            raise OutcomeUnknown(
                "Scenario request may have executed; reconcile without another POST"
            ) from exc
        if not isinstance(result, dict):
            raise OutcomeUnknown(
                "Malformed scenario acknowledgment; reconcile without resubmitting"
            )
        if result.get("status") != "ok":
            self.request = None
            raise BridgeError(
                str(result.get("error") or result.get("message") or result)
            )
        if result.get("lab_request_id") != self.request["lab_request_id"]:
            raise OutcomeUnknown("Scenario acknowledgment does not match the request")
        return await self.reconcile(timeout=timeout)

    async def reconcile(self, *, timeout=90):
        if self.request is None:
            raise ValueError("No staging request to reconcile")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                state = await self.bridge.read_state()
            except (httpx.TransportError, httpx.HTTPStatusError):
                await asyncio.sleep(0.25)
                continue
            self.last_state = state
            self.record("state_observed", state)
            scenario = state.get("lab_scenario") or {}
            if scenario.get("request_id") == self.request["lab_request_id"]:
                if scenario.get("status") == "failed":
                    raise ScenarioFailed(
                        str(scenario.get("error", "Scenario initialization failed"))
                    )
                if (
                    scenario.get("status") == "entered"
                    and state.get("lab_action_ready") is True
                    and state.get("lab_settled") is True
                ):
                    for key in ("seed", "encounter", "profile_id"):
                        if scenario.get(key) != self.request[key]:
                            raise ScenarioFailed(f"Scenario provenance differs: {key}")
                    if (
                        state.get("lab_profile_id") != 2
                        or scenario.get("actual_floor") != CONFIG["floor"]
                        or scenario.get("completed_combats_before") != 0
                    ):
                        raise ScenarioFailed(
                            "Scenario opening context differs from the fixed benchmark"
                        )
                    required = {
                        "initializer_version": "starter-staging-v1",
                        "method": "debug_staged_non_saving_run",
                        "game_sha256": self.request["expected_game_sha256"],
                        "mod_sha256": self.request["expected_mod_sha256"],
                        "rng_initialization": "numeric_run_seed_game_named_factories_before_combat",
                    }
                    if scenario.get("should_save") is not False or any(
                        scenario.get(k) != v for k, v in required.items()
                    ):
                        raise ScenarioFailed(
                            "Scenario initializer provenance is incomplete or differs"
                        )
                    try:
                        verify_scope(state, self.request["encounter"], opening=True)
                    except UnsupportedState as exc:
                        raise ScenarioFailed(str(exc)) from exc
                    self.request = None
                    return state
            await asyncio.sleep(0.25)
        raise OutcomeUnknown(
            "Scenario has not reached a confirmed opening; reconcile without resubmitting"
        )


def compare_opening(raw, encounter, seed):
    """Independent initialization; never copy game state into the simulator."""
    verify_scope(raw, encounter, opening=True)
    reference, _ = normalize_original(raw, "staging-opening")
    result = {
        "passed": False,
        "seed": seed,
        "seed_search_performed": False,
        "simulator_state_overridden": False,
        "scope": "opening_only",
    }
    with Simulator(encounter, seed) as env:
        difference = compare_observations(reference, env.observe())
        if difference:
            return {
                **result,
                "status": "public_opening_mismatch",
                "difference": difference,
            }
        order = raw["player"].get("draw_pile_ordered")
        if order is None:
            return {**result, "status": "private_opening_evidence_missing"}
        actual = [
            {"id": c["type_id"], "is_upgraded": c["upgraded"]}
            for c in env._raw(debug=True)["debug_draw_order"]
        ]
        expected = [{"id": c["id"], "is_upgraded": c["is_upgraded"]} for c in order]
        if expected != actual:
            return {**result, "status": "private_opening_order_mismatch"}
        return {
            **result,
            "passed": True,
            "status": "opening_matched",
            "full_battle_verified": False,
        }
