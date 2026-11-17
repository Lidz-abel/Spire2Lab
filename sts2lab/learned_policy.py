"""Fixed starter PPO deployment using public observations and pinned local weights."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time
from types import SimpleNamespace

import numpy as np
import torch

from .contracts import Candidate, Decision, Observation, digest
from .gym_env import CombatEnv
from .rl_experiment import load_experiment
from .rl_io import compatibility, file_hash, isolated_rng, load_checkpoint, state_digest
from .rl_model import ActorCritic, tensor_batch
from .simulator import CONFIG, ROOT

DEPLOYMENT_PATH = ROOT / "config/rl-deployment-v1.json"
ENEMIES = {
    "nibbits-weak": {"Nibbit"},
    "slimes-weak": {"LeafSlimeM", "LeafSlimeS", "TwigSlimeM", "TwigSlimeS"},
    "sludge-spinner": {"SludgeSpinner"},
}


class PolicyInputError(ValueError):
    """An unsupported input is a stopped decision, never a rule fallback."""


def encode_public_observation(obs: Observation, encounter: str):
    if encounter not in ENEMIES:
        raise PolicyInputError("Encounter outside learned starter scope")
    if obs.phase != "combat" or obs.outcome != "ongoing" or obs.unavailable_fields:
        raise PolicyInputError("Learned policy requires complete ongoing combat")
    if (
        obs.player.max_hp != CONFIG["max_hp"]
        or obs.player.max_energy != 3
        or obs.player.energy is None
        or obs.player.gold != CONFIG["gold"]
        or not 0 < obs.player.hp <= obs.player.max_hp
        or [r.type_id for r in obs.relics] != CONFIG["relics"]
    ):
        raise PolicyInputError("Player or relics outside fixed starter scope")
    cards = obs.hand + obs.draw_pile + obs.discard_pile + obs.exhaust_pile
    base = Counter(c.type_id for c in cards if c.type_id != "SLIMED")
    if base != Counter(CONFIG["deck"]):
        raise PolicyInputError("Deck outside fixed starter scope")
    if any(
        c.upgraded or c.enchantment != "None" or c.enchant_amount or c.free_this_turn
        for c in cards
    ):
        raise PolicyInputError("Upgrades, enchantments or free cards are unsupported")
    if obs.known_top or obs.known_bottom:
        raise PolicyInputError("Starter scope cannot establish known draw order")
    if not obs.enemies or any(e.type_id not in ENEMIES[encounter] for e in obs.enemies):
        raise PolicyInputError("Enemy outside selected encounter")
    hands = {c.ref: c for c in obs.hand}
    enemies = {e.ref for e in obs.enemies}
    if (
        len(hands) != len(obs.hand)
        or "" in hands
        or len(enemies) != len(obs.enemies)
        or "" in enemies
        or not obs.legal_actions
        or len({a.action_id for a in obs.legal_actions}) != len(obs.legal_actions)
    ):
        raise PolicyInputError("Missing or duplicate public action/entity references")
    for a in obs.legal_actions:
        if not a.action_id:
            raise PolicyInputError("Missing action identifier")
        if a.kind == "end_turn":
            valid = a.card_ref is None and a.target_ref is None
        elif a.kind == "play_card" and a.card_ref in hands:
            c = hands[a.card_ref]
            valid = (
                a.target_ref in enemies
                if c.target == "AnyEnemy"
                else a.target_ref is None
            )
        else:
            valid = False
        if not valid:
            raise PolicyInputError("Unsupported action or invalid public reference")
    # Reuse the frozen E1/E2 encoder without constructing or resetting a simulator.
    # Its sole observe() source is this already-public Observation; there is no
    # engine, private state, seed, step, reset or branching interface in the view.
    template = CombatEnv(encounter)
    view = SimpleNamespace(
        observation_space=template.observation_space,
        vocabulary=template.vocabulary,
        sim=SimpleNamespace(observe=lambda: obs),
    )
    try:
        encoded = CombatEnv._encode(view)
        tensor_batch([encoded])  # validate categorical, capacity and action contract
    except (ValueError, RuntimeError, KeyError, OverflowError, TypeError) as exc:
        raise PolicyInputError(f"Unsupported public encoding: {exc}") from exc
    return encoded


class LearnedPolicy:
    name = "ppo"
    is_learned = True

    def __init__(self, encounter):
        self.spec = json.loads(DEPLOYMENT_PATH.read_text())
        self.encounter = encounter
        if encounter not in self.spec["encounters"] or encounter not in ENEMIES:
            raise ValueError("Encounter outside learned deployment")
        if (
            self.spec["version"] != "starter-ppo-deployment-v1"
            or self.spec["action_rule"] != "greedy_logits_first_index_on_tie"
            or self.spec["fallback"] != "refuse_unsupported_no_rule_fallback"
            or self.spec["device"] != "cpu"
            or self.spec["final_test_enabled"]
            or self.spec["max_decisions"] != CONFIG["max_steps"]
        ):
            raise ValueError("Unsupported deployment contract")
        path = ROOT / self.spec["checkpoint"]
        # Verify the registered artifact before deserializing trusted Torch pickle.
        if file_hash(path) != self.spec["checkpoint_sha256"]:
            raise ValueError("Registered checkpoint SHA mismatch")
        experiment, base = load_experiment()
        manifest = json.loads((ROOT / self.spec["run_manifest"]).read_text())
        expected = manifest["compatibility"]
        if (
            manifest["source"]["dirty"]
            or expected["base"] != compatibility(base)
            or expected["experiment"] != digest(experiment)
        ):
            raise ValueError("Historical model core compatibility mismatch")
        for name, checksum in expected["files"].items():
            content = subprocess.check_output(
                ["git", "show", f"{manifest['source']['commit']}:{name}"], cwd=ROOT
            )
            if hashlib.sha256(content).hexdigest() != checksum:
                raise ValueError("Historical driver source fingerprint mismatch")
        torch.set_num_threads(self.spec["torch_threads"])
        with isolated_rng():
            self.model = ActorCritic(base)
            data = load_checkpoint(
                path, self.model, None, expected, restore_random=False
            )
        if data["source"] != manifest["source"] or data["recipe"]["base"] != base:
            raise ValueError("Checkpoint origin or recipe mismatch")
        self.model.eval()
        self.model.requires_grad_(False)
        self.calls = 0
        self.last_report = None
        self._provenance = {
            "deployment_version": self.spec["version"],
            "deployment_sha256": file_hash(DEPLOYMENT_PATH),
            "checkpoint_sha256": self.spec["checkpoint_sha256"],
            "model_state_sha256": state_digest(self.model.state_dict()),
            "training_source": data["source"],
            "training_counters": data["counters"],
            "adapter_sha256": file_hash(Path(__file__)),
            "deployment_files": {
                name: file_hash(ROOT / name)
                for name in (
                    "sts2lab/runtime.py",
                    "sts2lab/original.py",
                    "sts2lab/bridge.py",
                    "sts2lab/images.py",
                    "sts2lab/server.py",
                )
            },
            "input": "public_observation_only",
            "action_rule": self.spec["action_rule"],
            "scope": self.spec["scope"],
            "selection_basis": self.spec["selection_basis"],
            "device": "cpu",
            "fallback": False,
        }

    def provenance(self):
        return dict(self._provenance)

    def decide(self, obs: Observation):
        self.last_report = None
        if self.calls >= self.spec["max_decisions"]:
            raise PolicyInputError("Learned decision cap reached")
        started = time.perf_counter()
        encoded = encode_public_observation(obs, self.encounter)
        with torch.inference_mode():
            logits, value = self.model(tensor_batch([encoded]))
        scores = logits[0, : len(obs.legal_actions)].cpu().numpy().astype(float)
        estimate = float(value.item())
        if not np.isfinite(scores).all() or not np.isfinite(estimate):
            raise PolicyInputError("Non-finite learned prediction")
        index = int(np.argmax(scores))
        selected = obs.legal_actions[index].action_id
        self.calls += 1
        self.last_report = {
            **self.provenance(),
            "decision_id": obs.decision_id,
            "observation_sha256": digest(obs),
            "encoded_sha256": state_digest(encoded),
            "inference_call": self.calls,
            "action_ids": [a.action_id for a in obs.legal_actions],
            "logits": scores.tolist(),
            "value_estimate": estimate,
            "selected_index": index,
            "selected_action_id": selected,
            "score_semantics": "policy_logits_not_win_probability",
        }
        candidates = [
            Candidate(
                action_id=a.action_id,
                score=float(s),
                reasons=[
                    "PPO模型对公开状态的策略评分（logit），不是胜率或伤害预测",
                    "在当前合法动作中选择最高分；无规则回退",
                ],
            )
            for a, s in zip(obs.legal_actions, scores)
        ]
        candidates.sort(key=lambda c: c.score, reverse=True)
        return Decision(
            decision_id=obs.decision_id,
            policy=self.spec["version"],
            selected_action_id=selected,
            candidates=candidates,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            score_semantics="policy_logits_not_win_probability",
        )
