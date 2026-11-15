"""Single-act public observations. Privileged bridge data never goes to a policy."""

from __future__ import annotations

from typing import Literal
from pydantic import Field

from .contracts import StrictModel


class ActAction(StrictModel):
    action_id: str
    kind: str
    label: str
    index: int | None = None
    target: str | None = None


class ActObservation(StrictModel):
    protocol_version: Literal["single-act-v1"] = "single-act-v1"
    decision_id: str
    act: int = Field(ge=1)
    floor: int = Field(ge=0)
    phase: str
    player: dict
    screen: dict
    battle: dict | None = None
    legal_actions: tuple[ActAction, ...]
    outcome: Literal["ongoing", "act_complete", "lost"]
    unsupported_reason: str | None = None
    unavailable_fields: tuple[str, ...] = (
        "seed",
        "rng_state",
        "hidden_draw_order",
        "hidden_event_outcomes",
        "simulator_parity_outside_starter_scope",
        "selection_bounds_if_not_reported",
    )


def pick(obj, fields):
    """Copy only declared scalar display fields; reject containers in scalar slots."""
    if not isinstance(obj, dict):
        raise ValueError("Public object is missing")
    result = {}
    for key in fields.split():
        if key in obj:
            value = obj[key]
            if value is not None and type(value) not in (str, int, float, bool):
                raise ValueError(f"Invalid public scalar: {key}")
            result[key] = value
    return result


CARD_FIELDS = "id name type cost star_cost description rarity is_upgraded index can_play target_type lab_selectable lab_selected"
ITEM_FIELDS = "index type description gold_amount potion_id potion_name potion_description category price is_stocked can_afford on_sale card_id card_name card_type card_cost card_rarity card_description relic_id relic_name relic_description"
RELIC_FIELDS = "index id name description rarity counter"
ACTION_KINDS = {
    "choose_map_node",
    "claim_reward",
    "select_card_reward",
    "skip_card_reward",
    "choose_rest_option",
    "shop_purchase",
    "lab_open_shop",
    "lab_close_shop",
    "proceed",
    "choose_event_option",
    "advance_dialogue",
    "lab_open_chest",
    "claim_treasure_relic",
    "select_card",
    "combat_select_card",
    "confirm_selection",
    "combat_confirm_selection",
    "cancel_selection",
    "play_card",
    "end_turn",
    "use_potion",
}


def rows(obj, key, fields):
    if not isinstance(obj.get(key, []), list):
        raise ValueError(f"Invalid public list: {key}")
    return [pick(row, fields) for row in obj.get(key, [])]


def node(raw):
    result = pick(raw, "col row type index id name")
    if "children" in raw:
        children = raw["children"]
        if not isinstance(children, list) or any(
            not isinstance(child, list)
            or len(child) != 2
            or any(type(v) is not int for v in child)
            for child in children
        ):
            raise ValueError("Invalid map edges")
        result["children"] = [list(child) for child in children]
    if "leads_to" in raw:
        result["leads_to"] = [pick(v, "col row type") for v in raw["leads_to"]]
    return result


