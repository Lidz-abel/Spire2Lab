"""A single normal-run owner with explicit evidence, reconciliation and pause."""

import asyncio
import hashlib
import json
from pathlib import Path
import re
import uuid

from .acceptance import verify_windows_bundle, sha
from .act_bridge import ActBridge
from .act_contracts import normalize_act, check_continuity
from .act_policy import ActPolicy
from .bridge import BridgeError, OutcomeUnknown
from .contracts import digest, canonical_json
from .images import ImageStore
from .simulator import ROOT
from .traces import TraceWriter, read_trace


class ActLab:
    def __init__(self, data_dir, *, factory=None):
        self.data_dir = Path(data_dir)
        self.images = ImageStore(self.data_dir.parent / "act-images")
        self.factory = factory
        self.lock = asyncio.Lock()
        self.client = self.trace = self.observation = self.raw = None
        self.run_id = self.decision = self.decision_image = self.error = None
        self.status = "idle"
        self.running = False
        self.delay = 1.0
        self.pending = None
        self.sequence = 0
        self.history = []
        self.cache = {}
        self.visited = []
        self.expected_destination = None
        self.saw_boss = False
        self.policy = ActPolicy()

    @property
    def active(self):
        return self.status not in ("idle", "closed")

    def trace_path(self, run_id):
        if not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise ValueError("Invalid act run ID")
        path = (self.data_dir / (run_id + ".jsonl")).resolve()
        if not path.is_relative_to(self.data_dir.resolve()):
            raise ValueError("Act path escapes storage")
        return path

    def view(self):
        return {
            "run_id": self.run_id,
            "status": self.status,
            "running": self.running,
            "observation": (
                self.observation.model_dump(mode="json") if self.observation else None
            ),
            "decision": self.decision,
            "decision_image": self.decision_image,
            "history": self.history,
            "error": self.error,
            "pending_request_id": self.pending["request_id"] if self.pending else None,
        }

    def _capture_raw(self, raw):
        folder = self.data_dir.parent / "act-raw" / self.run_id
        folder.mkdir(parents=True, exist_ok=True)
        data = canonical_json(raw).encode()
        name = hashlib.sha256(data).hexdigest() + ".json"
        path = folder / name
        if not path.exists():
            with path.open("xb") as f:
                f.write(data)
        self.last_capture = {
            "capture_sha256": name[:-5],
            "path": str(path.relative_to(self.data_dir.parent)),
        }
        return self.last_capture

    async def start(self, seed):
        if not re.fullmatch(r"[A-Z0-9]{1,24}", seed):
            raise ValueError("Seed must contain 1–24 uppercase ASCII letters/digits")
        async with self.lock:
            if self.active:
                raise ValueError("Archive the current act before starting another")
            if self.factory:
                self.client, manifest = self.factory()
            else:
                manifest = verify_windows_bundle(ROOT, sha)
                self.client = ActBridge(
                    manifest["game_assembly_sha256"], mod_sha256=manifest["mod_sha256"]
                )
            self.run_id = uuid.uuid4().hex
            self.policy = ActPolicy()
            self.sequence, self.history, self.cache, self.visited = 0, [], {}, []
            self.observation = self.decision = self.decision_image = self.raw = None
            self.expected_destination, self.saw_boss = None, False
            self.trace = TraceWriter(self.trace_path(self.run_id))
            source_files = [
                "sts2lab/act_contracts.py",
                "sts2lab/act_policy.py",
                "sts2lab/act_bridge.py",
                "sts2lab/act_runtime.py",
                "config/single-act-v1.json",
            ]
            self.trace.append(
                "session_started",
                {
                    "metadata": {
                        "protocol_version": "single-act-v1",
                        "backend": "original_game",
                        "run_id": self.run_id,
                        "seed": seed,
                        "policy": self.policy.version,
                        "bridge": manifest,
                        "reward_version": "first-act-terminal-v1",
                        "should_save": False,
                        "source_sha256": {
                            name: sha(ROOT / name) for name in source_files
                        },
                    }
                },
            )
            request_id = uuid.uuid4().hex
            self.pending = {"request_id": request_id, "kind": "start", "seed": seed}
            self.trace.append("start_submitted", self.pending)
            self.status, self.error, self.running = "starting", None, False
            try:
                raw = await self.client.start_act(seed, request_id=request_id)
                await self._confirm(raw)
            except Exception as exc:
                self._error(exc)
            return self.view()

    def _error(self, exc):
        self.running = False
        self.error = str(exc)
        capture_error = None
        if self.client and getattr(self.client, "latest_state", None) is not None:
            try:
                self._capture_raw(self.client.latest_state)
            except (OSError, ValueError, TypeError) as capture_exc:
                capture_error = str(capture_exc)
        uncertain = isinstance(exc, OutcomeUnknown) or bool(
            self.client and self.client.pending
        )
        self.status = "awaiting_confirmation" if uncertain else "error"
        self.trace.append(
            "infrastructure_error",
            {
                "message": str(exc),
                "outcome_unknown": uncertain,
                "request_id": self.pending["request_id"] if self.pending else None,
                "last_capture": getattr(self, "last_capture", None),
                "capture_error": capture_error,
            },
        )
        if not uncertain:
            self.pending = None

    async def _confirm(self, raw):
        capture = self._capture_raw(raw)
        obs, mapping = normalize_act(raw, f"{self.run_id}:{self.sequence}")
        pending = self.pending
        before = self.observation
        if before:
            action = pending["action"]
            check_continuity(before, obs, action)
            if action.kind == "choose_map_node":
                selected = next(
                    n
                    for n in before.screen["next_options"]
                    if n["index"] == action.index
                )
                self.expected_destination = (selected["col"], selected["row"])
            record = {
                "request_id": pending["request_id"],
                "action": action.model_dump(),
                "before_decision_id": before.decision_id,
                "observation": obs.model_dump(mode="json"),
                "reward": (
                    1
                    if obs.outcome == "act_complete"
                    else -1 if obs.outcome == "lost" else 0
                ),
                "terminated": obs.outcome != "ongoing",
                "truncated": False,
                **capture,
            }
        if obs.phase == "map":
            visited = [(n["col"], n["row"]) for n in obs.screen["visited"]]
            if visited[: len(self.visited)] != self.visited:
                raise ValueError("Actual visited route is not a continuation")
            if (
                self.expected_destination
                and self.expected_destination not in visited[len(self.visited) :]
            ):
                raise ValueError(
                    "Selected destination was not recorded in the visited route"
                )
            self.visited = visited
            self.expected_destination = None
        if obs.phase == "boss" and obs.battle:
            self.saw_boss = True
        if obs.outcome == "act_complete" and not self.saw_boss:
            raise ValueError("Controller did not observe the boss combat")
        if before:
            self.policy.observe_transition(before, action, obs)
            self.trace.append("transition", record)
            self.history.append(
                {
                    "step": len(self.history) + 1,
                    "floor": before.floor,
                    "phase": before.phase,
                    "action": action.label,
                    "kind": action.kind,
                    "hp_after": obs.player["hp"],
                    "override": pending["override"],
                }
            )
        else:
            self.trace.append(
                "observation", {"observation": obs.model_dump(mode="json"), **capture}
            )
        self.raw, self.observation, self.action_map = raw, obs, mapping
        self.sequence += 1
        self.pending, self.error = None, None
        self.decision_image = None
        self.status = "capturing"
        try:
            metadata, png = await self.client.capture_image(raw)
            self.decision_image = await asyncio.to_thread(
                self.images.put,
                self.run_id,
                metadata,
                png,
                obs.decision_id,
                digest(obs),
            )
            self.decision_image["url"] = (
                f"/api/act/runs/{self.run_id}/images/{metadata['sha256']}.png"
            )
        except Exception as exc:
            self.decision_image = {
                "status": "unavailable",
                "run_id": self.run_id,
                "decision_id": obs.decision_id,
                "observation_sha256": digest(obs),
                "reason": str(exc),
            }
        self.trace.append("decision_image", self.decision_image)
        self.decision = self.policy.decide(
            obs, interrupted=bool(before and pending["override"])
        )
        if self.decision:
            self.trace.append("decision", self.decision)
        terminal = obs.outcome != "ongoing"
        if terminal and self.policy.goal:
            self.trace.append(
                "goal_ended", {**self.policy.goal, "termination_reason": obs.outcome}
            )
            self.policy.goal = None
        self.status = (
            "complete"
            if terminal
            else (
                "unsupported"
                if obs.unsupported_reason
                else "running" if self.running else "paused"
            )
        )
        if terminal or obs.unsupported_reason:
            self.running = False
        if before:
            self.cache[pending["request_id"]] = (pending["fingerprint"], self.view())

    async def step(self, request, *, automatic=False):
        fingerprint = digest(request)
        if request.request_id in self.cache:
            expected, result = self.cache[request.request_id]
            if expected != fingerprint:
                raise ValueError("request_id_conflict")
            return result
        if self.pending:
            if (
                self.pending["request_id"] == request.request_id
                and self.pending.get("fingerprint") == fingerprint
            ):
                return self.view()
            raise OutcomeUnknown("Resolve the pending act request first")
        if self.lock.locked():
            raise ValueError("Act controller busy")
        async with self.lock:
            if self.status not in ("paused", "running") or (
                self.running and not automatic
            ):
                raise ValueError("Pause before manually stepping the act")
            if request.decision_id != self.observation.decision_id:
                raise ValueError("stale_decision")
            selected = request.action_id or self.decision["selected_action_id"]
            action = next(
                (a for a in self.observation.legal_actions if a.action_id == selected),
                None,
            )
            if action is None:
                raise ValueError("illegal_action")
            self.pending = {
                "request_id": request.request_id,
                "fingerprint": fingerprint,
                "kind": "action",
                "action": action,
                "override": request.action_id is not None,
                "decision_id": request.decision_id,
            }
            self.trace.append(
                "action_submitted", {**self.pending, "action": action.model_dump()}
            )
            self.status = "executing"
            self.decision_image = None
            try:
                raw = await self.client.choose(
                    self.action_map[selected],
                    self.raw["lab_state_token"],
                    request_id=request.request_id,
                )
                await self._confirm(raw)
            except Exception as exc:
                self._error(exc)
            return self.view()

    async def reconcile(self):
        async with self.lock:
            if self.status != "awaiting_confirmation" or not self.pending:
                raise ValueError("No unresolved act command")
            self.status = "reconciling"
            try:
                await self._confirm(await self.client.reconcile())
            except Exception as exc:
                self._error(exc)
            return self.view()

    async def control(self, running, delay=None):
        if delay is not None:
            self.delay = delay
        if running and self.status not in ("paused", "running"):
            raise ValueError("Act cannot run from current state")
        self.running = running
        if self.status in ("paused", "running"):
            self.status = "running" if running else "paused"
        if self.trace:
            self.trace.append("control", {"running": running, "delay": self.delay})
        return self.view()

    async def worker(self):
        from .contracts import StepRequest

        while True:
            await asyncio.sleep(self.delay if self.running else 0.1)
            if self.running and self.status == "running":
                if len(self.history) >= 1200:
                    await self.control(False)
                    self.status = "step_limit"
                    self.trace.append(
                        "truncation",
                        {
                            "reason": "step_limit",
                            "terminated": False,
                            "truncated": True,
                        },
                    )
                    continue
                try:
                    await self.step(
                        StepRequest(
                            request_id=uuid.uuid4().hex,
                            decision_id=self.observation.decision_id,
                        ),
                        automatic=True,
                    )
                except Exception as exc:
                    self._error(exc)

    async def archive(self, run_id):
        async with self.lock:
            if run_id != self.run_id or self.running:
                raise ValueError("Pause this act before archiving")
            if self.pending:
                raise OutcomeUnknown(
                    "Reconcile the pending act command before archiving"
                )
            await self.close()
            return self.view()

    async def close(self):
        self.running = False
        if self.trace:
            terminal = self.observation and self.observation.outcome != "ongoing"
            if self.policy.goal:
                self.trace.append(
                    "goal_ended",
                    {**self.policy.goal, "termination_reason": "session_closed"},
                )
                self.policy.goal = None
            self.trace.append(
                "session_closed",
                {
                    "status": self.status,
                    "terminated": bool(terminal),
                    "truncated": not terminal,
                    "pending_request_id": (
                        self.pending["request_id"] if self.pending else None
                    ),
                },
            )
            self.trace.close()
            self.trace = None
        if self.client:
            await self.client.close()
            self.client = None
        self.status = "closed"
