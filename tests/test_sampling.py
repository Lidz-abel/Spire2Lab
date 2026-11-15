import copy
import multiprocessing as mp
import pytest

from sts2lab.sampling import EpisodeSpec, measure_round, verify_reproducibility


def test_seeded_trajectories_survive_process_layout_and_repeat():
    cases = [
        EpisodeSpec(encounter, seed, policy)
        for encounter, seed, policy in (
            ("nibbits-weak", 1, "random"),
            ("slimes-weak", 2, "heuristic"),
            ("sludge-spinner", 3, "random"),
        )
    ]
    rounds = [measure_round(cases, workers) for workers in (1, 2, 2)]
    assert verify_reproducibility(rounds)["passed"]
    for result in rounds:
        assert result["worker_cleanup_ok"]
        assert result["steps"] > result["episodes"]
        assert result["total_seconds"] >= result["sampling_seconds"] > 0
        assert result["decision_ms_p99"] >= result["decision_ms_p50"] > 0
        assert result["sum_worker_peak_rss_kib"] > 0
    corrupted = copy.deepcopy(rounds)
    corrupted[1]["records"][0]["trajectory_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="trajectories differ"):
        verify_reproducibility(corrupted)
    corrupted[1]["records"].pop()
    with pytest.raises(ValueError, match="trajectories differ"):
        verify_reproducibility(corrupted)


def test_worker_failure_releases_all_children():
    existing = {p.pid for p in mp.active_children()}
    with pytest.raises(RuntimeError, match="outside the phase-one support"):
        measure_round([EpisodeSpec("invalid-encounter", 1, "heuristic")], 1)
    assert {p.pid for p in mp.active_children()} == existing


def test_worker_startup_timeout_releases_all_children():
    existing = {p.pid for p in mp.active_children()}
    with pytest.raises(TimeoutError):
        measure_round([EpisodeSpec("nibbits-weak", 1, "heuristic")], 1, timeout=0.00001)
    assert {p.pid for p in mp.active_children()} == existing
