"""Original-game adapter using player-visible fields and the shared semantic protocol.

Static printed card numbers are explicitly from the pinned public rules catalog;
cross-backend verification must not count those as independent live evidence.
"""

from __future__ import annotations

from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import uuid

from .bridge import BridgeClient, BridgeError, OutcomeUnknown
from .catalog import catalog
from .contracts import (
    Action,
    Card,
    Enemy,
    Intent,
    Observation,
    Player,
    Power,
    Relic,
    StepResult,
    canonical_json,
)
from .simulator import CONFIG, ROOT

CARD_ENTRIES = {"STRIKE_IRONCLAD": 5, "DEFEND_IRONCLAD": 4, "BASH": 1}
ENEMY_ENTRIES = {
    "nibbits-weak": {"NIBBIT"},
    "slimes-weak": {"LEAF_SLIME_M", "LEAF_SLIME_S", "TWIG_SLIME_M", "TWIG_SLIME_S"},
    "sludge-spinner": {"SLUDGE_SPINNER"},
}
TERMINAL_MISSING = [
    "turn",
    "hand",
    "draw_pile",
    "discard_pile",
    "exhaust_pile",
    "known_top",
    "known_bottom",
    "enemies",
    "player.energy",
    "player.max_energy",
]


class UnsupportedState(BridgeError):
    pass


def required(obj, key):
    if key not in obj or obj[key] is None:
        raise UnsupportedState(f"Original-game state is missing required field: {key}")
    return obj[key]


def integral(value, field):
    if isinstance(value, bool):
        raise UnsupportedState(f"Expected integer {field}, got boolean")
    if isinstance(value, (int, float)) and int(value) == value:
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    raise UnsupportedState(f"Unrecognized integer {field}: {value!r}")


def parse_intent(raw):
    kind = required(raw, "type")
    if kind == "StatusCard":
        count = integral(required(raw, "label"), "intent.status_card_count")
        if count < 0:
            raise UnsupportedState("Negative status-card intent count")
        return Intent(type="StatusCard", deals_damage=False, magnitude=count, hits=None)
    if kind in {"Attack", "AttackBuff", "AttackDebuff", "AttackDefend"}:
        # The current support set emits separate Attack + Buff/Defend entries. Refuse
        # combined representations until the interface is extended explicitly.
        if kind != "Attack":
            raise UnsupportedState(f"Unsupported combined intent: {kind}")
        label = str(required(raw, "label")).strip()
        match = re.fullmatch(r"(\d+)\s*(?:[xX×]\s*(\d+))?", label)
        if not match:
            raise UnsupportedState(f"Cannot read original attack label: {label!r}")
        damage, hits = int(match[1]), int(match[2] or 1)
        return Intent(
            type="Attack", deals_damage=True, magnitude=damage * hits, hits=hits
        )
    if kind not in {"Defend", "Buff", "Debuff", "Unknown"}:
        raise UnsupportedState(f"Unsupported intent type: {kind}")
    return Intent(type=kind, deals_damage=False, magnitude=None, hits=None)


def power_list(items):
    mapping = catalog()["powers"]
    result = []
    for item in items:
        entry = required(item, "id")
        if entry not in mapping:
            raise UnsupportedState(f"Unknown power identity: {entry}")
        result.append(
            Power(
                type_id=mapping[entry],
                amount=integral(required(item, "amount"), "power.amount"),
            )
        )
    return sorted(result, key=lambda p: p.type_id)


def read_card(raw, ref=""):
    entry = required(raw, "id")
    definition = catalog()["cards"].get(entry)
    if definition is None:
        raise UnsupportedState(f"Unknown card identity: {entry}")
    # No arbitrary upgrades/enchantments/deck changes enter the fixed benchmark.
    if entry not in CARD_ENTRIES and entry != "SLIMED":
        raise UnsupportedState(f"Card outside the starter benchmark: {entry}")
    if raw.get("is_upgraded") is not False:
        raise UnsupportedState(
            "Upgraded or unspecified card upgrade state outside starter benchmark"
        )
    if required(raw, "lab_has_enchantment") is not False:
        raise UnsupportedState("Enchanted card outside starter benchmark")
    cost = integral(required(raw, "cost"), "card.cost")
    return Card(
        ref=ref,
        native_id=definition.card_id,
        type_id=entry,
        name=definition.name,
        card_type=definition.card_type,
        upgraded=False,
        target=definition.target,
        cost=cost,
        printed_damage=definition.base_damage,
        printed_block=definition.base_block,
    )


