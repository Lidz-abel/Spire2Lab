"""One session owner; cached views stay responsive during original-game actions."""

import asyncio
from collections import OrderedDict
import inspect
from pathlib import Path
import time
import uuid

from .bridge import OutcomeUnknown
from .contracts import StepRequest, digest, semantic_state
from .environment import Environment
from .original import OriginalEnvironment
from .policies import Policy
from .planning import PlanningConfig, PlanningPolicy
from .simulator import Simulator, CONFIG, ROOT
from .traces import TraceWriter
from .vocabulary import vocabulary
from .images import ImageStore


async def await_if_needed(result):
    return await result if inspect.isawaitable(result) else result


class Lab:
    def __init__(self, data_dir=None, *, original_factory=None):
        self.data_dir = Path(data_dir or ROOT / "artifacts/runs")
        self.images = ImageStore(self.data_dir.parent / "images")
        self.original_factory = original_factory or OriginalEnvironment.attach
        self.lock = asyncio.Lock()
        self.env: Environment | None = None
        self.trace = None
        self.status = "idle"
        self.revision = 0
        self.cache = OrderedDict()
        self.delay = 0.8
        self.error = None
        self.history = []
        self.last_result = None
        self.pending = None
        self.resume_after_step = False
        self.planning = None
        self.goal_event = None
        self.decision_image = None

    async def _capture_image(self):
        self.decision_image = None
        if self.metadata["backend"] != "original_game":
            return
        binding = {
            "run_id": self.run_id,
            "decision_id": self.observation.decision_id,
            "observation_sha256": digest(self.observation),
        }
        if not self.env.capabilities.get("original_pixels"):
            self.decision_image = {
                **binding,
                "status": "unavailable",
                "reason": "bridge_capability_missing",
            }
        else:
            previous_status = self.status
            self.status = "planning"
            self.revision += 1
            try:
                metadata, png = await self.env.capture_image()
                self.decision_image = await asyncio.to_thread(
                    self.images.put,
                    self.run_id,
                    metadata,
                    png,
                    self.observation.decision_id,
                    binding["observation_sha256"],
                )
            except Exception as exc:
                self.decision_image = {
                    **binding,
                    "status": "unavailable",
                    "reason": type(exc).__name__,
                    "detail": str(exc)[:300],
                }
            finally:
                self.status = (
                    "paused"
                    if previous_status == "running" and not self.resume_after_step
                    else previous_status
                )
        self.trace.append("decision_image", self.decision_image)

    async def _proposal(self):
        self.decision, self.planning = None, None
        await self._capture_image()
        if self.observation.legal_actions:
            if isinstance(self.policy, PlanningPolicy):
                previous_status = self.status
                self.status = "planning"
                self.revision += 1
                task = asyncio.create_task(
                    asyncio.to_thread(self.policy.decide, self.observation)
                )
                try:
                    self.decision = await asyncio.shield(task)
                except asyncio.CancelledError:
                    # Do not destroy native particles while the bounded worker still
                    # uses them. Cancellation never submits a game action.
                    await task
                    raise
                finally:
                    self.status = (
                        "paused"
                        if previous_status == "running" and not self.resume_after_step
                        else previous_status
                    )
                self.planning = self.policy.last_report
                self.trace.append("planning_report", self.planning)
            else:
                self.decision = self.policy.decide(self.observation)
        if self.decision:
            self.trace.append("decision", self.decision.model_dump())

    def _close_policy(self):
        policy = getattr(self, "policy", None)
        if isinstance(policy, PlanningPolicy):
            policy.close()

    def _interrupt_goal(self, reason):
        policy = getattr(self, "policy", None)
        if self.trace and isinstance(policy, PlanningPolicy) and policy.hierarchy:
            event = policy.hierarchy.interrupt(reason, self.observation.decision_id)
            if event:
                self.trace.append("goal_completed", event)

    def _require_free(self):
        if self.lock.locked() or self.status in ("executing", "reconciling"):
            raise ValueError("An operation is in progress; wait for its result")
        if self.pending is not None:
            raise OutcomeUnknown(
                "Resolve the previous command before changing the session"
            )

    async def new_session(
        self,
        encounter="nibbits-weak",
        seed=1,
        policy="heuristic",
        policy_seed=0,
        backend="native_simulator",
        planning_config=None,
    ):
        self._require_free()
        async with self.lock:
            if policy in PlanningPolicy.names:
                config = (
                    PlanningConfig.model_validate(planning_config)
                    if planning_config is not None
                    else PlanningConfig()
                )
                new_policy = PlanningPolicy(policy, policy_seed, encounter, config)
            else:
                if planning_config is not None:
                    raise ValueError(
                        "Planning configuration requires a planning policy"
                    )
                new_policy = Policy(policy, policy_seed)
            if backend == "native_simulator":
                new_env = Simulator(encounter, seed)
            elif backend == "original_game":
                new_env = await self.original_factory(encounter)
            else:
                raise ValueError("Unknown environment backend")
            try:
                new_obs = new_env.observe()
            except BaseException:
                await await_if_needed(new_env.close())
                raise
            if self.trace:
                self._interrupt_goal("session_reset")
                self.trace.append(
                    "session_closed", {"reason": "user_reset", "status": self.status}
                )
                self.trace.close()
                await await_if_needed(self.env.close())
            self._close_policy()
            self.env, self.policy = new_env, new_policy
            self.run_id = uuid.uuid4().hex
            self.trace = TraceWriter(self.data_dir / f"{self.run_id}.jsonl")
            self.observation = new_obs
            self.status, self.error = "paused", None
            self.history, self.last_result = [], None
            self.planning, self.goal_event = None, None
            self.pending, self.resume_after_step = None, False
            self.cache.clear()
            self.metadata = {
                "run_id": self.run_id,
                "backend": backend,
                "reference_status": "unverified_locally",
                "config": CONFIG,
                "encounter": encounter,
                "seed": new_env.seed,
                "policy": policy,
                "policy_seed": policy_seed,
                "build": new_env.manifest,
                "capabilities": new_env.capabilities,
                "branch_provenance": (
                    new_env.branch_provenance.model_dump()
                    if new_env.branch_provenance is not None
                    else None
                ),
                "content_vocabulary": vocabulary().metadata(),
            }
            if backend == "original_game":
                self.metadata["raw_capture_id"] = new_env.epoch
                self.metadata["opening_capture"] = new_env.last_capture
                self.metadata["printed_card_values_source"] = (
                    "pinned_catalog_not_live_measurement"
                )
            if isinstance(new_policy, PlanningPolicy):
                self.metadata["planning_config"] = new_policy.config.model_dump()
                self.metadata["planning_information"] = "confirmed_public_history_only"
                self.metadata["planning_provenance"] = new_policy.provenance()
            self.trace.append(
                "session_started",
                {"metadata": self.metadata, "observation": new_obs.model_dump()},
            )
            await self._proposal()
            self.revision += 1
            return self.view()

    def view(self):
        return {
            "revision": self.revision,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
            "observation": self.observation.model_dump(),
            "decision": self.decision.model_dump() if self.decision else None,
            "planning": self.planning,
            "goal_event": self.goal_event,
            "decision_image": self.decision_image,
            "last_result": self.last_result,
            "history": self.history[-80:],
            "delay": self.delay,
            "resume_after_step": self.resume_after_step,
            "pending_request_id": (
                self.pending["request"].request_id if self.pending else None
            ),
        }

    def _failure(self, exc):
        uncertain = (
            isinstance(exc, OutcomeUnknown)
            or getattr(getattr(self.env, "client", None), "pending", None) is not None
        )
        self.status = "awaiting_confirmation" if uncertain else "error"
        self.resume_after_step = False
        self.error = f"{type(exc).__name__}: {exc}"
        self.trace.append(
            "action_outcome_unknown" if uncertain else "infrastructure_error",
            {
                "error": self.error,
                "request_id": (
                    self.pending["request"].request_id if self.pending else None
                ),
            },
        )
        if not uncertain:
            self.pending = None
        self.revision += 1

    async def step(self, req: StepRequest, *, automatic=False):
        fingerprint = digest(req)
        if req.request_id in self.cache:
            previous, response = self.cache[req.request_id]
            if previous != fingerprint:
                raise ValueError(
                    "request_id_conflict: same identifier with different command"
                )
            return response
        if self.pending and self.pending["request"].request_id == req.request_id:
            if self.pending["fingerprint"] != fingerprint:
                raise ValueError(
                    "request_id_conflict: same identifier with different command"
                )
            raise OutcomeUnknown(
                "This request is already in progress; read state or reconcile, do not resubmit"
            )
        self._require_free()
        async with self.lock:
            if self.status not in ("paused", "running") or (
                self.status == "running" and not automatic
            ):
                raise ValueError("Pause the running session before a manual step")
            if req.decision_id != self.observation.decision_id:
                raise ValueError("stale_decision: reload the latest observation")
            action_id = req.action_id or self.decision.selected_action_id
            action = next(
                (a for a in self.observation.legal_actions if a.action_id == action_id),
                None,
            )
            if action is None:
                raise ValueError("illegal_action")
            manual = action_id != self.decision.selected_action_id
            self.pending = {
                "request": req,
                "fingerprint": fingerprint,
                "action": action,
                "before": self.observation,
                "manual": manual,
                "started": time.perf_counter(),
            }
            self.trace.append(
                "action_submitted",
                {
                    "request": req.model_dump(),
                    "action": action.model_dump(),
                    "manual_intervention": manual,
                },
            )
            self.resume_after_step = self.status == "running"
            self.status, self.error = "executing", None
            self.revision += 1
            try:
                result = await await_if_needed(
                    self.env.step(action_id, req.decision_id, request_id=req.request_id)
                )
                return await self._complete(result)
            except Exception as exc:
                self._failure(exc)
                raise

    async def _complete(self, result):
        pending = self.pending
        action, req = pending["action"], pending["request"]
        self.observation = result.observation
        payload = result.model_dump()
        payload["facts"]["manual_intervention"] = pending["manual"]
        payload["execution_ms"] = (time.perf_counter() - pending["started"]) * 1000
        payload["semantic_hash"] = digest(semantic_state(result.observation))
        self.trace.append(
            "transition",
            {"request_id": req.request_id, "action": action.model_dump(), **payload},
        )
        self.goal_event = None
        if isinstance(self.policy, PlanningPolicy):
            self.goal_event = self.policy.observe_transition(
                pending["before"], action, result, manual=pending["manual"]
            )
            if self.goal_event:
                self.trace.append("goal_completed", self.goal_event)
        self.last_result = {
            "action": action.model_dump(),
            "facts": payload["facts"],
            "execution_ms": payload["execution_ms"],
        }
        self.history.append(
            {
                "step": self.env.sequence,
                "turn": pending["before"].turn,
                "label": action.label,
                "hp": result.observation.player.hp,
                "hp_delta": payload["facts"]["player_hp_delta"],
                "manual": pending["manual"],
            }
        )
        self.status = (
            "finished"
            if result.terminated or result.truncated
            else "running" if self.resume_after_step else "paused"
        )
        self.pending, self.error = None, None
        await self._proposal()
        self.revision += 1
        response = self.view()
        self.cache[req.request_id] = (pending["fingerprint"], response)
        if len(self.cache) > 1024:
            self.cache.popitem(last=False)
        return response

    async def reconcile(self):
        if self.lock.locked():
            raise ValueError("An operation is already in progress")
        async with self.lock:
            if self.status != "awaiting_confirmation" or not self.pending:
                raise ValueError("No unresolved command to reconcile")
            self.status, self.error = "reconciling", None
            self.revision += 1
            try:
                return await self._complete(await self.env.reconcile())
            except Exception as exc:
                self._failure(exc)
                raise

    async def archive(self, run_id):
        """Detach the lab; leave the game untouched and retain uncertain commands."""
        if self.lock.locked():
            raise ValueError("Wait for the current operation before archiving")
        async with self.lock:
            if run_id != self.run_id:
                raise ValueError("stale_session: reload the current experiment")
            if self.status == "closed":
                return self.view()
            if self.status == "running":
                raise ValueError("Pause automatic decisions before archiving")
            self._interrupt_goal("session_archived")
            self.trace.append(
                "session_archived",
                {
                    "reason": "user_detached",
                    "status": self.status,
                    "unresolved_request_id": (
                        self.pending["request"].request_id if self.pending else None
                    ),
                    "last_error": self.error,
                    "game_action_sent": False,
                    "game_outcome": (
                        "unknown" if self.pending else self.observation.outcome
                    ),
                },
            )
            try:
                await await_if_needed(self.env.close())
            finally:
                self._close_policy()
                self.trace.close()
                self.trace = self.env = self.pending = self.decision = None
                self.cache.clear()
                self.resume_after_step = False
                self.status, self.error = "closed", None
                self.revision += 1
            return self.view()

    async def control(self, running, delay=None):
        if delay is not None and not 0.1 <= delay <= 5:
            raise ValueError("Delay must be between 0.1 and 5 seconds")
        # A pause stops future decisions immediately; it cannot undo an action that
        # the game is already executing. Do not wait behind the animation lock.
        if self.status in (
            "executing",
            "reconciling",
            "awaiting_confirmation",
            "planning",
        ):
            if running:
                raise ValueError("Wait for the original game's result before resuming")
            self.resume_after_step = False
            self.trace.append(
                "control", {"status": self.status, "pause_after_current_action": True}
            )
            self.revision += 1
            return self.view()
        self._require_free()
        async with self.lock:
            if self.status not in ("paused", "running"):
                raise ValueError("Create a new session before running")
            if delay is not None:
                self.delay = delay
            self.status = "running" if running else "paused"
            self.resume_after_step = running
            self.trace.append("control", {"status": self.status, "delay": self.delay})
            self.revision += 1
            return self.view()

    async def worker(self):
        while True:
            await asyncio.sleep(self.delay if self.status == "running" else 0.1)
            if self.status == "running":
                try:
                    await self.step(
                        StepRequest(
                            request_id=uuid.uuid4().hex,
                            decision_id=self.observation.decision_id,
                        ),
                        automatic=True,
                    )
                except Exception:
                    # step persists execution failures; a concurrent pause/reset can
                    # also invalidate a queued automatic command before submission.
                    continue

    def trace_path(self, run_id):
        if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
            raise ValueError("Invalid run identifier")
        path = self.data_dir / f"{run_id}.jsonl"
        if not path.is_file():
            raise FileNotFoundError(run_id)
        return path

    async def close(self):
        self._interrupt_goal("server_shutdown")
        self._close_policy()
        if self.trace:
            self.trace.append(
                "session_closed",
                {
                    "reason": "server_shutdown",
                    "status": self.status,
                    "pending_request_id": (
                        self.pending["request"].request_id if self.pending else None
                    ),
                },
            )
            self.trace.close()
            self.trace = None
        if self.env:
            await await_if_needed(self.env.close())
            self.env = None