def normalize_act(raw, decision_id):
    """Explicit whitelist projection plus a private decision-local command map."""
    meta = raw.get("lab_act", {})
    if (
        meta.get("version") != "single-act-v1"
        or meta.get("status") != "active"
        or meta.get("initializer") != "normal_seeded_non_saving"
        or meta.get("should_save") is not False
        or raw.get("lab_profile_id") != 2
    ):
        raise ValueError("Not an active non-saving experimental act")
    phase, source = raw["state_type"], raw["player"]
    if source.get("lab_character_id") != "IRONCLAD" or raw["run"]["ascension"] != 0:
        raise ValueError("Only Ironclad A0 is supported")
    for key in ("hp", "max_hp", "gold", "deck", "relics", "potions"):
        if key not in source:
            raise ValueError(f"Required public player field missing: {key}")
    player = pick(
        source,
        "hp max_hp block energy max_energy gold max_potion_slots lab_character_id draw_pile_count discard_pile_count exhaust_pile_count",
    )
    for key in ("deck", "hand", "draw_pile", "discard_pile", "exhaust_pile"):
        player[key] = rows(source, key, CARD_FIELDS)
    # Draw membership is inspectable, but its iteration order is never policy input.
    player["draw_pile"].sort(
        key=lambda c: (c.get("id", ""), c.get("is_upgraded", False))
    )
    player["relics"] = rows(source, "relics", RELIC_FIELDS)
    player["potions"] = rows(
        source,
        "potions",
        "id name description slot target_type can_use_in_combat lab_can_use",
    )
    player["status"] = rows(source, "status", "id name amount description")
    battle = None
    if isinstance(raw.get("battle"), dict):
        battle = pick(raw["battle"], "round turn is_play_phase")
        battle["enemies"] = []
        for enemy in raw["battle"].get("enemies", []):
            public = pick(enemy, "entity_id name hp max_hp block")
            public["status"] = rows(enemy, "status", "id name amount description")
            public["intents"] = rows(enemy, "intents", "type label title description")
            battle["enemies"].append(public)
    screen, unsupported = {}, None
    if phase == "map":
        src = raw["map"]
        for key in ("nodes", "visited", "next_options"):
            screen[key] = [node(v) for v in src[key]]
        for key in ("current_position", "boss"):
            if key in src:
                screen[key] = node(src[key])
    elif phase in ("card_reward", "card_select", "hand_select"):
        src = raw[phase]
        screen = pick(
            src,
            "screen_type mode prompt preview_showing can_confirm can_cancel can_skip",
        )
        screen["cards"] = rows(src, "cards", CARD_FIELDS)
        screen["preview_cards"] = rows(src, "preview_cards", CARD_FIELDS)
        screen["selected_cards"] = rows(src, "selected_cards", "index name")
        if phase == "card_select" and screen.get("screen_type") not in (
            "transform",
            "upgrade",
            "select",
            "simple_select",
            "choose",
        ):
            unsupported = "Unsupported card selection screen"
        if phase == "hand_select" and screen.get("mode") not in (
            "simple_select",
            "upgrade_select",
        ):
            unsupported = "Unsupported hand selection mode"
    elif phase in ("rewards", "shop"):
        src = raw[phase]
        screen = pick(src, "can_proceed lab_can_open lab_can_close lab_inventory_open")
        screen["items"] = rows(src, "items", ITEM_FIELDS)
    elif phase == "rest_site":
        screen = pick(raw[phase], "can_proceed")
        screen["options"] = rows(
            raw[phase], "options", "index id name description is_enabled"
        )
    elif phase == "event":
        src = raw[phase]
        screen = pick(src, "event_id event_name is_ancient in_dialogue body")
        screen["options"] = rows(
            src,
            "options",
            "index title description is_locked is_proceed was_chosen lab_enabled relic_name relic_description",
        )
    elif phase == "treasure":
        screen = pick(raw[phase], "can_proceed lab_can_open message")
        screen["relics"] = rows(raw[phase], "relics", RELIC_FIELDS)
    elif phase not in ("monster", "elite", "boss", "game_over"):
        unsupported = f"Unsupported screen: {phase}"
    actions, mapping = [], {}
    # These are bridge-advertised guarded commands; no arbitrary raw endpoint call.
    for index, choice in enumerate(raw.get("lab_act_choices", [])):
        command = choice["Command"]
        kind = choice["Kind"]
        if kind not in ACTION_KINDS:
            raise ValueError("Unsupported guarded action kind")
        if command.get("action") != kind or set(command) - {
            "action",
            "index",
            "card_index",
            "slot",
            "target",
        }:
            raise ValueError("Malformed guarded choice")
        action_id = f"a{index}"
        actions.append(
            ActAction(
                action_id=action_id,
                kind=kind,
                label=choice["Label"],
                index=command.get(
                    "index", command.get("card_index", command.get("slot"))
                ),
                target=command.get("target"),
            )
        )
        mapping[action_id] = choice["Id"]
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Duplicate guarded choices")
    outcome = meta["outcome"]
    if outcome == "act_complete" and not meta.get("boss_seen"):
        raise ValueError("Act completion without observed boss")
    if outcome == "lost" and player["hp"] > 0:
        raise ValueError("Loss without observed death")
    if outcome != "ongoing" and actions:
        raise ValueError("Terminal state advertises gameplay")
    if not actions and outcome == "ongoing":
        unsupported = unsupported or f"No supported decision in {phase}"
    if unsupported:
        actions, mapping = [], {}
    return (
        ActObservation(
            decision_id=decision_id,
            act=raw["run"]["act"],
            floor=raw["run"]["floor"],
            phase=phase,
            player=player,
            screen=screen,
            battle=battle,
            legal_actions=tuple(actions),
            outcome=outcome,
            unsupported_reason=unsupported,
        ),
        mapping,
    )


def check_continuity(before, after, action):
    if (
        after.floor < before.floor
        or after.act < before.act
        or after.act > before.act + 1
    ):
        raise ValueError("Run position regressed or skipped an act")
    if action.kind == "choose_map_node":
        selected = next(
            n for n in before.screen["next_options"] if n["index"] == action.index
        )
        # Rooms may have internal transitions; the first map after the visit must
        # confirm the chosen coordinate via the controller's route ledger.
        if selected["row"] < before.screen.get("current_position", {}).get("row", -1):
            raise ValueError("Map action moves backwards")
    elif after.floor > before.floor and action.kind not in (
        "proceed",
        "choose_event_option",
        "advance_dialogue",
    ):
        raise ValueError("Unexpected floor change")
