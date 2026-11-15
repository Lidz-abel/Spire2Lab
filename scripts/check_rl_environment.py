"""Bounded E0 readiness check: dependencies, native episodes and CPU/CUDA math.

No Windows connection, game action, learned game policy or training run is made.
CUDA is opt-in and requires exactly one explicitly visible GPU. Run inside the
project RL venv; reports and traces should be written beneath ignored artifacts/.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def math_probe(torch, device):
    torch.manual_seed(41)
    model = torch.nn.Linear(8, 4).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    x = torch.arange(32, dtype=torch.float32, device=device).reshape(4, 8) / 32
    before = model.weight.detach().clone()
    loss = model(x).square().mean()
    loss.backward()
    gradients_finite = all(
        torch.isfinite(p.grad).all().item() for p in model.parameters()
    )
    optimizer.step()
    changed = not torch.equal(before, model.weight.detach())
    assert torch.isfinite(loss).item() and gradients_finite and changed
    if device == "cuda":
        torch.cuda.synchronize()
    return {
        "loss": loss.item(),
        "gradients_finite": gradients_finite,
        "weights_changed": changed,
        "scope": "synthetic numerical dependency test; not game RL",
    }


def episode(encounter):
    from sts2lab.gym_env import CombatEnv
    from sts2lab.policies import Policy

    env = CombatEnv(encounter)
    policy = Policy("heuristic", seed=773)
    rows = []
    try:
        observation, metadata = env.reset(seed=1)
        initial = {k: v.tolist() for k, v in observation.items()}
        for _ in range(300):
            visible = env.sim.observe()
            selected = policy.decide(visible).selected_action_id
            action = next(
                i
                for i, candidate in enumerate(env.actions)
                if candidate.action_id == selected
            )
            assert observation["action_mask"][action]
            observation, reward, terminated, truncated, info = env.step(action)
            assert info.get("training_transition", True)
            rows.append(
                {
                    "action": action,
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "observation": {k: v.tolist() for k, v in observation.items()},
                }
            )
            if terminated or truncated:
                assert terminated and not truncated
                assert not observation["action_mask"].any()
                final = env.sim.observe()
                return {
                    "encounter": encounter,
                    "environment_seed": 1,
                    "policy": "heuristic",
                    "steps": len(rows),
                    "outcome": final.outcome,
                    "final_hp": final.player.hp,
                    "encoding_metadata": metadata,
                    "initial": initial,
                    "transitions": rows,
                }
        raise AssertionError("Episode did not finish within the fixed cap")
    finally:
        env.close()


def check(args, report):
    import numpy
    import torch
    from sts2lab.source_integrity import verify_installed_source
    from sts2lab.simulator import CONFIG, load_native

    expected = (ROOT / ".venv-rl").resolve()
    assert (
        Path(sys.prefix).resolve() == expected
    ), "Run using the dedicated .venv-rl interpreter"
    for module in (numpy, torch):
        assert Path(module.__file__).resolve().is_relative_to(expected)
    report["python"] = {
        "executable": sys.executable,
        "prefix": sys.prefix,
        "version": sys.version,
    }
    report["packages"] = {
        name: importlib.metadata.version(name)
        for name in ("torch", "numpy", "gymnasium", "pytest")
    }
    report["dependency_check"] = subprocess.check_output(
        [sys.executable, "-m", "pip", "check"], text=True
    ).strip()
    report["source_verification"] = {
        name: verify_installed_source(name) for name in ("sts2", "sts2mcp-v107")
    }
    _, _, manifest = load_native()
    report["native_sha256"] = manifest["library_sha256"]
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    report["cpu_math"] = math_probe(torch, "cpu")
    assert (
        torch.from_numpy(numpy.array([1.0, 2.0], dtype=numpy.float32)).sum().item() == 3
    )
    report["numpy_torch_bridge"] = True
    if args.cuda:
        selection = os.environ.get("CUDA_VISIBLE_DEVICES", "")
        assert (
            selection and "," not in selection and selection != "-1"
        ), "Select exactly one GPU explicitly"
        assert torch.cuda.is_available() and torch.cuda.device_count() == 1
        device = torch.cuda.get_device_properties(0)
        report["cuda"] = {
            "visible_devices": selection,
            "torch_cuda_runtime": torch.version.cuda,
            "name": device.name,
            "memory_bytes": device.total_memory,
            "capability": list(torch.cuda.get_device_capability(0)),
            "math": math_probe(torch, "cuda"),
        }
    else:
        report["cuda"] = {"tested": False}
    report["episodes"] = []
    for encounter in CONFIG["encounters"]:
        first, second = episode(encounter), episode(encounter)
        assert first == second, f"Repeated public trajectory differs: {encounter}"
        raw = json.dumps(
            first, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode()
        target = args.output.parent / f"{encounter}-seed1.json"
        target.write_bytes(raw + b"\n")
        report["episodes"].append(
            {key: first[key] for key in ("encounter", "steps", "outcome", "final_hp")}
            | {
                "repeat_matched": True,
                "trace": target.name,
                "file_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cuda", action="store_true")
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": False,
        "scope": "E0 dependency/native readiness; no original-game acceptance or RL agent training",
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }
    try:
        check(args, report)
        report["passed"] = True
    except Exception:
        report["error"] = traceback.format_exc()
        raise
    finally:
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
