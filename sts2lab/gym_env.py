"""Gymnasium training interface over the same semantic simulator used by the UI.

Versioned padded entity encoding; categorical columns are IDs, not magnitudes.
An exceeded capacity is an explicit error, never silent observation truncation.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np

from .simulator import Simulator, CONFIG

MAX_ACTIONS = 64
ENCODING_VERSION = "combat-entities-v2"


class CombatEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, encounter="nibbits-weak"):
        self.encounter = encounter
        self.sim = None
        self.attempts = 0
        self.done = False
        self.action_space = spaces.Discrete(MAX_ACTIONS)
        shapes = {
            "player": (8,),
            "hand": (10, 7),
            "piles": (3, 64, 7),
            "known_order": (2, 10, 7),
            "enemies": (6, 13),
            "powers": (7, 16, 2),
            "relics": (8, 2),
            "actions": (MAX_ACTIONS, 3),
        }
        self.observation_space = spaces.Dict(
            {
                **{
                    k: spaces.Box(-(2**30), 2**30, shape=s, dtype=np.int32)
                    for k, s in shapes.items()
                },
                "action_mask": spaces.MultiBinary(MAX_ACTIONS),
            }
        )

    def _encode(self):
        o = self.sim.observe()
        result = {
            k: np.zeros(s.shape, dtype=s.dtype)
            for k, s in self.observation_space.spaces.items()
        }
        self.actions = o.legal_actions
        if len(self.actions) > MAX_ACTIONS:
            raise RuntimeError("Action encoding capacity exceeded")
        result["action_mask"][: len(self.actions)] = 1
        p = o.player
        result["player"][:] = [
            p.hp,
            p.max_hp,
            p.block,
            p.energy,
            p.max_energy,
            p.gold,
            o.turn,
            len(o.hand),
        ]

        def cards(items, destination):
            if len(items) > len(destination):
                raise RuntimeError("Card encoding capacity exceeded")
            for i, c in enumerate(items):
                destination[i] = [
                    c.native_id,
                    int(c.upgraded),
                    c.cost,
                    c.printed_damage,
                    c.printed_block,
                    c.bonus_damage,
                    c.enchant_amount,
                ]

        cards(o.hand, result["hand"])
        for i, key in enumerate(("draw_pile", "discard_pile", "exhaust_pile")):
            cards(getattr(o, key), result["piles"][i])
        for i, key in enumerate(("known_top", "known_bottom")):
            cards(getattr(o, key), result["known_order"][i])
        enemy_types = {v: k for k, v in self.sim.names.enemies().items()}
        buff_types = {v: k for k, v in self.sim.names.buffs().items()}
        relic_types = {v: k for k, v in self.sim.names.relics().items()}
        if len(o.enemies) > 6 or len(o.relics) > 8:
            raise RuntimeError("Entity encoding capacity exceeded")
        for i, e in enumerate(o.enemies):
            result["enemies"][i, :4] = [
                enemy_types[e.type_id],
                e.hp,
                e.max_hp,
                e.block,
            ]
            if len(e.intents) > 2:
                raise RuntimeError("Intent encoding capacity exceeded")
            intent_ids = {
                name: value + 1 for value, name in self.sim.names.intents().items()
            }
            # Canonical distinction absent from the upstream five-kind enum.
            # Slime status-card counts are displayed by the real game.
            intent_ids["StatusCard"] = 6
            for j, intent in enumerate(e.intents):
                result["enemies"][i, 4 + j * 4 : 8 + j * 4] = [
                    intent_ids[intent.type],
                    intent.magnitude or 0,
                    intent.hits or 0,
                    int(intent.deals_damage),
                ]
            result["enemies"][i, 12] = 1
        for row, buffs in enumerate([p.powers] + [e.powers for e in o.enemies]):
            if len(buffs) > 16:
                raise RuntimeError("Power encoding capacity exceeded")
            for i, b in enumerate(buffs):
                result["powers"][row, i] = [buff_types[b.type_id], b.amount]
        for i, r in enumerate(o.relics):
            result["relics"][i] = [relic_types[r.type_id], r.counter]
        hand_refs = {c.ref: i for i, c in enumerate(o.hand)}
        enemy_refs = {e.ref: i for i, e in enumerate(o.enemies)}
        for i, a in enumerate(self.actions):
            result["actions"][i] = [
                1 if a.kind == "play_card" else 2,
                hand_refs.get(a.card_ref, -1),
                enemy_refs.get(a.target_ref, -1),
            ]
        return result

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        actual_seed = (
            int(self.np_random.integers(0, 2**31 - 1)) if seed is None else seed
        )
        self.close()
        self.attempts = 0
        self.done = False
        self.sim = Simulator(
            (options or {}).get("encounter", self.encounter), actual_seed
        )
        return self._encode(), {"encoding_version": ENCODING_VERSION}

    def step(self, action):
        if self.sim is None:
            raise RuntimeError("Call reset first")
        if self.done:
            raise RuntimeError("Episode ended; call reset")
        if not self.action_space.contains(action):
            raise ValueError("Action is outside the declared action space")
        self.attempts += 1
        if int(action) >= len(self.actions):
            # Gym checkers sample the whole Discrete space without consulting masks.
            # Invalid masked actions are explicit no-ops excluded from training data.
            self.done = self.attempts >= CONFIG["max_steps"]
            encoded = self._encode()
            if self.done:
                encoded["action_mask"][:] = 0
            return (
                encoded,
                0.0,
                False,
                self.done,
                {"invalid_action": True, "training_transition": False},
            )
        result = self.sim.step(
            self.actions[int(action)].action_id, self.sim.decision_id
        )
        truncated = result.truncated or (
            not result.terminated and self.attempts >= CONFIG["max_steps"]
        )
        self.done = result.terminated or truncated
        encoded = self._encode()
        if self.done:
            encoded["action_mask"][:] = 0
        return (
            encoded,
            result.reward,
            result.terminated,
            truncated,
            {"facts": result.facts, "reward_version": result.reward_version},
        )

    def action_masks(self):
        mask = np.zeros(MAX_ACTIONS, dtype=bool)
        if not self.done:
            mask[: len(self.actions)] = True
        return mask

    def close(self):
        if self.sim is not None:
            self.sim.close()
            self.sim = None
