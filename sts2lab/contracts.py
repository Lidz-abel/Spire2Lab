"""Versioned semantic contracts; backend metadata never enters policy observations."""

from __future__ import annotations

import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

PROTOCOL_VERSION = "0.2.0"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Power(StrictModel):
    type_id: str
    amount: int


class Player(StrictModel):
    hp: int
    max_hp: int
    block: int
    energy: int | None
    max_energy: int | None
    gold: int
    powers: list[Power]


class Card(StrictModel):
    # References identify one item in one decision, never a persistent hidden instance.
    ref: str = ""
    native_id: int
    type_id: str
    name: str
    card_type: str
    upgraded: bool
    target: str
    cost: int
    printed_damage: int
    printed_block: int
    bonus_damage: int = 0
    enchantment: str = "None"
    enchant_amount: int = 0
    free_this_turn: bool = False


class Intent(StrictModel):
    type: str
    deals_damage: bool
    magnitude: int | None
    hits: int | None


class Enemy(StrictModel):
    ref: str
    type_id: str
    name: str
    hp: int
    max_hp: int
    block: int
    powers: list[Power]
    intents: list[Intent]


class Relic(StrictModel):
    type_id: str
    name: str
    counter: int


class Action(StrictModel):
    action_id: str
    kind: Literal[
        "play_card", "end_turn", "select_card", "confirm_selection", "use_potion"
    ]
    card_ref: str | None = None
    target_ref: str | None = None
    label: str


class Observation(StrictModel):
    protocol_version: str = PROTOCOL_VERSION
    decision_id: str
    phase: Literal["combat", "card_selection", "terminal"]
    turn: int
    player: Player
    hand: list[Card]
    draw_pile: list[Card]
    discard_pile: list[Card]
    exhaust_pile: list[Card]
    known_top: list[Card]
    known_bottom: list[Card]
    enemies: list[Enemy]
    relics: list[Relic]
    legal_actions: list[Action]
    outcome: Literal["ongoing", "won", "lost", "truncated"] = "ongoing"
    # Empty containers for these paths mean unavailable, not known-empty. Primarily
    # used at the original game's reward screen after combat piles disappear.
    unavailable_fields: list[str] = Field(default_factory=list)


class Candidate(StrictModel):
    action_id: str
    score: float
    reasons: list[str]


class Decision(StrictModel):
    decision_id: str
    policy: str
    selected_action_id: str
    candidates: list[Candidate]
    elapsed_ms: float
    score_semantics: str = "heuristic_points"
    goal: str | None = None
    parent_decision_id: str | None = None


class StepResult(StrictModel):
    observation: Observation
    reward: float
    reward_version: str = "terminal-win-v1"
    terminated: bool
    truncated: bool
    facts: dict


class StepRequest(StrictModel):
    request_id: str = Field(min_length=1, max_length=128)
    decision_id: str
    action_id: str | None = None


def canonical_json(value) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def semantic_state(obs: Observation) -> dict:
    """Comparison projection: remove transport IDs, retain all gameplay fields."""
    d = obs.model_dump()
    d.pop("decision_id")
    for pile in (
        "hand",
        "draw_pile",
        "discard_pile",
        "exhaust_pile",
        "known_top",
        "known_bottom",
    ):
        for card in d[pile]:
            card.pop("ref")
    enemy_refs = {e["ref"]: index for index, e in enumerate(d["enemies"])}
    hand_refs = {c.ref: index for index, c in enumerate(obs.hand)}
    for enemy in d["enemies"]:
        enemy.pop("ref")
    for action in d["legal_actions"]:
        action.pop("action_id")
        action.pop("label")
        if action["card_ref"] is not None:
            action["card_ref"] = hand_refs.get(action["card_ref"], action["card_ref"])
        if action["target_ref"] is not None:
            action["target_ref"] = enemy_refs[action["target_ref"]]
    return d
