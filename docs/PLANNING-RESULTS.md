# Starter planning evaluation

Implementation frozen at `2f36503` before held-out evaluation. Recorded 2026-10-24. **The current search baseline does not outperform the heuristic baseline.** Phase two remains in progress.

The same three starter encounters, 10 development seeds and 10 held-out seeds were used. Each row contains 30 battles per split. All configurations won all 30; win rate is saturated. These are simulator experiments, not training results.

| Policy | Search calls / decision | Development final HP | Held-out final HP | Held-out fallback decisions | Held-out decision p50 / p95 (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0 | 76.53 | 76.50 | 0 / 416 | 0.03 / 0.04 |
| hierarchical | 64 | 72.90 | 71.53 | 121 / 354 | 61.96 / 364.69 |
| hierarchical | 256 | 71.93 | 71.67 | 129 / 348 | 216.88 / 632.80 |
| random | 0 | 59.40 | 57.50 | 0 / 588 | 0.02 / 0.03 |
| rollout | 64 | 72.70 | 71.53 | 121 / 354 | 62.00 / 368.20 |
| rollout | 256 | 72.20 | 71.67 | 129 / 346 | 216.33 / 638.11 |

Final HP includes the normal Burning Blood victory heal and is bounded by 80. The paired encounter/seed inventory is identical across policies. There is one policy seed (773); no confidence intervals or broad generalization claim are made. Flat search is the hierarchy ablation; 64 versus 256 calls is the compute ablation. Neither more search nor the fixed tactical goals established a gain here.

## Settings and measurement

- CPU: **AMD EPYC 7T83 64-Core Processor**; 128 logical CPUs visible, 128 in the process affinity; no GPU used. Runs are sequential on a shared Linux host, Python 3.12.3.
- Search: 8 target particles, at most 512 opening attempts and 128 conditioning attempts, rollout depth 8, UCB coefficient 0.7, at most 3 actions per goal. No wall-clock cutoff in this comparison.
- Budget counts forward-model steps inside search. Belief initializations and conditioning calls are additional costs, recorded separately in the JSON summary.
- Decision latency includes policy computation and belief work, excluding actor execution, rendering and trace writes. It includes fallback decisions; it is not a search-only latency measure. Browser/regression activity overlapped portions of the shared-host run.
- Full recipe and reproduction commands: [planning guide](PLANNING.md#reproduce-the-comparison). Output directories are immutable per attempt.

## What passed

- **360 / 360** recorded simulator trajectories re-executed without differences; **24 / 24** selected complete search-policy traces reproduced choices, candidate values/visits, goals and fallback reports. Timing is excluded from exact replay.
- **152 tests** passed, including hidden-state noninterference, native resource cleanup, budgets, manual-override feedback, goal accounting and responsive pause during search. One existing dependency deprecation warning remains.
- Desktop and mobile UI checks passed: search report, manual override, pause, full battle, terminal goal and replay with zero mutation requests.
- The unchanged **60 phase-one original references plus one boundary probe** passed re-audit on the new branch. This is historical compatibility evidence.
- A **fresh original-game hierarchical-search battle** also passed: Nibbit, seed 1, 256-call budget, depth 8, nine confirmed actions, win at 68 HP, no heuristic fallback. Every original state matched an independently executed simulator; policy replay reproduced all nine decisions. It used the existing verified Mod and a non-saving debug scenario in experiment profile 2. No original-game images were captured.

## What needs work

Slimes is the main belief bottleneck: strict rejection must match several public enemy attributes and the opening hand simultaneously, and surviving particles can still deplete after a transition. The fallback is intentional and visible, but it means many reported search-policy actions are heuristic actions. A particle count is not an effective sample size. Limited rollout depth and fixed utility also remain hypotheses to test; this experiment does not identify a unique cause of the HP deficit.

Next, improve public-state-conditioned proposals and measure particle survival on development cases; then evaluate rollout/value and goal ablations separately. The 1001–1010 results are now visible. Do not tune against them while continuing to call them untouched held-out data; preregister a new split for a new iteration.

One original search battle is a smoke check, not broad live-policy certification. Decision-boundary game screenshots, incremental single-act support, independent phase-two reproduction and remote delivery remain outstanding. See [phase-two status](../PHASE2-STATUS.json).

## Evidence and failures

[Machine-readable summary](PHASE2-VALIDATION.json) records all case outcomes, work counts, trace hashes, build bindings and report hashes. Full raw traces, game captures and local logs remain in ignored `artifacts/`; they are not shipped with the repository. A public summary cannot turn a fresh clone into a verified installation.

The initial hidden-state test selected a random resample with the same hidden order and correctly failed its fixture check; the retained fixture now verifies a genuinely different hidden order. The first complete test run failed because the PowerShell executable path omitted `bin/`; correcting the test environment produced 152 passing tests. The first historical audit refused vendor symlinks outside the worktree; copying the pinned sources into the isolated worktree satisfied the existing containment check. Original failures were retained, and no policy/utility tuning occurred after the evaluation freeze.
