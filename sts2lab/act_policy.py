"""Public-screen heuristic baseline for normal act traversal; no forward model.

Numeric text estimates rank choices only. The game decides legality and effects.
This is explicitly not a trained policy or a full-act search implementation.
"""

import re
import time


def visible_amount(text):
    numbers = [int(v) for v in re.findall(r"\d+", str(text))]
    if not numbers:
        return 0
    if len(numbers) > 1 and any(mark in str(text) for mark in ("×", "x", "*")):
        return numbers[0] * numbers[1]
    return numbers[0]


class ActPolicy:
    version = "public-act-heuristic-v1"

    def __init__(self):
        self.goal = None
        self.goal_sequence = 0
        self.visited_shop = False
        self.used_rest = False
        self.closed_shop_floors = set()

    def observe_transition(self, before, action, after):
        if action.kind == "shop_purchase":
            self.visited_shop = True
        if action.kind == "choose_rest_option":
            self.used_rest = True
        if action.kind == "lab_close_shop":
            self.closed_shop_floors.add((before.act, before.floor))

    def _goal_name(self, obs):
        if obs.phase in ("monster", "elite", "boss", "hand_select"):
            return "preserve_hp_in_combat"
        if obs.phase == "rest_site":
            return "recover_or_upgrade"
        if obs.phase in ("shop", "card_reward", "card_select", "rewards", "treasure"):
            return "improve_inventory"
        return "advance_first_act"

    def decide(self, obs, *, interrupted=False):
        started = time.perf_counter()
        if obs.unsupported_reason or not obs.legal_actions:
            return None
        name = self._goal_name(obs)
        boundary = (obs.act, obs.floor, name)
        ended = None
        if self.goal and (self.goal["boundary"] != list(boundary) or interrupted):
            ended = {
                **self.goal,
                "termination_reason": (
                    "manual_override" if interrupted else "room_or_goal_changed"
                ),
            }
            self.goal = None
        if self.goal is None:
            self.goal_sequence += 1
            self.goal = {
                "goal_id": f"g{self.goal_sequence}",
                "name": name,
                "parent_decision_id": obs.decision_id,
                "boundary": list(boundary),
            }
        candidates = []
        for action in obs.legal_actions:
            score, reason = self.score(obs, action)
            candidates.append(
                {
                    "action_id": action.action_id,
                    "score": round(score, 6),
                    "reason": reason,
                }
            )
        best = max(candidates, key=lambda c: c["score"])
        return {
            "policy": self.version,
            "selected_action_id": best["action_id"],
            "candidates": candidates,
            "goal": dict(self.goal),
            "ended_goal": ended,
            "score_semantics": "fixed public-screen heuristic utility; not win probability",
            "planning_mode": "heuristic",
            "model_calls": 0,
            "search_unavailable_reason": "normal_run_inventory_and_encounters_not_certified_by_starter_model",
            "elapsed_ms": (time.perf_counter() - started) * 1000,
        }

    def _route_score(self, obs, selected):
        nodes = {(n["col"], n["row"]): n for n in obs.screen["nodes"]}
        hp = obs.player["hp"] / obs.player["max_hp"]

        def value(n):
            kind = n.get("type", "").lower()
            return {
                "restsite": 8 if hp < 0.7 else (4 if not self.used_rest else 1),
                "shop": 9 if not self.visited_shop and obs.player["gold"] >= 60 else -1,
                "merchant": (
                    9 if not self.visited_shop and obs.player["gold"] >= 60 else -1
                ),
                "elite": -9 if hp < 0.85 else -5,
                "monster": 0,
                "treasure": 4,
                "unknown": -1,
                "boss": 1,
            }.get(kind, 0)

        def walk(coord, seen):
            if coord in seen or coord not in nodes:
                return 0
            n = nodes[coord]
            return value(n) + 0.8 * max(
                (walk(tuple(c), seen | {coord}) for c in n.get("children", [])),
                default=0,
            )

        return walk((selected["col"], selected["row"]), set())

    def score(self, obs, action):
        kind, player, screen = action.kind, obs.player, obs.screen
        if kind == "choose_map_node":
            selected = next(
                n for n in screen["next_options"] if n["index"] == action.index
            )
            return (
                self._route_score(obs, selected),
                "Visible map path: recovery, affordable shop, fewer elites",
            )
        if kind == "claim_reward":
            item = next(i for i in screen["items"] if i["index"] == action.index)
            return {"gold": 80, "relic": 70, "potion": 60, "card": 50}.get(
                item["type"], 30
            ), "Claim an available reward"
        if kind == "select_card_reward":
            card = next(c for c in screen["cards"] if c["index"] == action.index)
            counts = sum(c.get("id") == card["id"] for c in player["deck"])
            priority = {
                "SHRUG_IT_OFF": 30,
                "POMMEL_STRIKE": 27,
                "BATTLE_TRANCE": 26,
                "FLAME_BARRIER": 28,
                "UPPERCUT": 25,
                "HEADBUTT": 23,
                "CLEAVE": 22,
                "THUNDERCLAP": 21,
                "SHOCKWAVE": 29,
                "INFLAME": 27,
                "METALLICIZE": 25,
                "IMPERVIOUS": 28,
            }
            return (
                priority.get(card["id"], 12 if card.get("type") == "Attack" else 10)
                - 12 * counts
                - max(0, len(player["deck"]) - 16) * 3,
                "Fixed card preference and duplicate/deck-size penalty",
            )
        if kind == "skip_card_reward":
            return 5, "Avoid adding a low-ranked or redundant card"
        if kind == "choose_rest_option":
            option = next(o for o in screen["options"] if o["index"] == action.index)
            name = str(option["id"]).lower()
            hurt = player["hp"] / player["max_hp"] < 0.72
            if name in ("rest", "heal"):
                return (50 if hurt else 5), "Rest below the fixed 72% HP threshold"
            if name in ("smith", "upgrade"):
                return (20 if hurt else 50), "Upgrade when HP is sufficient"
            return 0, "Other enabled rest option"
        if kind == "shop_purchase":
            item = next(i for i in screen["items"] if i["index"] == action.index)
            base = {"relic": 24, "card_removal": 22, "potion": 12, "card": 15}.get(
                item["category"], 0
            )
            return (
                base - item["price"] / 20,
                "Affordable goods ranked by category and price",
            )
        if kind in ("select_card", "combat_select_card"):
            card = next(c for c in screen["cards"] if c["index"] == action.index)
            if card.get("lab_selected"):
                return -20, "Avoid toggling an already selected card"
            upgrade = (
                screen.get("screen_type") == "upgrade"
                or screen.get("mode") == "upgrade_select"
            )
            if upgrade:
                return (
                    40
                    if card["id"] == "BASH"
                    else 25 if card.get("type") == "Attack" else 20
                ), "Fixed upgrade preference"
            return (
                (
                    30
                    if card.get("type") in ("Curse", "Status")
                    else 20 if card["id"].startswith("STRIKE") else 10
                ),
                "Prefer a curse/status or basic Strike for removal/discard; prompt remains visible",
            )
        if kind in ("confirm_selection", "combat_confirm_selection"):
            return 100, "Confirm a valid current selection"
        if kind == "choose_event_option":
            option = next(o for o in screen["options"] if o["index"] == action.index)
            return (
                (30 if option.get("is_proceed") else 10),
                "Prefer an explicit proceed option; otherwise deterministic listed order, no hidden-outcome prediction",
            )
        if kind == "lab_close_shop":
            return 0, "Close inventory after worthwhile purchases"
        if kind == "lab_open_shop" and (obs.act, obs.floor) in self.closed_shop_floors:
            return (
                -30,
                "Inventory already considered on this floor; proceed instead of reopening",
            )
        if kind in (
            "advance_dialogue",
            "lab_open_chest",
            "lab_open_shop",
            "claim_treasure_relic",
        ):
            return 40, "Advance the explicit visible interaction"
        if kind == "proceed":
            return 0, "Continue after higher-ranked available choices"
        if kind == "cancel_selection":
            return -50, "Fallback cancellation"
        if kind in ("play_card", "end_turn", "use_potion"):
            enemies = obs.battle["enemies"]
            incoming = sum(
                visible_amount(i.get("label", ""))
                for e in enemies
                for i in e["intents"]
                if "attack" in i.get("type", "").lower()
            )
            need_block = max(0, incoming - player.get("block", 0))
            if kind == "end_turn":
                return -10, "End turn after useful playable actions"
            if kind == "use_potion":
                return (
                    35
                    if need_block >= player["hp"] or obs.phase in ("boss", "elite")
                    else -15
                ), "Reserve potions for lethal pressure, elites or boss"
            card = next(c for c in player["hand"] if c["index"] == action.index)
            target = next((e for e in enemies if e["entity_id"] == action.target), None)
            amount = visible_amount(card.get("description", ""))
            if card.get("type") == "Attack":
                score = 12 + min(amount, 30) / 3
                if target:
                    score += 15 / max(1, target["hp"] + target["block"])
                    if 0 < target["hp"] + target["block"] <= amount:
                        score += 15
                return (
                    score,
                    "Public attack-text estimate and low-HP target preference; effects resolved only by game",
                )
            if card["id"].startswith("DEFEND") or card["id"] in (
                "SHRUG_IT_OFF",
                "FLAME_BARRIER",
                "IMPERVIOUS",
                "IRON_WAVE",
            ):
                return (
                    24 + min(need_block, amount) / 2 if need_block > 0 else -12
                ), "Block while displayed incoming damage exceeds current block"
            return (
                24 if card.get("type") == "Power" else 18
            ), "Play a legal setup/utility card; no simulated outcome claim"
        return -100, "Unranked supported action"