def normalize_original(raw, decision_id, *, previous=None):
    """Returns a policy-safe observation and private semantic-to-Mod action mapping."""
    player = required(raw, "player")
    screen = required(raw, "state_type")
    terminal = screen in {"rewards", "card_reward", "game_over"}
    if screen not in {"monster", "rewards", "card_reward", "game_over"}:
        raise UnsupportedState(f"Screen outside the combat benchmark: {screen}")
    hp = integral(required(player, "hp"), "hp")
    if terminal and previous is None:
        raise UnsupportedState(
            "Attach at a live combat decision, not at a reward or game-over screen"
        )
    if screen == "game_over" and hp > 0:
        raise UnsupportedState(
            "Game-over with surviving player has no established combat outcome"
        )
    observation_player = Player(
        hp=hp,
        max_hp=integral(required(player, "max_hp"), "max_hp"),
        block=integral(required(player, "block"), "block"),
        gold=integral(required(player, "gold"), "gold"),
        energy=None if terminal else integral(required(player, "energy"), "energy"),
        max_energy=(
            None if terminal else integral(required(player, "max_energy"), "max_energy")
        ),
        powers=power_list(required(player, "status")),
    )
    relics = []
    for relic in required(player, "relics"):
        entry = required(relic, "id")
        if entry != "BURNING_BLOOD":
            raise UnsupportedState(f"Relic outside starter benchmark: {entry}")
        canonical = catalog()["relics"][entry]
        relics.append(
            Relic(
                type_id=canonical,
                name="Burning Blood",
                counter=integral(relic.get("counter") or 0, "relic.counter"),
            )
        )
    if len(relics) != 1:
        raise UnsupportedState("Starter relic is missing or duplicated")
    if terminal:
        return (
            Observation(
                decision_id=decision_id,
                phase="terminal",
                turn=previous.turn,
                player=observation_player,
                relics=relics,
                hand=[],
                draw_pile=[],
                discard_pile=[],
                exhaust_pile=[],
                known_top=[],
                known_bottom=[],
                enemies=[],
                legal_actions=[],
                outcome="lost" if hp <= 0 else "won",
                unavailable_fields=TERMINAL_MISSING,
            ),
            {},
        )
    battle = required(raw, "battle")
    if battle.get("is_play_phase") is not True or not raw.get("lab_action_ready"):
        raise UnsupportedState("Original game is not at a settled player decision")
    hand_raw = required(player, "hand")
    hand = []
    for index, card in enumerate(hand_raw):
        if integral(required(card, "index"), "card.index") != index:
            raise UnsupportedState("Original hand indices are inconsistent")
        hand.append(read_card(card, f"{decision_id}:card:{index}"))
    piles = {}
    for key in ("draw_pile", "discard_pile", "exhaust_pile"):
        cards = [read_card(c) for c in required(player, key)]
        if len(cards) != integral(required(player, key + "_count"), key + "_count"):
            raise UnsupportedState(f"Incomplete original pile data: {key}")
        # Even if the Mod changes ordering, nothing but the multiset crosses this boundary.
        piles[key] = sorted(cards, key=lambda c: canonical_json(c))
    enemies = []
    targets = {}
    for index, enemy in enumerate(required(battle, "enemies")):
        entity = required(enemy, "entity_id")
        entry = entity.rsplit("_", 1)[0]
        if entry not in catalog()["enemies"]:
            raise UnsupportedState(f"Unknown enemy identity: {entry}")
        canonical = catalog()["enemies"][entry]
        ref = f"{decision_id}:enemy:{index}"
        targets[ref] = entity
        enemies.append(
            Enemy(
                ref=ref,
                type_id=canonical,
                name=catalog()["enemy_names"][entry],
                hp=integral(required(enemy, "hp"), "enemy.hp"),
                max_hp=integral(required(enemy, "max_hp"), "enemy.max_hp"),
                block=integral(required(enemy, "block"), "enemy.block"),
                powers=power_list(required(enemy, "status")),
                intents=[parse_intent(i) for i in required(enemy, "intents")],
            )
        )
    legal, mapping = [], {}
    for index, (card, item) in enumerate(zip(hand, hand_raw)):
        if item.get("can_play") is False:
            continue
        if item.get("can_play") is not True:
            raise UnsupportedState("Missing authoritative card playability")
        if required(item, "target_type") != card.target:
            raise UnsupportedState(
                "Card target type differs from the pinned rules catalog"
            )
        for enemy in enemies if card.target == "AnyEnemy" else [None]:
            target_index = enemies.index(enemy) if enemy else "-"
            aid = f"play:{index}:{target_index}"
            legal.append(
                Action(
                    action_id=aid,
                    kind="play_card",
                    card_ref=card.ref,
                    target_ref=enemy.ref if enemy else None,
                    label=f"{card.name} → {enemy.name}" if enemy else card.name,
                )
            )
            mapping[aid] = {"action": "play_card", "card_index": index}
            if enemy:
                mapping[aid]["target"] = targets[enemy.ref]
    legal.append(Action(action_id="end_turn", kind="end_turn", label="结束回合"))
    mapping["end_turn"] = {"action": "end_turn"}
    # Starter cards cannot reveal or set draw order. Enabling other content requires an
    # explicit knowledge tracker; true ordered piles from the Mod are never used here.
    return (
        Observation(
            decision_id=decision_id,
            phase="combat",
            turn=integral(required(battle, "round"), "round") - 1,
            player=observation_player,
            hand=hand,
            **piles,
            known_top=[],
            known_bottom=[],
            enemies=enemies,
            relics=relics,
            legal_actions=legal,
        ),
        mapping,
    )


