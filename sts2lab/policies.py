"""Policies receive only Observation. Scores describe the actual decision rule."""

import random
import time
from .contracts import Candidate, Decision, Observation


class Policy:
    def __init__(self, name="heuristic", seed=0):
        if name not in ("random", "heuristic"):
            raise ValueError("Unknown policy")
        self.name = name
        self.rng = random.Random(seed)

    def decide(self, obs: Observation) -> Decision:
        started = time.perf_counter()
        if not obs.legal_actions:
            raise ValueError("No legal decision at terminal state")
        candidates = []
        incoming = sum(
            i.magnitude for e in obs.enemies for i in e.intents if i.deals_damage
        )
        deficit = max(0, incoming - obs.player.block)
        cards = {c.ref: c for c in obs.hand}
        enemies = {e.ref: e for e in obs.enemies}
        for action in obs.legal_actions:
            if self.name == "random":
                score = self.rng.random()
                reasons = ["为每个合法动作抽取独立均匀随机数，选择最大者"]
            elif action.kind == "end_turn":
                score, reasons = -100.0, ["仍有可出牌时优先行动；只剩结束回合时执行"]
            else:
                card = cards[action.card_ref]
                attack = card.printed_damage + card.bonus_damage
                block = min(max(0, card.printed_block), deficit)
                score = float(attack + block * 1.5 - max(0, card.cost) * 0.1)
                reasons = [
                    f"牌面伤害项 +{attack}",
                    f"按当前意图计算的防御缺口 {deficit}；格挡评分 +{block * 1.5:g}",
                    f"费用评分 -{max(0, card.cost) * .1:g}",
                ]
                if action.target_ref:
                    enemy = enemies[action.target_ref]
                    if attack >= enemy.hp + enemy.block:
                        score += 20
                        reasons.append(
                            "牌面伤害达到目标生命与护甲：集中攻击评分 +20（非结算保证）"
                        )
                    score += 1 / max(1, enemy.hp)
                if card.type_id == "BASH":
                    score += 3
                    reasons.append("痛击的易伤效果评分 +3")
            candidates.append(
                Candidate(action_id=action.action_id, score=score, reasons=reasons)
            )
        candidates.sort(key=lambda c: c.score, reverse=True)
        return Decision(
            decision_id=obs.decision_id,
            policy=f"{self.name}-v1",
            selected_action_id=candidates[0].action_id,
            candidates=candidates,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            score_semantics=(
                "random_priority" if self.name == "random" else "heuristic_points"
            ),
        )
