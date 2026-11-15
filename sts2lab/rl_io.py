"""Local experiment evidence, irreversible budget accounting, and learner snapshots."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess

import numpy as np
import torch

from .contracts import digest
from .rl_contract import ROOT


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state_digest(value):
    h = hashlib.sha256()

    def visit(v):
        if isinstance(v, torch.Tensor):
            visit(v.detach().cpu().numpy())
        elif isinstance(v, np.ndarray):
            h.update(str((v.dtype.str, v.shape)).encode())
            h.update(v.tobytes())
        elif isinstance(v, dict):
            h.update(b"dict")
            for key in sorted(v, key=repr):
                visit(key)
                visit(v[key])
        elif isinstance(v, (tuple, list)):
            h.update(type(v).__name__.encode())
            for item in v:
                visit(item)
        else:
            h.update(repr(v).encode())
            h.update(b"\0")

    visit(value)
    return h.hexdigest()


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")


def append_json(path, data):
    with Path(path).open("a") as f:
        f.write(json.dumps(data, ensure_ascii=False, allow_nan=False) + "\n")
        f.flush()


def compatibility(recipe):
    paths = [
        "config/content-v1.json",
        "config/phase1.json",
        "requirements-rl.lock",
        "sts2lab/gym_env.py",
        "sts2lab/simulator.py",
        "sts2lab/contracts.py",
        "sts2lab/vocabulary.py",
        "sts2lab/rl_contract.py",
        "sts2lab/rl_model.py",
        "sts2lab/rl_ppo.py",
        "sts2lab/rl_rollout.py",
        "sts2lab/rl_io.py",
        "sts2lab/rl_evaluate.py",
        "scripts/train_rl.py",
        "scripts/evaluate_rl.py",
        "vendor/manifest.json",
        ".tools/native/build.json",
        ".tools/native/Sts2Emulator.so",
    ]
    hashes = {name: file_hash(ROOT / name) for name in paths}
    if hashes[".tools/native/Sts2Emulator.so"] != recipe["native_sha256"]:
        raise ValueError("Native recipe mismatch")
    return {
        "recipe_sha256": digest(recipe),
        "files": hashes,
        "torch": torch.__version__,
        "numpy": np.__version__,
    }


def source_version():
    return {
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
    }


def rng_state():
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
    }


def restore_rng(state):
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])


@contextmanager
def isolated_rng():
    before = rng_state()
    try:
        yield
    finally:
        restore_rng(before)


class Budget:
    """One campaign ledger, locked for the whole run. Reservations never roll back.

    Reserve before dispatch; confirm after validated replies. A killed worker can
    leave a reservation unconfirmed: it remains charged against the hard cap.
    """

    def __init__(self, path, cap=10000):
        if not 0 < cap <= 10000:
            raise ValueError("E2 hard cap is 10000")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+")
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.file.seek(0)
            events = [json.loads(line) for line in self.file]
            self.charged = sum(e.get("reserved", 0) for e in events)
            self.valid = sum(e.get("confirmed", 0) for e in events)
            self.cap = cap
            if self.valid > self.charged or self.charged > cap:
                raise ValueError("Invalid budget ledger")
        except BaseException:
            self.file.close()
            raise

    def _event(self, event):
        self.file.write(
            json.dumps({"at": datetime.now(timezone.utc).isoformat(), **event}) + "\n"
        )
        self.file.flush()
        os.fsync(self.file.fileno())

    def reserve(self, count, run_id):
        if type(count) is not int or count <= 0 or self.charged + count > self.cap:
            raise ValueError("E2 budget exhausted")
        self._event({"reserved": count, "run_id": run_id})
        self.charged += count

    def confirm(self, count, run_id):
        if type(count) is not int or count <= 0 or self.valid + count > self.charged:
            raise ValueError("Cannot confirm unreserved transitions")
        self._event({"confirmed": count, "run_id": run_id})
        self.valid += count

    def close(self):
        self.file.close()


def save_checkpoint(
    path,
    model,
    optimizer,
    recipe,
    compatible,
    scheduler,
    counters,
    validation,
    active_episodes,
    probe,
    origin,
):
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    payload = {
        "format": "rl-checkpoint-v1",
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "rng": rng_state(),
        "recipe": recipe,
        "compatibility": compatible,
        "scheduler": scheduler,
        "counters": counters,
        "validation": validation,
        "active_episodes": active_episodes,
        "probe": probe,
        "source": origin,
        "resume_mode": "reset_environments",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with temporary.open("xb") as f:
        torch.save(payload, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)
    write_json(
        path.with_suffix(".sha256.json"),
        {"sha256": file_hash(path), "model_sha256": state_digest(payload["model"])},
    )


def load_checkpoint(path, model, optimizer, compatible, *, restore_random=True):
    """Load ONLY trusted project-produced local checkpoints (Torch pickle format)."""
    path = Path(path)
    expected = json.loads(path.with_suffix(".sha256.json").read_text())["sha256"]
    if file_hash(path) != expected:
        raise ValueError("Checkpoint checksum mismatch")
    data = torch.load(path, map_location="cpu", weights_only=False)
    if data.get("format") != "rl-checkpoint-v1" or data["compatibility"] != compatible:
        raise ValueError("Checkpoint compatibility mismatch")
    model.load_state_dict(data["model"], strict=True)
    if optimizer is not None:
        optimizer.load_state_dict(data["optimizer"])
    if restore_random:
        restore_rng(data["rng"])
    return data