def verify_scope(raw, encounter, *, opening):
    if encounter not in CONFIG["encounters"]:
        raise UnsupportedState("Encounter outside declared benchmark")
    player = required(raw, "player")
    run = required(raw, "run")
    if required(player, "lab_character_id") != "IRONCLAD":
        raise UnsupportedState("Original character differs from Ironclad")
    if integral(required(run, "ascension"), "ascension") != CONFIG["ascension"]:
        raise UnsupportedState("Original ascension differs from the benchmark")
    deck = required(player, "deck")
    if Counter(c.get("id") for c in deck) != Counter(CARD_ENTRIES):
        raise UnsupportedState("Original permanent deck differs from the starter deck")
    if any(c.get("is_upgraded") is not False for c in deck):
        raise UnsupportedState("Original deck has upgraded or unspecified cards")
    if any(c.get("lab_has_enchantment") is not False for c in deck):
        raise UnsupportedState("Original deck has enchanted or unverified cards")
    if required(player, "potions"):
        raise UnsupportedState("Benchmark requires empty potion slots")
    if opening:
        expected = {
            "hp": CONFIG["hp"],
            "max_hp": CONFIG["max_hp"],
            "gold": CONFIG["gold"],
            "block": 0,
            "energy": 3,
            "max_energy": 3,
            "draw_pile_count": 5,
            "discard_pile_count": 0,
            "exhaust_pile_count": 0,
        }
        for key, value in expected.items():
            if integral(required(player, key), key) != value:
                raise UnsupportedState(
                    f"Original opening {key} does not match benchmark {value}"
                )
        if len(required(player, "hand")) != 5 or required(player, "status"):
            raise UnsupportedState(
                "Original opening hand or powers differ from the benchmark"
            )
        for enemy in required(raw["battle"], "enemies"):
            if (
                required(enemy, "hp") != required(enemy, "max_hp")
                or required(enemy, "block") != 0
            ):
                raise UnsupportedState(
                    "Reference enemy has already taken damage or gained block"
                )
        if integral(required(run, "floor"), "floor") != CONFIG["floor"]:
            raise UnsupportedState("Original opening floor differs from the benchmark")
        if integral(required(raw["battle"], "round"), "round") != 1:
            raise UnsupportedState(
                "Reference combat must be attached at its opening decision"
            )
        entries = [
            e["entity_id"].rsplit("_", 1)[0] for e in required(raw["battle"], "enemies")
        ]
        if not entries or not set(entries) <= ENEMY_ENTRIES[encounter]:
            raise UnsupportedState("Enemy roster does not match the selected encounter")
        if encounter == "slimes-weak":
            valid = (
                len(entries) == 3
                and {entries[0], entries[2]} == {"LEAF_SLIME_S", "TWIG_SLIME_S"}
                and entries[1] in {"LEAF_SLIME_M", "TWIG_SLIME_M"}
            )
        else:
            valid = len(entries) == 1
        if not valid:
            raise UnsupportedState(
                "Enemy count or slot order differs from the selected encounter"
            )


