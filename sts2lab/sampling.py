"""Finite, process-isolated sampling measurements; no learning or game-parity claim.

Each worker loads and warms the simulator before the parent releases a shared
barrier. Every layout executes the same cases. Public transition hashes verify
that scheduling does not change the observed trajectory. Hashing is excluded
from per-decision latency but included in total sampling throughput.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import math
import multiprocessing as mp
from multiprocessing.connection import wait
import os
from pathlib import Path
import platform
import resource
import subprocess
import time

from .contracts import PROTOCOL_VERSION, canonical_json, semantic_state
from .policies import Policy
from .simulator import CONFIG, ROOT, Simulator


@dataclass(frozen=True)
class EpisodeSpec:
    encounter: str
    seed: int
    policy: str
    repetition: int = 0
    policy_seed: int = 773

    @property
    def case_id(self):
        return f"{self.encounter}:{self.seed}:{self.policy}:{self.repetition}"


def inventory(split="development", episodes_per_case=5):
    if split not in ("development", "heldout") or episodes_per_case < 1:
        raise ValueError("Invalid split or episode repetition count")
    return [
        EpisodeSpec(encounter, seed, policy, repetition)
        for repetition in range(episodes_per_case)
        for encounter in CONFIG["encounters"]
        for seed in CONFIG[f"{split}_seeds"]
        for policy in ("random", "heuristic")
    ]


def _episode(spec):
    latencies = []
    with Simulator(spec.encounter, spec.seed) as env:
        obs = env.observe()
        chain = hashlib.sha256(canonical_json(semantic_state(obs)).encode())
        policy = Policy(spec.policy, spec.policy_seed)
        while obs.outcome == "ongoing":
            before = obs
            started = time.perf_counter_ns()
            proposal = policy.decide(before)
            result = env.step(proposal.selected_action_id, before.decision_id)
            latencies.append((time.perf_counter_ns() - started) / 1_000_000)
            obs = result.observation
            # Indices are local to this observation; UUID epochs never enter hashes.
            action_index = next(
                i
                for i, a in enumerate(before.legal_actions)
                if a.action_id == proposal.selected_action_id
            )
            chain.update(
                canonical_json(
                    {
                        "action_index": action_index,
                        "observation": semantic_state(obs),
                        "reward": result.reward,
                        "terminated": result.terminated,
                        "truncated": result.truncated,
                    }
                ).encode()
            )
        return {
            **asdict(spec),
            "case_id": spec.case_id,
            "steps": env.sequence,
            "outcome": obs.outcome,
            "final_hp": obs.player.hp,
            "trajectory_sha256": chain.hexdigest(),
            "library_sha256": env.manifest["library_sha256"],
        }, latencies


def _worker(connection, start, cases):
    try:
        _episode(cases[0])  # warm-up is not a measured episode
        connection.send({"kind": "ready"})
        start.wait()
        cpu_before = resource.getrusage(resource.RUSAGE_SELF)
        records, latencies = [], []
        for case in cases:
            record, samples = _episode(case)
            records.append(record)
            latencies.extend(samples)
        usage = resource.getrusage(resource.RUSAGE_SELF)
        connection.send(
            {
                "kind": "result",
                "records": records,
                "latencies_ms": latencies,
                "peak_rss_kib": usage.ru_maxrss,
                "cpu_seconds": usage.ru_utime
                + usage.ru_stime
                - cpu_before.ru_utime
                - cpu_before.ru_stime,
            }
        )
    except BaseException as exc:
        connection.send({"kind": "error", "error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


def _collect(connections, expected, deadline):
    pending = list(connections)
    messages = []
    while pending:
        ready = wait(pending, timeout=max(0, deadline - time.monotonic()))
        if not ready:
            raise TimeoutError(
                f"Sampling workers timed out while waiting for {expected}"
            )
        for connection in ready:
            try:
                message = connection.recv()
            except EOFError as exc:
                raise RuntimeError("Sampling worker exited without a result") from exc
            if message.get("kind") != expected:
                raise RuntimeError(message.get("error", "Unexpected worker response"))
            messages.append(message)
            pending.remove(connection)
    return messages


def _percentile(values, probability):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(probability * len(ordered)) - 1)]


def measure_round(cases, workers, timeout=120):
    if not cases or not 1 <= workers <= len(cases) or timeout <= 0:
        raise ValueError("Need cases, 1..len(cases) workers, and a positive timeout")
    if len({s.case_id for s in cases}) != len(cases):
        raise ValueError("Duplicate case identifiers")
    ctx = mp.get_context("spawn")
    start = ctx.Event()
    processes, connections = [], []
    launch_time = time.perf_counter()
    deadline = time.monotonic() + timeout
    try:
        for slot in range(workers):
            receive, send = ctx.Pipe(duplex=False)
            connections.append(receive)
            process = ctx.Process(
                target=_worker, args=(send, start, cases[slot::workers])
            )
            try:
                process.start()
            finally:
                send.close()
            processes.append(process)
        _collect(connections, "ready", deadline)
        sampling_started = time.perf_counter()
        start.set()
        replies = _collect(connections, "result", deadline)
        sampling_seconds = time.perf_counter() - sampling_started
        for process in processes:
            process.join(timeout=max(0, deadline - time.monotonic()))
            if process.exitcode != 0:
                raise RuntimeError("Sampling worker did not exit cleanly")
        total_seconds = time.perf_counter() - launch_time
    finally:
        # Applies to startup errors, timeouts, interrupted runs and normal completion.
        for process in processes:
            if process.is_alive():
                process.terminate()
        for process in processes:
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
        for connection in connections:
            connection.close()
    records = sorted(
        (r for reply in replies for r in reply["records"]), key=lambda r: r["case_id"]
    )
    latencies = [value for reply in replies for value in reply["latencies_ms"]]
    steps = sum(record["steps"] for record in records)
    if steps != len(latencies) or {r["case_id"] for r in records} != {
        s.case_id for s in cases
    }:
        raise RuntimeError("Sampling worker returned an incomplete workload")
    return {
        "workers": workers,
        "episodes": len(records),
        "steps": steps,
        "startup_and_warmup_seconds": sampling_started - launch_time,
        "sampling_seconds": sampling_seconds,
        "total_seconds": total_seconds,
        "decisions_per_second": steps / sampling_seconds,
        "end_to_end_decisions_per_second": steps / total_seconds,
        "decision_ms_p50": _percentile(latencies, 0.5),
        "decision_ms_p95": _percentile(latencies, 0.95),
        "decision_ms_p99": _percentile(latencies, 0.99),
        "worker_peak_rss_kib": [reply["peak_rss_kib"] for reply in replies],
        "sum_worker_peak_rss_kib": sum(reply["peak_rss_kib"] for reply in replies),
        "worker_cpu_seconds": sum(reply["cpu_seconds"] for reply in replies),
        "worker_cleanup_ok": True,
        "records": records,
    }


def verify_reproducibility(rounds):
    if not rounds:
        raise ValueError("No sampling rounds")
    baseline = rounds[0]["records"]
    for index, measured in enumerate(rounds[1:], 1):
        if measured["records"] != baseline:
            raise ValueError(f"Sampling trajectories differ in round {index}")
    return {"passed": True, "rounds": len(rounds), "cases_per_round": len(baseline)}


def hardware_info():
    cpu = Path("/proc/cpuinfo").read_text()
    model = next(
        (
            line.split(":", 1)[1].strip()
            for line in cpu.splitlines()
            if line.startswith("model name")
        ),
        "unknown",
    )
    memory = next(
        line
        for line in Path("/proc/meminfo").read_text().splitlines()
        if line.startswith("MemTotal:")
    )

    def cgroup_value(name):
        path = Path("/sys/fs/cgroup") / name
        return path.read_text().strip() if path.exists() else None

    return {
        "os": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "cpu_model": model,
        "logical_cpus": os.cpu_count(),
        "affinity_cpu_count": len(os.sched_getaffinity(0)),
        "host_memory_kib": int(memory.split()[1]),
        "visible_cgroup_cpu_max": cgroup_value("cpu.max"),
        "visible_cgroup_memory_max": cgroup_value("memory.max"),
        "load_average_at_start": list(os.getloadavg()),
    }


def benchmark(
    *,
    workers=(1, 2, 4),
    repeats=3,
    episodes_per_case=5,
    split="development",
    timeout=120,
):
    if repeats < 1 or len(set(workers)) != len(workers) or 1 not in workers:
        raise ValueError(
            "Use unique worker counts including 1, and at least one repeat"
        )
    cases = inventory(split, episodes_per_case)
    host = hardware_info()
    rounds = []
    # Rotate layouts between repeats to reduce a fixed measurement-order bias.
    for repeat in range(repeats):
        order = list(workers[repeat % len(workers) :]) + list(
            workers[: repeat % len(workers)]
        )
        for count in order:
            measured = measure_round(cases, count, timeout)
            measured["repeat"] = repeat
            rounds.append(measured)
    proof = verify_reproducibility(rounds)
    baseline = (
        sum(r["decisions_per_second"] for r in rounds if r["workers"] == 1) / repeats
    )
    summary = []
    for count in workers:
        group = [r for r in rounds if r["workers"] == count]
        throughput = sum(r["decisions_per_second"] for r in group) / repeats
        summary.append(
            {
                "workers": count,
                "mean_decisions_per_second": throughput,
                "min_decisions_per_second": min(
                    r["decisions_per_second"] for r in group
                ),
                "max_decisions_per_second": max(
                    r["decisions_per_second"] for r in group
                ),
                "speedup_over_one_worker": throughput / baseline,
                "max_sum_worker_peak_rss_kib": max(
                    r["sum_worker_peak_rss_kib"] for r in group
                ),
            }
        )
    paths = [
        "sts2lab/sampling.py",
        "sts2lab/simulator.py",
        "sts2lab/policies.py",
        "sts2lab/contracts.py",
        "scripts/benchmark_sampling.py",
        "config/phase1.json",
        "requirements.lock",
    ]
    return {
        "schema_version": "sampling-benchmark-v1",
        "scope": "simulator_only",
        "local_game_parity": "not_verified",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "hardware": host,
        "config": CONFIG,
        "protocol_version": PROTOCOL_VERSION,
        "split": split,
        "episodes_per_case": episodes_per_case,
        "repeats": repeats,
        "start_method": "spawn",
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "working_tree_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        ),
        "source_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in paths
        },
        "measurement": {
            "sampling_throughput": "From warm-worker release through receiving all results; includes reset, policy, simulation, public trajectory hashing and IPC; excludes startup, warm-up and shutdown.",
            "end_to_end_throughput": "Includes spawn, source checks, warm-up, measured work, IPC and shutdown; counts measured decisions only.",
            "decision_latency": "Policy.decide + Simulator.step; excludes reset, hash instrumentation, IPC and rendering; nearest-rank percentiles.",
            "memory": "Each worker lifetime peak RSS from Linux getrusage, including warm-up. Sum of peaks is not simultaneous physical memory; shared pages can be counted multiple times. Parent excluded.",
            "repeats": "Timing replicates of the same seeded cases, not additional independent evaluation seeds.",
            "contention": "Current shared host; no exclusive CPU allocation or CPU pinning.",
        },
        "reproducibility": proof,
        "summary": summary,
        "rounds": rounds,
    }
