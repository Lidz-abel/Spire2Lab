"""Local NativeAOT adapter. All mechanics are executed by the pinned C# engine."""

from __future__ import annotations

import ctypes
from functools import lru_cache
import json
import os
from pathlib import Path
import sys
import threading
import uuid

from .contracts import (
    Action,
    Card,
    Enemy,
    Observation,
    Relic,
    StepResult,
    canonical_json,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/phase1.json").read_text())
LOCK = threading.RLock()  # Upstream native handle pools are not thread-safe.
_LOADED_LIBRARY_HASH = None


@lru_cache(maxsize=1)
def _verify_source(archive_sha256):
    from .source_integrity import verify_installed_source

    proof = verify_installed_source("sts2")
    if proof["archive_sha256"] != archive_sha256:
        raise RuntimeError(
            "Native build and pinned source archive differ; rebuild before use"
        )
    return proof


@lru_cache(maxsize=4)
def _binary_hash(path, mtime_ns, size):
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_native():
    global _LOADED_LIBRARY_HASH
    path = ROOT / ".tools/native"
    manifest = json.loads((path / "build.json").read_text())
    _verify_source(manifest["archive_sha256"])
    binary = path / "Sts2Emulator.so"
    stat = binary.stat()
    actual_hash = _binary_hash(str(binary), stat.st_mtime_ns, stat.st_size)
    if actual_hash != manifest["library_sha256"]:
        raise RuntimeError("Native library hash differs from its build manifest")
    if _LOADED_LIBRARY_HASH is not None and _LOADED_LIBRARY_HASH != actual_hash:
        raise RuntimeError("Native library rebuilt while loaded; restart this process")
    import hashlib

    for relative, expected in manifest["extension_sources"].items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
            raise RuntimeError(
                "Native extension source changed; run scripts/build_native.py"
            )
    os.environ["STS2_LIB_PATH"] = str(path)
    upstream = str(ROOT / "vendor/sts2/src")
    if upstream not in sys.path:
        sys.path.insert(0, upstream)
    from sts2_gym import native, names

    lib = native._lib
    lib.Sts2Lab_ApiVersion.restype = ctypes.c_int
    if lib.Sts2Lab_ApiVersion() != 1:
        raise RuntimeError("Unsupported native observation extension")
    lib.Sts2Lab_Observe.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_int,
    ]
    lib.Sts2Lab_Observe.restype = ctypes.c_int
    _LOADED_LIBRARY_HASH = actual_hash
    return native, names, manifest


