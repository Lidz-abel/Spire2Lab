"""Frozen E3 experiment and separate per-seed budget; E2 remains unchanged."""

import fcntl
import json
from pathlib import Path

from .contracts import digest
from .rl_contract import ROOT, load_recipe
from .rl_io import Budget, compatibility, file_hash

EXPERIMENT_PATH = ROOT / "config/rl-e3-v1.json"


def load_experiment(path=EXPERIMENT_PATH):
    spec = json.loads(Path(path).read_text())
    expected = {
        "version": "rl-e3-v1",
        "base_recipe": "config/rl-mvp-v1.json",
        "training_run_seeds": [41, 42, 43],
        "valid_transitions_per_seed": 32768,
        "campaign_hard_cap": 98304,
        "workers": 4,
        "device": "cpu",
        "torch_threads": 1,
        "max_parallel_learners": 1,
        "max_seconds_per_run": 900,
        "validation_every_updates": 8,
        "final_test_enabled": False,
        "fresh_initialization": True,
        "evaluate_initial_policy": True,
        "reward_shaping": False,
        "hyperparameter_search": False,
        "early_stopping_on_performance": False,
        "include_initial_checkpoint_in_selection": False,
        "campaign_directory": "artifacts/rl-mvp/experiments/e3-20261115-v1",
    }
    if any(
        spec.get(k) != v or type(spec.get(k)) != type(v) for k, v in expected.items()
    ):
        raise ValueError(
            "E3 frozen experiment differs; register a new version before changes"
        )
    if file_hash(ROOT / spec["base_recipe"]) != spec["base_recipe_sha256"]:
        raise ValueError("E3 base recipe fingerprint mismatch")
    return spec, load_recipe()


def experiment_compatibility(spec, base):
    return {
        "base": compatibility(base),
        "experiment": digest(spec),
        "files": {
            p: file_hash(ROOT / p)
            for p in (
                "config/rl-e3-v1.json",
                "sts2lab/rl_experiment.py",
                "scripts/train_rl_e3.py",
            )
        },
    }


class ExperimentBudget(Budget):
    """Reuse E2 append/fsync/close; independently initialize E3's frozen caps.

    The E2 Budget constructor and its 10,000 ceiling are deliberately untouched.
    """

    def __init__(self, path, spec, seed):
        if seed not in spec["training_run_seeds"]:
            raise ValueError("Unregistered training seed")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+")
        self.seed = seed
        self.cap = spec["campaign_hard_cap"]
        self.seed_cap = spec["valid_transitions_per_seed"]
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.file.seek(0)
            events = [json.loads(line) for line in self.file]
            header = {
                "experiment_sha256": digest(spec),
                "campaign_cap": self.cap,
                "seed_cap": self.seed_cap,
            }
            if not events:
                self._event({"header": header})
                events = [{"header": header}]
            if events[0].get("header") != header:
                raise ValueError("Experiment budget fingerprint mismatch")
            self.charged = sum(e.get("reserved", 0) for e in events)
            self.valid = sum(e.get("confirmed", 0) for e in events)
            by_seed = {
                s: (
                    sum(e.get("reserved", 0) for e in events if e.get("seed") == s),
                    sum(e.get("confirmed", 0) for e in events if e.get("seed") == s),
                )
                for s in spec["training_run_seeds"]
            }
            self.seed_charged, self.seed_valid = by_seed[seed]
            if (
                self.valid > self.charged
                or self.charged > self.cap
                or sum(v[0] for v in by_seed.values()) != self.charged
                or any(
                    not 0 <= confirmed <= charged <= self.seed_cap
                    for charged, confirmed in by_seed.values()
                )
            ):
                raise ValueError("Invalid experiment ledger")
        except BaseException:
            self.file.close()
            raise

    def reserve(self, count, run_id):
        if (
            type(count) is not int
            or count <= 0
            or self.charged + count > self.cap
            or self.seed_charged + count > self.seed_cap
        ):
            raise ValueError("E3 campaign or seed budget exhausted")
        self._event({"reserved": count, "seed": self.seed, "run_id": run_id})
        self.charged += count
        self.seed_charged += count

    def confirm(self, count, run_id):
        if (
            type(count) is not int
            or count <= 0
            or self.seed_valid + count > self.seed_charged
        ):
            raise ValueError("Cannot confirm unreserved E3 transitions")
        self._event({"confirmed": count, "seed": self.seed, "run_id": run_id})
        self.valid += count
        self.seed_valid += count
