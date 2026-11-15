"""E1-specified public entity actor-critic; no environment or experiment metadata."""

import math

import numpy as np
import torch
from torch import nn
from torch.distributions import Categorical

from .rl_contract import FEATURES, FIELD_ORDER, prepare_observation
from .vocabulary import vocabulary


def tensor_batch(observations, dones=None):
    if not observations:
        raise ValueError("Empty observation batch")
    if dones is None:
        dones = [False] * len(observations)
    if len(dones) != len(observations):
        raise ValueError("Observation/boundary batch mismatch")
    prepared = [
        prepare_observation(o, episode_done=bool(d))
        for o, d in zip(observations, dones, strict=True)
    ]

    def stack(values):
        if isinstance(values[0], dict):
            return {k: stack([v[k] for v in values]) for k in values[0]}
        return torch.from_numpy(np.stack(values))

    return stack(prepared)


def select_batch(batch, indices):
    return {
        k: select_batch(v, indices) if isinstance(v, dict) else v[indices]
        for k, v in batch.items()
    }


class ActorCritic(nn.Module):
    def __init__(self, recipe):
        super().__init__()
        spec = recipe["network"]
        if (
            spec["architecture"] != "flat_public_context_shared_candidate_scorer_v1"
            or spec["context_hidden"] != [128, 128]
            or spec["candidate_hidden"] != [64]
            or spec["activation"] != "tanh"
            or spec["embedding_dim"] != 8
            or spec["recurrent"]
        ):
            raise ValueError("Unsupported network recipe")
        # Fixed category order also fixes seeded initialization order.
        self.embeddings = nn.ModuleDict(
            {
                name: nn.Embedding(
                    max(vocabulary().tables[name].values()) + 1, 8, padding_idx=0
                )
                for name in (
                    "cards",
                    "enemies",
                    "powers",
                    "relics",
                    "intents",
                    "actions",
                )
            }
        )
        self.widths = {
            name: shape[-1] - len(cats) + 8 * len(cats) + bool(cats)
            for name, (shape, cats, _) in FEATURES.items()
        }
        width = sum(
            math.prod(shape[:-1]) * self.widths[name]
            for name, (shape, _, _) in FEATURES.items()
        )
        self.context = nn.Sequential(
            nn.Linear(width, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh()
        )
        self.scorer = nn.Sequential(
            nn.Linear(128 + self.widths["hand"] + self.widths["enemies"] + 8 + 2, 64),
            nn.Tanh(),
            nn.Linear(64, 1),
        )
        self.value_head = nn.Linear(128, 1)

    def encode(self, batch):
        rows = {}
        for name in FIELD_ORDER:
            parts = [batch["numeric"][name]]
            for index, (_, category) in enumerate(FEATURES[name][1]):
                parts.append(
                    self.embeddings[category](batch["tokens"][name][..., index])
                )
            if name in batch["present"]:
                parts.append(batch["present"][name].unsqueeze(-1).float())
            rows[name] = torch.cat(parts, dim=-1)
        context = self.context(
            torch.cat([rows[k].flatten(1) for k in FIELD_ORDER], dim=-1)
        )
        return context, rows

    def value(self, batch):
        context, _ = self.encode(batch)
        value = self.value_head(context).squeeze(-1)
        if not torch.isfinite(value).all():
            raise FloatingPointError("Nonfinite value")
        return value

    def forward(self, batch):
        mask = batch["action_mask"]
        if not mask.any(dim=1).all():
            raise ValueError("All-zero action mask: value-only observation")
        context, rows = self.encode(batch)
        refs = batch["action_references"]
        linked = []
        for col, field in enumerate(("hand", "enemies")):
            index = refs[..., col]
            selected = rows[field].gather(
                1, index.clamp(min=0).unsqueeze(-1).expand(-1, -1, self.widths[field])
            )
            linked.append(selected * (index >= 0).unsqueeze(-1))
        candidates = torch.cat(
            [
                context.unsqueeze(1).expand(-1, mask.shape[1], -1),
                *linked,
                self.embeddings["actions"](batch["action_tokens"]),
                (refs >= 0).float(),
            ],
            dim=-1,
        )
        logits = self.scorer(candidates).squeeze(-1)
        value = self.value_head(context).squeeze(-1)
        if not torch.isfinite(logits).all() or not torch.isfinite(value).all():
            raise FloatingPointError("Nonfinite policy/value output")
        return logits.masked_fill(~mask, -torch.inf), value

    def distribution(self, batch):
        logits, value = self(batch)
        return Categorical(logits=logits), value


def make_optimizer(model, recipe):
    return torch.optim.Adam(
        model.parameters(),
        lr=recipe["ppo"]["learning_rate"],
        eps=recipe["ppo"]["adam_eps"],
    )
