"""Observable tactical goals with explicit duration and termination accounting."""

from dataclasses import asdict, dataclass


def incoming_damage(obs):
    # The observation magnitude already includes the multi-hit total.
    return sum(
        i.magnitude or 0 for e in obs.enemies for i in e.intents if i.deals_damage
    )


@dataclass
class Goal:
    goal_id: str
    kind: str
    parent_decision_id: str
    start_turn: int
    target_type: str | None = None
    target_max_hp: int | None = None
    duration: int = 0
    cumulative_reward: float = 0.0

    def to_dict(self):
        return asdict(self)


class TacticalHierarchy:
    def __init__(self, max_actions=3):
        self.max_actions = max_actions
        self.current = None
        self.sequence = 0

    def select(self, obs):
        if self.current is not None:
            return self.current
        deficit = max(0, incoming_damage(obs) - obs.player.block)
        kind, target = "progress_combat", None
        if deficit >= max(8, obs.player.hp * 0.2):
            kind = "survive_turn"
        elif obs.enemies:
            enemy = min(obs.enemies, key=lambda e: e.hp + e.block)
            matches = [
                e
                for e in obs.enemies
                if (e.type_id, e.max_hp) == (enemy.type_id, enemy.max_hp)
            ]
            if len(matches) == 1:
                kind, target = "focus_enemy", enemy
        self.sequence += 1
        self.current = Goal(
            f"{obs.decision_id}:goal:{self.sequence}",
            kind,
            obs.decision_id,
            obs.turn,
            target.type_id if target else None,
            target.max_hp if target else None,
        )
        return self.current

    def observe_transition(self, before, after, reward, manual):
        goal = self.current
        if goal is None:
            return None
        goal.duration += 1
        goal.cumulative_reward += reward
        reason = None
        if after.outcome != "ongoing":
            reason = "terminal"
        elif manual:
            reason = "manual_override"
        elif after.turn != goal.start_turn:
            reason = "turn_boundary"
        elif goal.kind == "focus_enemy" and not any(
            (e.type_id, e.max_hp) == (goal.target_type, goal.target_max_hp)
            for e in after.enemies
        ):
            reason = "target_removed"
        elif goal.kind == "survive_turn" and after.player.block >= incoming_damage(
            after
        ):
            reason = "visible_intent_covered"
        elif goal.duration >= self.max_actions:
            reason = "duration_limit"
        if reason:
            self.current = None
            return {
                **goal.to_dict(),
                "termination_reason": reason,
                "end_decision_id": after.decision_id,
                "reward_version": "terminal-win-v1",
            }
        return None

    def interrupt(self, reason, decision_id):
        if self.current is None:
            return None
        event = {
            **self.current.to_dict(),
            "termination_reason": reason,
            "end_decision_id": decision_id,
            "reward_version": "terminal-win-v1",
        }
        self.current = None
        return event


def leaf_utility(root, obs, goal=None):
    """Fixed planning utility; never modifies the environment reward."""
    hp = obs.player.hp / max(1, obs.player.max_hp)
    if obs.outcome == "won":
        return 1.0 + 0.5 * hp
    if obs.outcome == "lost":
        return -2.0
    enemy_scale = max(1, sum(e.max_hp for e in root.enemies))
    remaining = sum(e.hp for e in obs.enemies) / enemy_scale
    risk = max(0, incoming_damage(obs) - obs.player.block) / max(1, obs.player.max_hp)
    value = 0.5 * hp - 0.6 * remaining - 0.15 * risk
    if goal and goal.kind == "survive_turn":
        value -= (
            0.3 * max(0, root.player.hp - obs.player.hp) / max(1, root.player.max_hp)
        )
        if obs.turn == root.turn:
            value -= 0.2 * risk
    elif goal and goal.kind == "focus_enemy":
        target = next(
            (
                e
                for e in obs.enemies
                if (e.type_id, e.max_hp) == (goal.target_type, goal.target_max_hp)
            ),
            None,
        )
        value += 0.2 * (1 - (target.hp / target.max_hp if target else 0))
    return value
