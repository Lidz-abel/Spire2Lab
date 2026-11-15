"""E2 mathematics/engineering tests. Synthetic updates are not agent-training evidence."""

import copy
import json
import random

import numpy as np
import pytest
import torch

from sts2lab.gym_env import CombatEnv
from sts2lab.rl_contract import PublicTransition, load_recipe
from sts2lab.rl_io import (
    Budget,
    load_checkpoint,
    rng_state,
    save_checkpoint,
    state_digest,
    restore_rng,
)
from sts2lab.rl_model import ActorCritic, make_optimizer, tensor_batch
from sts2lab.rl_ppo import clipped_policy_loss, gae, update
from sts2lab.rl_rollout import CaseScheduler, EnvironmentPool, collect
from sts2lab.rl_evaluate import selection_key


@pytest.fixture
def observation():
    env = CombatEnv()
    try:
        obs, _ = env.reset(seed=3)  # old development case; no learned-policy stepping
        yield obs
    finally:
        env.close()


@pytest.fixture
def recipe():
    return load_recipe()


@pytest.fixture
def model(recipe):
    torch.set_num_threads(1)
    torch.manual_seed(41)
    return ActorCritic(recipe)


def test_mask_probabilities_and_candidate_permutation(model, observation):
    batch = tensor_batch([observation])
    dist, value = model.distribution(batch)
    assert torch.equal(
        dist.probs[~batch["action_mask"]],
        torch.zeros_like(dist.probs[~batch["action_mask"]]),
    )
    assert dist.probs.sum().item() == pytest.approx(1)
    permutation = np.arange(64)[::-1].copy()
    changed = copy.deepcopy(observation)
    changed["actions"] = changed["actions"][permutation]
    changed["action_mask"] = changed["action_mask"][permutation]
    shuffled, shuffled_value = model(tensor_batch([changed]))
    logits, _ = model(batch)
    torch.testing.assert_close(shuffled, logits[:, permutation], rtol=0, atol=0)
    torch.testing.assert_close(shuffled_value, value, rtol=0, atol=0)
    samples = dist.sample((100,))
    assert batch["action_mask"][0, samples].all()


def test_only_end_turn_and_terminal_value(model, observation):
    end_turn = next(row.copy() for row in observation["actions"] if row[0] == 2)
    observation["actions"][:] = 0
    observation["action_mask"][:] = 0
    observation["actions"][0] = end_turn
    observation["action_mask"][0] = 1
    dist, value = model.distribution(tensor_batch([observation]))
    assert dist.log_prob(torch.tensor([0])).item() == 0
    assert dist.entropy().item() == 0
    observation["actions"][:] = 0
    observation["action_mask"][:] = 0
    terminal = tensor_batch([observation], [True])
    torch.testing.assert_close(model.value(terminal), value, rtol=0, atol=0)
    with pytest.raises(ValueError, match="All-zero"):
        model.distribution(terminal)


def test_seed_never_enters_network_batch(observation):
    observation["seed"] = 10000
    with pytest.raises(ValueError, match="private"):
        tensor_batch([observation])


def test_gae_hand_calculation_resets_and_workers():
    rewards = np.array([[0, 0], [1, 0], [0, -1]], dtype=np.float32)
    values = np.array([[0.2, 0.1], [0.3, 0.2], [0.4, 0.3]], dtype=np.float32)
    next_values = np.array([[0.3, 0.9], [99, 0.3], [0.5, 99]], dtype=np.float32)
    term = np.array([[False, False], [True, False], [False, True]])
    trunc = np.array([[False, True], [False, False], [False, False]])
    advantage, returns = gae(rewards, values, next_values, term, trunc, 1.0, 1.0)
    np.testing.assert_allclose(
        advantage, [[0.8, 0.8], [0.7, -1.2], [0.1, -1.3]], atol=1e-6
    )
    np.testing.assert_allclose(returns, [[1, 0.9], [1, -1], [0.5, -1]], atol=1e-6)


def test_ppo_clip_both_advantage_signs():
    log_prob = torch.tensor([1.5, 1.5]).log().requires_grad_()
    loss, _, _ = clipped_policy_loss(
        log_prob, torch.zeros(2), torch.tensor([1.0, -1.0]), 0.2
    )
    assert loss.item() == pytest.approx(0.15)
    loss.backward()
    assert log_prob.grad[0] == 0  # clipped positive advantage
    assert log_prob.grad[1] > 0


def synthetic_update(model, recipe, observation, optimizer=None):
    count = 128
    batch = tensor_batch([observation] * count)
    with torch.no_grad():
        dist, value = model.distribution(batch)
        actions = dist.sample()
        old_log = dist.log_prob(actions)
    if optimizer is None:
        optimizer = make_optimizer(model, recipe)
    metrics = update(
        model,
        optimizer,
        batch,
        actions.numpy().reshape(count, 1),
        old_log.numpy().reshape(count, 1),
        value.numpy().reshape(count, 1),
        np.ones((count, 1), dtype=np.float32),
        np.zeros((count, 1), dtype=np.float32),
        np.ones((count, 1), dtype=bool),
        np.zeros((count, 1), dtype=bool),
        recipe,
    )
    return optimizer, metrics


def test_synthetic_update_changes_parameters_keeps_padding_zero(
    model, recipe, observation
):
    before = state_digest(model.state_dict())
    _, metrics = synthetic_update(model, recipe, observation)
    assert state_digest(model.state_dict()) != before
    assert metrics["max_grad_norm_observed"] > 0
    assert all(np.isfinite(value) for value in metrics.values())
    for embedding in model.embeddings.values():
        assert not embedding.weight[0].any()


