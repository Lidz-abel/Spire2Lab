"""Explicit-reset environment workers and public-only, time-major rollouts."""

import multiprocessing as mp
import os
import random
import resource
import time
import traceback

import numpy as np

from .gym_env import CombatEnv
from .rl_contract import validate_transition


class CaseScheduler:
    def __init__(self, recipe, seed, state=None):
        self.recipe = recipe
        self.rng = random.Random(seed)
        self.cursor = 0
        if state:
            self.rng.setstate(state["rng"])
            self.cursor = state["cursor"]

    def next(self):
        start, end = self.recipe["environment_seed_ranges_inclusive"]["train"]
        case = {
            "encounter": self.recipe["encounters"][
                self.cursor % len(self.recipe["encounters"])
            ],
            "seed": self.rng.randint(start, end),
            "episode_id": self.cursor,
        }
        self.cursor += 1
        return case

    def state(self):
        return {"rng": self.rng.getstate(), "cursor": self.cursor}


class EnvironmentSlot:
    def __init__(self):
        self.env = CombatEnv()
        self.observation = None
        self.case = None

    def reset(self, case):
        self.case = dict(case)
        self.observation, _ = self.env.reset(
            seed=case["seed"], options={"encounter": case["encounter"]}
        )
        return self.observation

    def step(self, action):
        result = self.env.step(action)
        record = validate_transition(self.observation, action, result)
        self.observation = record.next_observation
        return record, {**self.case, "step_index": self.env.attempts - 1}

    def close(self):
        self.env.close()


def _worker(connection):
    slot = EnvironmentSlot()
    try:
        connection.send(("ok", {"pid": os.getpid()}))
        while True:
            command, value = connection.recv()
            if command == "close":
                slot.close()
                connection.send(
                    (
                        "ok",
                        {
                            "pid": os.getpid(),
                            "peak_rss_kib": resource.getrusage(
                                resource.RUSAGE_SELF
                            ).ru_maxrss,
                        },
                    )
                )
                return
            if command == "reset":
                result = slot.reset(value)
            elif command == "step":
                result = slot.step(value)
            else:
                raise ValueError("Unknown worker command")
            connection.send(("ok", result))
    except BaseException:
        try:
            connection.send(("error", traceback.format_exc()))
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        slot.close()
        connection.close()


class EnvironmentPool:
    def __init__(self, workers, timeout=30):
        if workers not in (1, 2, 4):
            raise ValueError("E2 supports 1/2/4 workers")
        self.workers, self.timeout = workers, timeout
        self.slots = [EnvironmentSlot()] if workers == 1 else []
        self.processes, self.connections = [], []
        self.observations = [None] * workers
        self.cases = [None] * workers
        self.steps = [0] * workers
        self.cleanup = []
        if workers > 1:
            context = mp.get_context("spawn")
            try:
                for _ in range(workers):
                    parent, child = context.Pipe()
                    process = context.Process(target=_worker, args=(child,))
                    process.start()
                    child.close()
                    self.processes.append(process)
                    self.connections.append(parent)
                for connection in self.connections:
                    self._receive(connection)
            except BaseException:
                self.close()
                raise

    def _receive(self, connection):
        if not connection.poll(self.timeout):
            raise TimeoutError("Environment worker timed out")
        status, data = connection.recv()
        if status != "ok":
            raise RuntimeError(data)
        return data

    def reset(self, index, case):
        if self.slots:
            obs = self.slots[index].reset(case)
        else:
            self.connections[index].send(("reset", case))
            obs = self._receive(self.connections[index])
        self.observations[index] = obs
        self.cases[index] = dict(case)
        self.steps[index] = 0

    def step(self, actions):
        if len(actions) != self.workers:
            raise ValueError("Action/worker count mismatch")
        if self.slots:
            replies = [self.slots[0].step(int(actions[0]))]
        else:
            for connection, action in zip(self.connections, actions, strict=True):
                connection.send(("step", int(action)))
            replies = [self._receive(c) for c in self.connections]
        for i, (record, _) in enumerate(replies):
            self.observations[i] = record.next_observation
            self.steps[i] += 1
        return replies

    def active_episodes(self):
        return [
            {**case, "steps": steps}
            for case, steps in zip(self.cases, self.steps)
            if case
        ]

    def close(self):
        for slot in self.slots:
            slot.close()
        for process, connection in zip(self.processes, self.connections):
            reply = {}
            try:
                if process.is_alive():
                    connection.send(("close", None))
                    reply = self._receive(connection)
            except (OSError, EOFError, RuntimeError, TimeoutError):
                pass
            process.join(timeout=3)
            forced = process.is_alive()
            if forced:
                process.terminate()
                process.join(timeout=3)
            if process.is_alive():
                process.kill()
                process.join(timeout=3)
            connection.close()
            self.cleanup.append(
                {
                    **reply,
                    "pid": process.pid,
                    "exitcode": process.exitcode,
                    "forced": forced,
                    "alive": process.is_alive(),
                }
            )
        self.processes, self.connections = [], []
        return self.cleanup


def collect(model, pool, scheduler, steps, budget, run_id, policy_update):
    import torch
    from .rl_model import tensor_batch

    observations, next_observations, audit, episodes = [], [], [], []
    fields = {
        k: []
        for k in (
            "actions",
            "log_prob",
            "values",
            "next_values",
            "rewards",
            "terminated",
            "truncated",
        )
    }
    latencies = []
    started = time.perf_counter()
    model.eval()
    with torch.no_grad():
        for _ in range(steps):
            before = list(pool.observations)
            tick = time.perf_counter()
            dist, values = model.distribution(tensor_batch(before))
            actions = dist.sample()
            log_prob = dist.log_prob(actions)
            latencies.append(1000 * (time.perf_counter() - tick))
            budget.reserve(pool.workers, run_id)
            replies = pool.step(actions.tolist())
            budget.confirm(pool.workers, run_id)
            records = [r for r, _ in replies]
            done = [r.terminated or r.truncated for r in records]
            after = [r.next_observation for r in records]
            next_values = model.value(tensor_batch(after, done)).numpy()
            observations.extend(before)
            next_observations.extend(after)
            for key, value in (
                ("actions", actions.numpy()),
                ("log_prob", log_prob.numpy()),
                ("values", values.numpy()),
                ("next_values", next_values),
                ("rewards", [r.reward for r in records]),
                ("terminated", [r.terminated for r in records]),
                ("truncated", [r.truncated for r in records]),
            ):
                fields[key].append(value)
            for i, (record, meta) in enumerate(replies):
                audit.append({**meta, "worker": i, "policy_update": policy_update})
                if done[i]:
                    episodes.append(
                        {
                            **meta,
                            "worker": i,
                            "steps": meta["step_index"] + 1,
                            "outcome": (
                                "won"
                                if record.reward == 1
                                else "lost" if record.reward == -1 else "truncated"
                            ),
                            "return": record.reward,
                            "final_hp": int(after[i]["player"][0]),
                        }
                    )
                    # Bootstrap was computed from the actual final obs above.
                    pool.reset(i, scheduler.next())
    return {
        "observations": observations,
        "next_observations": next_observations,
        "audit": audit,
        "episodes": episodes,
        **{k: np.asarray(v) for k, v in fields.items()},
        "sampling_seconds": time.perf_counter() - started,
        "inference_batch_ms": latencies,
    }
