"""Clipped PPO and time-major GAE, implemented from the frozen E1 equations."""

import numpy as np
import torch

from .rl_model import select_batch


def gae(rewards, values, next_values, terminated, truncated, gamma, lam):
    arrays = [
        np.asarray(x) for x in (rewards, values, next_values, terminated, truncated)
    ]
    if len({x.shape for x in arrays}) != 1 or arrays[0].ndim != 2:
        raise ValueError("GAE requires equal [time, worker] arrays")
    rewards, values, next_values, terminated, truncated = arrays
    if (
        terminated.dtype != bool
        or truncated.dtype != bool
        or (terminated & truncated).any()
    ):
        raise ValueError("Invalid GAE boundary flags")
    if not all(np.isfinite(a).all() for a in arrays[:3]):
        raise ValueError("Nonfinite rollout")
    advantages = np.zeros_like(values, dtype=np.float32)
    carry = np.zeros(values.shape[1], dtype=np.float32)
    for t in reversed(range(len(values))):
        delta = rewards[t] + gamma * (~terminated[t]) * next_values[t] - values[t]
        carry = delta + gamma * lam * (~(terminated[t] | truncated[t])) * carry
        advantages[t] = carry
    return advantages, advantages + values


def clipped_policy_loss(new_log_prob, old_log_prob, advantage, clip_ratio):
    log_ratio = new_log_prob - old_log_prob
    ratio = log_ratio.exp()
    loss = -torch.minimum(
        ratio * advantage, ratio.clamp(1 - clip_ratio, 1 + clip_ratio) * advantage
    ).mean()
    return loss, ratio, log_ratio


def update(
    model,
    optimizer,
    batch,
    actions,
    old_log_prob,
    old_values,
    rewards,
    next_values,
    terminated,
    truncated,
    recipe,
):
    p = recipe["ppo"]
    advantages, returns = gae(
        rewards,
        old_values,
        next_values,
        terminated,
        truncated,
        p["gamma"],
        p["gae_lambda"],
    )
    advantage = torch.from_numpy(advantages.reshape(-1)).float()
    advantage = (advantage - advantage.mean()) / (advantage.std(unbiased=False) + 1e-8)
    target = torch.from_numpy(returns.reshape(-1)).float()
    old_log = torch.as_tensor(old_log_prob.reshape(-1), dtype=torch.float32)
    actions = torch.as_tensor(actions.reshape(-1), dtype=torch.long)
    count = len(actions)
    if count % p["minibatch_size"]:
        raise ValueError("Rollout is not divisible by the frozen minibatch size")
    metrics = []
    model.train()
    for _ in range(p["epochs"]):
        order = torch.randperm(count)
        for start in range(0, count, p["minibatch_size"]):
            ids = order[start : start + p["minibatch_size"]]
            dist, value = model.distribution(select_batch(batch, ids))
            new_log = dist.log_prob(actions[ids])
            policy_loss, ratio, log_ratio = clipped_policy_loss(
                new_log, old_log[ids], advantage[ids], p["clip_ratio"]
            )
            value_loss = (value - target[ids]).square().mean()
            entropy = dist.entropy().mean()
            loss = (
                policy_loss
                + p["value_coefficient"] * value_loss
                - p["entropy_coefficient"] * entropy
            )
            if not torch.isfinite(loss):
                raise FloatingPointError("Nonfinite PPO loss")
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            grad = torch.nn.utils.clip_grad_norm_(
                model.parameters(), p["max_grad_norm"], error_if_nonfinite=True
            )
            optimizer.step()
            if not all(torch.isfinite(v).all() for v in model.parameters()):
                raise FloatingPointError("Nonfinite updated weights")
            metrics.append(
                {
                    "loss": loss.item(),
                    "policy_loss": policy_loss.item(),
                    "value_loss": value_loss.item(),
                    "entropy": entropy.item(),
                    "grad_norm": grad.item(),
                    "approx_kl": ((ratio - 1) - log_ratio).mean().item(),
                    "clip_fraction": ((ratio - 1).abs() > p["clip_ratio"])
                    .float()
                    .mean()
                    .item(),
                }
            )
    return {
        **{k: float(np.mean([m[k] for m in metrics])) for k in metrics[0]},
        "max_grad_norm_observed": max(m["grad_norm"] for m in metrics),
        "optimizer_steps": len(metrics),
        "return_mean": float(returns.mean()),
    }