def test_checkpoint_optimizer_rng_and_corruption(tmp_path, model, recipe, observation):
    optimizer, _ = synthetic_update(model, recipe, observation)
    scheduler = CaseScheduler(recipe, 41)
    scheduler.next()
    path = tmp_path / "checkpoint.pt"
    compatible = {"test_only": "synthetic"}
    save_checkpoint(
        path,
        model,
        optimizer,
        recipe,
        compatible,
        scheduler.state(),
        {"updates": 1, "valid_steps": 128},
        [],
        [],
        {},
        {"test": True},
    )
    expected_rng = state_digest(rng_state())
    expected_opt = state_digest(optimizer.state_dict())
    restored_model = ActorCritic(recipe)
    restored_opt = make_optimizer(restored_model, recipe)
    restored = load_checkpoint(path, restored_model, restored_opt, compatible)
    assert state_digest(rng_state()) == expected_rng
    assert state_digest(restored_opt.state_dict()) == expected_opt
    assert state_digest(restored_model.state_dict()) == state_digest(model.state_dict())
    assert restored["counters"] == {"updates": 1, "valid_steps": 128}
    resumed_scheduler = CaseScheduler(recipe, 999, restored["scheduler"])
    assert [scheduler.next() for _ in range(5)] == [
        resumed_scheduler.next() for _ in range(5)
    ]
    # Same saved learner RNG produces the same next synthetic minibatch update.
    state = rng_state()
    synthetic_update(model, recipe, observation, optimizer)
    restore_rng(state)
    synthetic_update(restored_model, recipe, observation, restored_opt)
    assert state_digest(model.state_dict()) == state_digest(restored_model.state_dict())
    with pytest.raises(ValueError, match="compatibility"):
        load_checkpoint(path, restored_model, restored_opt, {"test_only": "other"})
    with path.open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        load_checkpoint(path, restored_model, restored_opt, compatible)


def test_budget_survives_restart_and_unconfirmed_reservation(tmp_path):
    path = tmp_path / "ledger.jsonl"
    first = Budget(path, cap=5)
    try:
        first.reserve(3, "failure")
        first.confirm(2, "failure")
        with pytest.raises(BlockingIOError):
            Budget(path, cap=5)
    finally:
        first.close()
    second = Budget(path, cap=5)
    try:
        assert (second.charged, second.valid) == (3, 2)
        second.reserve(2, "resume")
        with pytest.raises(ValueError, match="exhausted"):
            second.reserve(1, "retry")
    finally:
        second.close()


def test_scheduler_training_only_and_reproducible(recipe):
    first, second = CaseScheduler(recipe, 41), CaseScheduler(recipe, 41)
    cases = [first.next() for _ in range(20)]
    assert cases == [second.next() for _ in range(20)]
    assert all(10000 <= case["seed"] <= 10999 for case in cases)
    assert [c["encounter"] for c in cases[:3]] == recipe["encounters"]


def test_collector_uses_final_value_before_reset(tmp_path, observation, recipe):
    class FakeModel:
        def eval(self):
            pass

        def distribution(self, batch):
            logits = torch.zeros_like(
                batch["action_mask"], dtype=torch.float32
            ).masked_fill(~batch["action_mask"], -torch.inf)
            return torch.distributions.Categorical(logits=logits), self.value(batch)

        def value(self, batch):
            return batch["numeric"]["player"][:, 3]

    class FakePool:
        workers = 1
        observations = [observation]

        def step(self, actions):
            before = self.observations[0]
            after = copy.deepcopy(before)
            after["player"][3] = 2
            after["action_mask"][:] = 0
            self.observations = [after]
            return [
                (
                    PublicTransition(before, actions[0], 0.0, after, False, True),
                    {
                        "step_index": 0,
                        "episode_id": 0,
                        "seed": 3,
                        "encounter": "nibbits-weak",
                    },
                )
            ]

        def reset(self, i, case):
            self.observations = [copy.deepcopy(observation)]

    budget = Budget(tmp_path / "synthetic-budget.jsonl")
    try:
        data = collect(
            FakeModel(),
            FakePool(),
            CaseScheduler(recipe, 41),
            2,
            budget,
            "synthetic",
            0,
        )
        np.testing.assert_allclose(data["values"], 1)
        np.testing.assert_allclose(data["next_values"], 2 / 3)
        assert data["truncated"].all() and not data["terminated"].any()
        assert not data["next_observations"][0]["action_mask"].any()
        assert data["observations"][1]["action_mask"].any()
    finally:
        budget.close()


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_environment_workers_development_scripted_step_cleanup(workers):
    # Fixed end_turn, not model sampling/training. Does not spend E2 learning budget.
    pool = EnvironmentPool(workers)
    try:
        for index in range(workers):
            pool.reset(
                index, {"encounter": "nibbits-weak", "seed": 3, "episode_id": index}
            )
        actions = [
            int(np.flatnonzero(o["actions"][:, 0] == 2)[0]) for o in pool.observations
        ]
        replies = pool.step(actions)
        assert all(not r.terminated and not r.truncated for r, _ in replies)
        assert all(meta["step_index"] == 0 for _, meta in replies)
        assert len({meta["episode_id"] for _, meta in replies}) == workers
    finally:
        cleanup = pool.close()
    assert all(
        not c["alive"] and not c["forced"] and c["exitcode"] == 0 for c in cleanup
    )


def test_validation_selection_never_drops_errors():
    good = {"error": 0, "win_rate": 0.9, "mean_final_hp_all_cases": 70}
    assert selection_key(good, 100) > selection_key(good, 200)
    with pytest.raises(ValueError):
        selection_key({**good, "error": 1}, 100)