class OriginalEnvironment:
    backend = "original_game"
    capabilities = {
        "reset": False,
        "snapshot": False,
        "restore": False,
        "sample_hidden": False,
        "original_pixels": False,
        "native_game_window": True,
    }

    def __init__(self, client, encounter, manifest, *, raw_dir=None):
        self.client, self.encounter, self.manifest = client, encounter, manifest
        self.sequence, self.seed = 0, None
        self.epoch = uuid.uuid4().hex
        self.raw_dir = (
            Path(raw_dir) if raw_dir else ROOT / "artifacts/original-raw" / self.epoch
        )
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.pending_before = None

    @classmethod
    async def attach(cls, encounter, *, client=None, manifest=None, raw_dir=None):
        if manifest is None:
            path = ROOT / "artifacts/windows/mod/build.json"
            if not path.exists():
                raise BridgeError(
                    "Windows DLLs and compiled bridge are missing; run Connect-Windows.ps1 first"
                )
            manifest = json.loads(path.read_text())
        instance = cls(
            client or BridgeClient(manifest["game_assembly_sha256"]),
            encounter,
            manifest,
            raw_dir=raw_dir,
        )
        try:
            raw = await instance.client.wait_ready()
            instance._record_raw(raw, "opening")
            verify_scope(raw, encounter, opening=True)
            instance._install(raw)
            return instance
        except BaseException:
            await instance.close()
            raise

    def _record_raw(self, raw, label):
        path = self.raw_dir / f"{self.sequence:04d}-{label}-{uuid.uuid4().hex[:8]}.json"
        content = (canonical_json(raw) + "\n").encode()
        path.write_bytes(content)
        self.last_capture = {
            "file": path.name,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    def _install(self, raw):
        self.raw = copy.deepcopy(raw)
        self.observation, self.action_map = normalize_original(
            raw,
            f"{self.epoch}:{self.sequence}",
            previous=getattr(self, "observation", None),
        )

    def observe(self):
        return self.observation

    async def step(self, action_id, decision_id, *, request_id=None):
        if decision_id != self.observation.decision_id:
            raise ValueError("stale_decision")
        if action_id not in self.action_map:
            raise ValueError("illegal_action")
        if self.pending_before is not None:
            raise OutcomeUnknown("Resolve previous original-game command first")
        self.pending_before = self.observation
        try:
            raw = await self.client.submit(
                self.action_map[action_id],
                self.raw["lab_state_token"],
                request_id=request_id,
            )
        except OutcomeUnknown:
            raise
        except BaseException:
            if self.client.pending is None:
                self.pending_before = None
            raise
        return self._finish(raw)

    def _finish(self, raw):
        before = self.pending_before
        self.sequence += 1
        self._record_raw(raw, "after")
        verify_scope(raw, self.encounter, opening=False)
        self._install(raw)
        self.pending_before = None
        obs = self.observation
        terminated = obs.outcome in ("won", "lost")
        truncated = not terminated and self.sequence >= CONFIG["max_steps"]
        if truncated:
            obs = obs.model_copy(
                update={
                    "phase": "terminal",
                    "outcome": "truncated",
                    "legal_actions": [],
                }
            )
            self.observation = obs
        return StepResult(
            observation=obs,
            reward=(
                1.0 if obs.outcome == "won" else -1.0 if obs.outcome == "lost" else 0.0
            ),
            terminated=terminated,
            truncated=truncated,
            facts={
                "player_hp_delta": obs.player.hp - before.player.hp,
                "turn_delta": (
                    None if "turn" in obs.unavailable_fields else obs.turn - before.turn
                ),
                "outcome": obs.outcome,
                "manual_intervention": False,
                "original_capture": self.last_capture,
            },
        )

    async def reconcile(self):
        if self.pending_before is None:
            raise BridgeError("No unresolved original-game command")
        return self._finish(await self.client.reconcile())

    async def close(self):
        await self.client.close()
