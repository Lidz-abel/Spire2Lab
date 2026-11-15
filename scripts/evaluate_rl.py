"""Re-evaluate trusted E2 checkpoints on validation only; never the final split."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--policy", choices=("random", "heuristic", "rl_greedy"), required=True
    )
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.policy == "rl_greedy") != bool(args.checkpoint):
        parser.error("rl_greedy requires --checkpoint; baselines must omit it")
    if not args.output.resolve().is_relative_to(ROOT / "artifacts"):
        parser.error("Output must be under artifacts/")
    import torch
    from sts2lab.rl_contract import load_recipe
    from sts2lab.rl_io import compatibility, load_checkpoint
    from sts2lab.rl_model import ActorCritic
    from sts2lab.rl_evaluate import evaluate

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    recipe = load_recipe()
    model = None
    if args.checkpoint:
        model = ActorCritic(recipe)
        load_checkpoint(
            args.checkpoint, model, None, compatibility(recipe), restore_random=False
        )
    print(evaluate(recipe, args.policy, args.output, model))


if __name__ == "__main__":
    main()
