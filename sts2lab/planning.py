"""Project-authored root bandit rollout search over public-history particles.

This is an approximate planning baseline, not a POMCP/ISMCTS implementation.
"""

from __future__ import annotations

import math
import hashlib
import random
import time

from pydantic import Field

from .belief import HistoryBelief, action_key, find_action, public_hash
from .contracts import Candidate, Decision, StrictModel, canonical_json
from .hierarchy import TacticalHierarchy, leaf_utility
from .policies import Policy
from .simulator import LOCK, ROOT, load_native


class PlanningConfig(StrictModel):
    version: str = "rollout-config-v1"
    particles: int = Field(default=8, ge=1, le=32, strict=True)
    init_attempts: int = Field(default=512, ge=1, le=4096, strict=True)
    update_attempts: int = Field(default=128, ge=1, le=1024, strict=True)
    search_calls: int = Field(default=256, ge=0, le=8192, strict=True)
    rollout_depth: int = Field(default=12, ge=1, le=64, strict=True)
    max_wall_ms: int | None = Field(default=2000, ge=1, le=30000, strict=True)
    exploration: float = Field(default=0.7, ge=0, le=10, allow_inf_nan=False)
    goal_max_actions: int = Field(default=3, ge=1, le=20, strict=True)


class PlanningPolicy:
    names = ("rollout", "hierarchical")

    @staticmethod
    def provenance():
        paths = [
            "sts2lab/belief.py",
            "sts2lab/hierarchy.py",
            "sts2lab/planning.py",
            "sts2lab/policies.py",
            "sts2lab/contracts.py",
            "sts2lab/simulator.py",
            "config/phase1.json",
        ]
        with LOCK:
            manifest = load_native()[2]
        return {
            "model_library_sha256": manifest["library_sha256"],
            "source_sha256": {
                p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths
            },
        }

    def __init__(self, name, seed, encounter, config=None):
        if name not in self.names:
            raise ValueError("Unknown planning policy")
        self.name = name
        self.config = config or PlanningConfig()
        if self.config.version != "rollout-config-v1":
            raise ValueError("Unsupported planning configuration version")
        self.rng = random.Random(seed)
        self.belief = HistoryBelief(
            encounter,
            self.rng.randrange(2**31),
            self.config.particles,
            self.config.init_attempts,
            self.config.update_attempts,
        )
        self.hierarchy = (
            TacticalHierarchy(self.config.goal_max_actions)
            if name == "hierarchical"
            else None
        )
        self.fallback = Policy("heuristic", 0)
        self.pending_transition = None
        self.last_report = None
        self.last_decision = None
        self.last_observation_hash = None
        self.closed = False

    def observe_transition(self, before, action, result, *, manual=False):
        if self.pending_transition is not None:
            raise ValueError("Unconsumed planning transition")
        if self.last_observation_hash != public_hash(before):
            raise ValueError("Planning feedback is outside the proposed public history")
        self.last_decision = None
        event = (
            self.hierarchy.observe_transition(
                before, result.observation, result.reward, manual
            )
            if self.hierarchy
            else None
        )
        if result.observation.outcome != "ongoing":
            if self.belief.initialized:
                self.belief.advance(before, action, result.observation)
        else:
            self.pending_transition = (before, action, result.observation)
        return event

    def _fallback(self, obs, started, report, reason, goal):
        decision = self.fallback.decide(obs)
        report["fallback_reason"] = reason
        report["elapsed_ms"] = (time.perf_counter() - started) * 1000
        self.last_report = report
        self.last_decision = decision.model_copy(
            update={
                "policy": f"{self.name}-v1",
                "elapsed_ms": report["elapsed_ms"],
                "score_semantics": "heuristic_points_fallback",
                "goal": goal.kind if goal else None,
                "parent_decision_id": goal.goal_id if goal else None,
            }
        )
        return self.last_decision

    def decide(self, obs):
        if self.closed:
            raise RuntimeError("Planning policy is closed")
        if not obs.legal_actions:
            raise ValueError("No legal decision at terminal state")
        key = public_hash(obs)
        if self.last_decision and self.last_decision.decision_id == obs.decision_id:
            if key != self.last_observation_hash:
                raise ValueError("Public state changed without a new decision")
            return self.last_decision
        if self.last_decision is not None:
            raise ValueError("Confirm the previous action before planning again")
        started = time.perf_counter()
        deadline = (
            started + self.config.max_wall_ms / 1000
            if self.config.max_wall_ms is not None
            else None
        )
        goal = self.hierarchy.select(obs) if self.hierarchy else None
        self.last_observation_hash = key
        report = {
            "schema": "planning-report-v1",
            "decision_id": obs.decision_id,
            "algorithm": "root-ucb-observable-rollout-v1",
            "config": self.config.model_dump(),
            "utility_version": "starter-public-leaf-v1",
            "goal": goal.to_dict() if goal else None,
            "model_calls": 0,
            "rollouts": 0,
            "timed_out": False,
            "candidates": [],
            "fallback_reason": None,
            "belief": {},
            "planning_uses_acting_environment": False,
        }
        if self.config.search_calls == 0:
            self.pending_transition = None
            return self._fallback(obs, started, report, "zero_search_budget", goal)
        if not self.belief.initialized:
            self.belief.initialize(obs, deadline)
        elif self.pending_transition:
            before, action, after = self.pending_transition
            if public_hash(after) != key:
                raise ValueError("Confirmed history differs from planning observation")
            self.belief.advance(before, action, after, deadline)
        elif self.belief.current_hash != key:
            raise ValueError("Missing confirmed transition before planning")
        self.pending_transition = None
        report["belief"] = dict(self.belief.report)
        report["timed_out"] = bool(self.belief.report["timed_out"])
        if not self.belief.particles:
            return self._fallback(
                obs, started, report, self.belief.report["reason"], goal
            )
        groups = {}
        for action in obs.legal_actions:
            groups.setdefault(action_key(obs, action), []).append(action)
        keys = sorted(groups, key=canonical_json)
        visits = {k: 0 for k in keys}
        totals = {k: 0.0 for k in keys}
        scenarios = []
        rollout_policy = Policy("heuristic", 0)
        while (
            report["model_calls"] + self.config.rollout_depth
            <= self.config.search_calls
        ):
            if HistoryBelief.expired(deadline):
                report["timed_out"] = True
                break
            unvisited = [k for k in keys if visits[k] == 0]
            selected = (
                unvisited[0]
                if unvisited
                else max(
                    keys,
                    key=lambda k: totals[k] / visits[k]
                    + self.config.exploration
                    * math.sqrt(math.log(max(1, report["rollouts"])) / visits[k]),
                )
            )
            ordinal = visits[selected]
            while len(scenarios) <= ordinal:
                scenarios.append(self.rng.randrange(2**31))
            parent = self.belief.particles[ordinal % len(self.belief.particles)]
            complete = True
            with parent.sample_world(scenarios[ordinal]) as world:
                current = world.observe()
                if public_hash(current) != key:
                    raise RuntimeError(
                        "Search world violates public belief constraints"
                    )
                for depth in range(self.config.rollout_depth):
                    if HistoryBelief.expired(deadline):
                        report["timed_out"] = True
                        complete = False
                        break
                    if depth == 0:
                        action = find_action(current, selected)
                    else:
                        proposed = rollout_policy.decide(current).selected_action_id
                        action = next(
                            a for a in current.legal_actions if a.action_id == proposed
                        )
                    if action is None:
                        raise RuntimeError("Sampled search action is unavailable")
                    current = world.step(
                        action.action_id, current.decision_id
                    ).observation
                    report["model_calls"] += 1
                    if current.outcome != "ongoing":
                        break
                if complete:
                    totals[selected] += leaf_utility(obs, current, goal)
                    visits[selected] += 1
                    report["rollouts"] += 1
            if not complete:
                break
        report["candidates"] = [
            {
                "action_ids": [a.action_id for a in groups[k]],
                "visits": visits[k],
                "mean_utility": totals[k] / visits[k] if visits[k] else None,
            }
            for k in keys
        ]
        if any(n == 0 for n in visits.values()):
            reason = (
                "time_limit_before_all_actions"
                if report["timed_out"]
                else "budget_before_all_actions"
            )
            return self._fallback(obs, started, report, reason, goal)
        candidates = [
            Candidate(
                action_id=a.action_id,
                score=totals[k] / visits[k],
                reasons=[
                    f"{visits[k]} 次模拟分支 rollout 的平均效用（非胜率）",
                    f"公开历史约束下 {len(self.belief.particles)} 个粒子",
                    f"战术目标：{goal.kind}" if goal else "无上层目标的平坦搜索",
                ],
            )
            for k in keys
            for a in groups[k]
        ]
        candidates.sort(key=lambda c: c.score, reverse=True)
        report["elapsed_ms"] = (time.perf_counter() - started) * 1000
        self.last_report = report
        self.last_decision = Decision(
            decision_id=obs.decision_id,
            policy=f"{self.name}-v1",
            selected_action_id=candidates[0].action_id,
            candidates=candidates,
            elapsed_ms=report["elapsed_ms"],
            score_semantics="sampled_rollout_utility",
            goal=goal.kind if goal else None,
            parent_decision_id=goal.goal_id if goal else None,
        )
        return self.last_decision

    def close(self):
        self.belief.close()
        self.pending_transition = None
        self.closed = True
