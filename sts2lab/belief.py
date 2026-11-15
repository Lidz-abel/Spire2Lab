"""Bounded approximate particles conditioned only on confirmed public history.

The acting environment is never an input. Native clones belong to independently
generated particles. Hidden-state resampling is an attributed simulator service.
"""

from __future__ import annotations

import random
import time

from .contracts import Action, Observation, canonical_json, digest
from .simulator import Simulator


def card_key(card):
    return canonical_json(card.model_dump(exclude={"ref", "name"}))


def action_key(obs: Observation, action: Action):
    cards = {c.ref: c for c in obs.hand}
    targets = {e.ref: i for i, e in enumerate(obs.enemies)}
    return (
        action.kind,
        card_key(cards[action.card_ref]) if action.card_ref else "",
        targets[action.target_ref] if action.target_ref else -1,
    )


def find_action(obs, key):
    return next((a for a in obs.legal_actions if action_key(obs, a) == key), None)


def public_state(obs):
    """Hand permutations are equivalent; known draw positions stay ordered."""
    return {
        "phase": obs.phase,
        "turn": obs.turn,
        "player": obs.player.model_dump(),
        "outcome": obs.outcome,
        "unavailable_fields": sorted(obs.unavailable_fields),
        "hand": sorted(map(card_key, obs.hand)),
        "draw": sorted(map(card_key, obs.draw_pile)),
        "discard": sorted(map(card_key, obs.discard_pile)),
        "exhaust": sorted(map(card_key, obs.exhaust_pile)),
        "known_top": list(map(card_key, obs.known_top)),
        "known_bottom": list(map(card_key, obs.known_bottom)),
        "enemies": [e.model_dump(exclude={"ref", "name"}) for e in obs.enemies],
        "relics": sorted(r.type_id for r in obs.relics),
        "legal": sorted(action_key(obs, a) for a in obs.legal_actions),
    }


def public_hash(obs):
    return digest(public_state(obs))


class HistoryBelief:
    """Rejection at initialization; resample/propagate/filter after each action.

    This preserves observed history constraints in surviving particles, but
    reseeding future RNG is an approximation rather than posterior MCMC.
    Depletion is explicit and permanent for this episode; no oracle recovery.
    """

    def __init__(
        self,
        encounter,
        seed,
        particles=8,
        init_attempts=512,
        update_attempts=128,
        *,
        factory=Simulator,
        proposal="seed_rejection",
    ):
        self.encounter = encounter
        self.rng = random.Random(seed)
        self.target = particles
        self.init_attempts = init_attempts
        self.update_attempts = update_attempts
        self.factory = factory
        if proposal not in ("seed_rejection", "public_opening"):
            raise ValueError("Unknown belief proposal")
        self.proposal = proposal
        self.particles = []
        self.current_hash = None
        self.history_digest = None
        self.steps = 0
        self.initialized = False
        self.report = {}

    @staticmethod
    def expired(deadline):
        return deadline is not None and time.perf_counter() >= deadline

    def initialize(self, obs, deadline=None):
        if self.initialized:
            raise ValueError("Belief already initialized")
        self.initialized = True
        self.current_hash = public_hash(obs)
        self.history_digest = self.current_hash
        counts = {
            "initializations": 0,
            "model_calls": 0,
            "resamples": 0,
            "rejections": 0,
            "timed_out": False,
        }
        if (
            obs.turn != 0
            or obs.phase != "combat"
            or obs.unavailable_fields
            or len(obs.hand) != 5
            or obs.discard_pile
            or obs.exhaust_pile
            or obs.player.energy != 3
            or obs.player.hp != 80
            or (
                self.proposal == "public_opening"
                and (obs.outcome != "ongoing" or obs.known_top or obs.known_bottom)
            )
        ):
            self._report(counts, "unsupported_opening")
            return self.report
        try:
            for _ in range(self.init_attempts):
                if self.expired(deadline):
                    counts["timed_out"] = True
                    break
                counts["initializations"] += 1
                proposal_seed = self.rng.randrange(2**31)
                world = (
                    self.factory.from_public_opening(self.encounter, obs, proposal_seed)
                    if self.proposal == "public_opening"
                    else self.factory(self.encounter, proposal_seed)
                )
                if world is None:
                    counts["rejections"] += 1
                    continue
                try:
                    matches = public_hash(world.observe()) == self.current_hash
                except BaseException:
                    world.close()
                    raise
                if matches:
                    self.particles.append(world)
                    if len(self.particles) == self.target:
                        break
                else:
                    counts["rejections"] += 1
                    world.close()
        except BaseException:
            self.close()
            raise
        self._report(counts, "initialization_depleted" if not self.particles else None)
        return self.report

    def advance(self, before, action, after, deadline=None):
        if public_hash(before) != self.current_hash:
            raise ValueError("Belief history does not match the confirmed transition")
        key = action_key(before, action)
        wanted = public_hash(after)
        self.history_digest = digest([self.history_digest, key, wanted])
        self.steps += 1
        counts = {
            "initializations": 0,
            "model_calls": 0,
            "resamples": 0,
            "rejections": 0,
            "timed_out": False,
        }
        old, survivors = self.particles, []
        self.particles = []
        try:
            if after.outcome == "ongoing":
                for trial in range(self.update_attempts if old else 0):
                    if self.expired(deadline):
                        counts["timed_out"] = True
                        break
                    branch = old[trial % len(old)].sample_world(
                        self.rng.randrange(2**31)
                    )
                    counts["resamples"] += 1
                    keep = False
                    try:
                        current = branch.observe()
                        if public_hash(current) != self.current_hash:
                            raise RuntimeError(
                                "Particle resampling changed public state"
                            )
                        mapped = find_action(current, key)
                        if mapped is None:
                            raise RuntimeError("Particle lacks a public legal action")
                        result = branch.step(mapped.action_id, current.decision_id)
                        counts["model_calls"] += 1
                        keep = public_hash(result.observation) == wanted
                        if keep:
                            survivors.append(branch)
                        else:
                            counts["rejections"] += 1
                    finally:
                        if not keep:
                            branch.close()
                    if len(survivors) == self.target:
                        break
            self.particles = survivors
        except BaseException:
            for branch in survivors:
                branch.close()
            raise
        finally:
            for world in old:
                world.close()
        self.current_hash = wanted
        reason = (
            "terminal"
            if after.outcome != "ongoing"
            else ("history_particles_depleted" if not self.particles else None)
        )
        self._report(counts, reason)
        return self.report

    def _report(self, counts, reason):
        self.report = {
            **counts,
            "particles": len(self.particles),
            "target_particles": self.target,
            "conditioned_transitions": self.steps,
            "history_digest": self.history_digest,
            "reason": reason,
            "method": (
                "public-history-conditioned-opening-v2"
                if self.proposal == "public_opening"
                else "public-history-rejection-resample-v1"
            ),
            "exact_posterior_claim": False,
        }

    def close(self):
        for world in self.particles:
            world.close()
        self.particles = []
