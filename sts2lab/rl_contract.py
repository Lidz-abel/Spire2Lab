"""E1 public feature and rollout boundary contract, independent of Torch.

No policy, collector, optimizer or environment reset is performed here. Arrays
crossing this boundary are copied; simulator handles and info never reach a model.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from .vocabulary import vocabulary

ROOT = Path(__file__).resolve().parents[1]
RECIPE_PATH = ROOT / "config/rl-mvp-v1.json"

# shape, categorical (column, vocabulary) pairs, per-column numeric divisors.
# Categorical columns are removed from numeric output, never treated as ranks.
FEATURES = {
    "player": ((8,), (), (80, 80, 80, 3, 3, 100, 30, 10)),
    "hand": ((10, 7), ((0, "cards"),), (1, 1, 3, 20, 20, 20, 10)),
    "piles": ((3, 64, 7), ((0, "cards"),), (1, 1, 3, 20, 20, 20, 10)),
    "known_order": ((2, 10, 7), ((0, "cards"),), (1, 1, 3, 20, 20, 20, 10)),
    "enemies": (
        (6, 13),
        ((0, "enemies"), (4, "intents"), (8, "intents")),
        (1, 80, 80, 80, 1, 20, 5, 1, 1, 20, 5, 1, 1),
    ),
    "powers": ((7, 16, 2), ((0, "powers"),), (1, 10)),
    "relics": ((8, 2), ((0, "relics"),), (1, 10)),
}
FIELD_ORDER = tuple(FEATURES)


def load_recipe(path=RECIPE_PATH):
    """Fail closed when the frozen environment or split boundaries have drifted."""
    recipe = json.loads(Path(path).read_text())
    if recipe["version"] != "rl-mvp-v1":
        raise ValueError("Unsupported training recipe version")
    for field, relative in (
        ("phase1_sha256", "config/phase1.json"),
        ("vocabulary_sha256", "config/content-v1.json"),
    ):
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != recipe[field]:
            raise ValueError(f"Recipe fingerprint mismatch: {field}")
    from .gym_env import ENCODING_VERSION
    from .simulator import CONFIG

    if (
        recipe["encoding_version"] != ENCODING_VERSION
        or recipe["feature_version"] != "public-entities-scaled-v1"
        or recipe["reward_version"] != "terminal-win-v1"
        or recipe["episode_max_steps"] != CONFIG["max_steps"]
        or recipe["encounters"] != CONFIG["encounters"]
    ):
        raise ValueError("Recipe environment contract mismatch")
    ranges = recipe["environment_seed_ranges_inclusive"]
    if set(ranges) != {"train", "validation", "test"}:
        raise ValueError("Expected train/validation/test splits")
    if recipe["excluded_historical_seed_ranges_inclusive"] != [
        [1, 10],
        [1001, 1010],
        [2001, 2030],
    ]:
        raise ValueError("Historical exclusions cannot be removed")
    intervals = (
        list(ranges.values()) + recipe["excluded_historical_seed_ranges_inclusive"]
    )
    for interval in intervals:
        if (
            len(interval) != 2
            or any(type(n) is not int for n in interval)
            or not 0 <= interval[0] <= interval[1] < 2**31
        ):
            raise ValueError("Invalid seed range")
    for i, (start, end) in enumerate(intervals):
        for other_start, other_end in intervals[i + 1 :]:
            if max(start, other_start) <= min(end, other_end):
                raise ValueError("Seed splits overlap or reuse historical seeds")
    smoke = recipe["smoke"]
    if (
        not 0
        < smoke["target_valid_transitions"]
        <= smoke["hard_cap_valid_transitions"]
        <= 10000
    ):
        raise ValueError("Smoke transition budget exceeds E2 scope")
    if smoke["test_split_enabled"] or recipe["formal_training"]["enabled"]:
        raise ValueError("E1 recipe does not authorize final evaluation or E3 training")
    return recipe


def evaluation_cases(recipe, split):
    """Materialize IDs only; reading the test manifest does not execute a test."""
    if split not in {"train", "validation", "test"}:
        raise ValueError("Unknown split")
    start, end = recipe["environment_seed_ranges_inclusive"][split]
    return [
        (encounter, seed)
        for encounter in recipe["encounters"]
        for seed in range(start, end + 1)
    ]


def _integer_array(value, shape, name):
    a = np.asarray(value)
    if a.shape != shape or a.dtype.kind not in "iu":
        raise ValueError(f"{name}: wrong shape or non-integer data")
    if np.any(a < -(2**30)) or np.any(a > 2**30):
        raise ValueError(f"{name}: outside encoding range")
    return a.astype(np.int64, copy=True)


def prepare_observation(observation, *, episode_done=False):
    """Return categorical IDs, scaled numbers and masks from encoded public data.

    All-zero action masks are allowed only for value-only terminal/truncated
    observations. Numeric features use fixed divisors without clipping or fitting.
    """
    if set(observation) != set(FEATURES) | {"actions", "action_mask"}:
        raise ValueError("Unexpected observation fields (private metadata forbidden)")
    out = {"tokens": {}, "numeric": {}, "present": {}}
    tables = vocabulary().tables
    for name, (shape, categories, scales) in FEATURES.items():
        a = _integer_array(observation[name], shape, name)
        columns = [column for column, _ in categories]
        for column, category in categories:
            if not np.isin(a[..., column], [0, *tables[category].values()]).all():
                raise ValueError(f"Unknown {category} token")
        if categories:
            present = a[..., 0] != 0
            if np.any(a[~present] != 0):
                raise ValueError(f"{name}: nonzero padding")
            out["present"][name] = present
        if name == "enemies" and not np.array_equal(a[..., 12], present):
            raise ValueError("Enemy presence differs from token")
        if name == "enemies":
            for column in (4, 8):
                if np.any(a[a[:, column] == 0, column + 1 : column + 4] != 0):
                    raise ValueError("Nonzero padding for absent intent")
        out["tokens"][name] = a[..., columns]
        numeric_columns = [i for i in range(shape[-1]) if i not in columns]
        out["numeric"][name] = (
            a[..., numeric_columns] / np.asarray(scales)[numeric_columns]
        ).astype(np.float32)
    actions = _integer_array(observation["actions"], (64, 3), "actions")
    mask = _integer_array(observation["action_mask"], (64,), "action_mask")
    if not np.isin(mask, [0, 1]).all():
        raise ValueError("Non-binary action mask")
    mask = mask.astype(bool)
    if bool(mask.any()) == bool(episode_done):
        raise ValueError("Action mask inconsistent with episode boundary")
    if not np.isin(actions[:, 0], [0, *tables["actions"].values()]).all():
        raise ValueError("Unknown action token")
    if np.any(actions[actions[:, 0] == 0] != 0) or np.any(mask & (actions[:, 0] == 0)):
        raise ValueError("Invalid action padding")
    if not episode_done and not np.array_equal(mask, actions[:, 0] != 0):
        raise ValueError("Mask omits an encoded legal candidate")
    for kind, hand, enemy in actions[actions[:, 0] != 0]:
        if kind == tables["actions"]["end_turn"]:
            if (hand, enemy) != (-1, -1):
                raise ValueError("end_turn cannot reference an entity")
        elif (
            not 0 <= hand < 10
            or not out["present"]["hand"][hand]
            or not -1 <= enemy < 6
            or (enemy >= 0 and not out["present"]["enemies"][enemy])
        ):
            raise ValueError("Candidate references unavailable entity")
    out["action_tokens"] = actions[:, 0].copy()
    out["action_references"] = actions[:, 1:].copy()
    out["action_mask"] = mask
    return out


def _copy_observation(observation):
    return {k: np.array(v, copy=True) for k, v in observation.items()}


@dataclass(frozen=True)
class PublicTransition:
    observation: dict
    action: int
    reward: float
    next_observation: dict
    terminated: bool
    truncated: bool

    @property
    def bootstrap(self):
        return not self.terminated

    @property
    def continue_trace(self):
        return not (self.terminated or self.truncated)


def validate_transition(observation, action, step_result):
    """Reject no-ops/errors; retain the final observation before explicit reset.

    This accepts only the unwrapped CombatEnv five-tuple. Auto-reset wrappers
    must be adapted explicitly in a future collector, not silently accepted here.
    """
    before = prepare_observation(observation)
    if (
        not isinstance(action, (int, np.integer))
        or isinstance(action, (bool, np.bool_))
        or not 0 <= action < 64
        or not before["action_mask"][action]
    ):
        raise ValueError("Selected action is not legal")
    after, reward, terminated, truncated, info = step_result
    if any(k in info for k in ("final_observation", "final_obs", "final_info")):
        raise ValueError(
            "Auto-reset result requires explicit final-observation handling"
        )
    if info.get("invalid_action", False) or not info.get("training_transition", True):
        raise ValueError("Invalid/no-op step is not a training transition")
    if info.get("reward_version") != "terminal-win-v1":
        raise ValueError("Reward version mismatch")
    if (
        type(terminated) is not bool
        or type(truncated) is not bool
        or (terminated and truncated)
    ):
        raise ValueError("Invalid terminal flags")
    if not np.isfinite(reward) or (
        reward not in (-1.0, 1.0) if terminated else reward != 0.0
    ):
        raise ValueError("Reward violates terminal-win-v1")
    prepare_observation(after, episode_done=terminated or truncated)
    return PublicTransition(
        _copy_observation(observation),
        int(action),
        float(reward),
        _copy_observation(after),
        terminated,
        truncated,
    )