class Simulator:
    backend = "native_simulator"
    capabilities = {
        "reset": True,
        "snapshot": True,
        "restore": True,
        "sample_hidden": True,
        "original_pixels": False,
    }

    def __init__(self, encounter="nibbits-weak", seed=1):
        if encounter not in CONFIG["encounters"]:
            raise ValueError("Encounter is outside the phase-one support inventory")
        if not 0 <= seed < 2**31:
            raise ValueError("Seed must be in [0, 2**31)")
        with LOCK:
            self.native, self.names, self.manifest = load_native()
            from sts2_gym.env import ENCOUNTER_IDS

            self.encounter = encounter
            self.seed = seed
            self.handle = self.native.create(seed)
            if self.handle < 0:
                raise RuntimeError("Native handle capacity exhausted")
            self.buf = (ctypes.c_int * self.native.OBS_SIZE)()
            self.reward_buf = (ctypes.c_float * 1)()
            self.sequence = 0
            self.epoch = uuid.uuid4().hex
            self.terminated = False
            self.truncated = False
            self.native.reset_arena(
                self.handle,
                CONFIG["deck"],
                self.buf,
                encounter_id=ENCOUNTER_IDS[encounter],
                relic_ids=CONFIG["relics"],
                potion_ids=CONFIG["potions"],
                player_hp=CONFIG["hp"],
                player_max_hp=CONFIG["max_hp"],
                player_gold=CONFIG["gold"],
                ascension=CONFIG["ascension"],
                total_floor=CONFIG["floor"],
                completed_combat_rooms=CONFIG["completed_combats"],
            )

    @property
    def decision_id(self):
        return f"{self.epoch}:{self.sequence}"

    def _raw(self, *, debug=False):
        if self.handle < 0:
            raise RuntimeError("Environment is closed")
        size = self.native._lib.Sts2Lab_Observe(self.handle, int(debug), None, 0)
        if not 0 < size <= 4_000_000:
            raise RuntimeError(f"Observation export failed: {size}")
        buf = (ctypes.c_ubyte * size)()
        result = self.native._lib.Sts2Lab_Observe(self.handle, int(debug), buf, size)
        if result != size:
            raise RuntimeError("State changed during observation serialization")
        return json.loads(bytes(buf))

    def observe(self):
        with LOCK:
            raw = self._raw()
            raw["player"]["powers"].sort(key=lambda p: p["type_id"])
            for enemy in raw["enemies"]:
                enemy["powers"].sort(key=lambda p: p["type_id"])
            for pile in ("draw_pile", "discard_pile", "exhaust_pile"):
                raw[pile].sort(key=canonical_json)
            prefix = self.decision_id
            hand = [
                Card(**c, ref=f"{prefix}:card:{i}") for i, c in enumerate(raw["hand"])
            ]
            enemies = []
            enemy_slots = {}
            for e in raw["enemies"]:
                data = dict(e)
                data["intents"] = [
                    (
                        i
                        if i["deals_damage"]
                        else (
                            {**i, "type": "StatusCard", "hits": None}
                            if i["type"] == "Debuff"
                            and self.names.enemies()[e["native_id"]]
                            in {"LeafSlimeS", "LeafSlimeM", "TwigSlimeM"}
                            else {**i, "magnitude": None, "hits": None}
                        )
                    )
                    for i in e["intents"]
                ]
                slot = data.pop("slot")
                eid = data.pop("native_id")
                ref = f"{prefix}:enemy:{slot}"
                enemy_slots[ref] = slot
                enemies.append(
                    Enemy(
                        **data,
                        ref=ref,
                        type_id=self.names.enemies()[eid],
                        name=self.names.enemy_name(eid),
                    )
                )
            self._action_map = {}
            legal = []
            if not self.terminated and not self.truncated:
                if raw["phase"] != "combat":
                    raise RuntimeError(
                        "Card selection is outside the current benchmark; expand contract before executing"
                    )
                for index in raw["legal_indices"]:
                    if index < len(hand):
                        card = hand[index]
                        targets = enemies if card.target == "AnyEnemy" else [None]
                        for enemy in targets:
                            aid = f"play:{index}:{enemy_slots[enemy.ref] if enemy else '-'}"
                            legal.append(
                                Action(
                                    action_id=aid,
                                    kind="play_card",
                                    card_ref=card.ref,
                                    target_ref=enemy.ref if enemy else None,
                                    label=(
                                        f"{card.name} → {enemy.name}"
                                        if enemy
                                        else card.name
                                    ),
                                )
                            )
                            self._action_map[aid] = (
                                index,
                                enemy_slots[enemy.ref] if enemy else -1,
                            )
                    elif index == len(hand):
                        legal.append(
                            Action(
                                action_id="end_turn", kind="end_turn", label="结束回合"
                            )
                        )
                        self._action_map["end_turn"] = (index, -1)
                    else:
                        raise RuntimeError(
                            "Potion action outside the phase-one empty-potion benchmark"
                        )
            outcome = (
                "truncated"
                if self.truncated
                else (
                    ("won" if self.native.player_won(self.handle) else "lost")
                    if self.terminated
                    else "ongoing"
                )
            )
            return Observation(
                decision_id=prefix,
                phase="terminal" if self.terminated or self.truncated else raw["phase"],
                turn=raw["turn"],
                player=raw["player"],
                hand=hand,
                enemies=enemies,
                **{
                    key: raw[key]
                    for key in (
                        "draw_pile",
                        "discard_pile",
                        "exhaust_pile",
                        "known_top",
                        "known_bottom",
                    )
                },
                relics=[
                    Relic(
                        type_id=self.names.relics()[r["native_id"]],
                        name=self.names.relic_name(r["native_id"]),
                        counter=r["counter"],
                    )
                    for r in raw["relics"]
                ],
                legal_actions=legal,
                outcome=outcome,
            )

    def step(self, action_id, decision_id):
        with LOCK:
            before = self.observe()
            if decision_id != before.decision_id:
                raise ValueError("stale_decision: state has advanced")
            if action_id not in self._action_map:
                raise ValueError(
                    "illegal_action: action is unavailable in this decision"
                )
            action, target = self._action_map[action_id]
            self.terminated = self.native.step(
                self.handle, action, self.buf, self.reward_buf, target
            )
            self.sequence += 1
            self.truncated = (
                not self.terminated and self.sequence >= CONFIG["max_steps"]
            )
            after = self.observe()
            return StepResult(
                observation=after,
                reward=(
                    1.0
                    if after.outcome == "won"
                    else -1.0 if after.outcome == "lost" else 0.0
                ),
                terminated=self.terminated,
                truncated=self.truncated,
                facts={
                    "player_hp_delta": after.player.hp - before.player.hp,
                    "turn_delta": after.turn - before.turn,
                    "outcome": after.outcome,
                    "manual_intervention": False,
                },
            )

    def _fork(self, *, resample_seed=None):
        with LOCK:
            copy = object.__new__(Simulator)
            for key in (
                "native",
                "names",
                "manifest",
                "encounter",
                "seed",
                "sequence",
                "terminated",
                "truncated",
            ):
                setattr(copy, key, getattr(self, key))
            copy.epoch = uuid.uuid4().hex
            copy.buf = (ctypes.c_int * self.native.OBS_SIZE)()
            copy.reward_buf = (ctypes.c_float * 1)()
            copy.handle = self.native.clone(
                self.handle, resample_seed is not None, resample_seed or 0, copy.buf
            )
            if copy.handle < 0:
                raise RuntimeError("Native handle capacity exhausted")
            return copy

    def snapshot(self):
        """Exact in-process checkpoint for replay/debug; caller must close it."""
        return self._fork()

    def sample_world(self, search_seed):
        """Search entry point. Always resamples the hidden state."""
        if not 0 <= search_seed < 2**31:
            raise ValueError("Search seed must be in [0, 2**31)")
        return self._fork(resample_seed=search_seed)

    def restore(self, snapshot):
        with LOCK:
            if snapshot.encounter != self.encounter or snapshot.seed != self.seed:
                raise ValueError("Checkpoint belongs to another scenario")
            replacement = snapshot._fork()
            self.close()
            self.__dict__.update(replacement.__dict__)
            replacement.handle = -1
            return self.observe()

    def close(self):
        with LOCK:
            if self.handle >= 0:
                self.native.destroy(self.handle)
                self.handle = -1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
