# Search revision: development and held-out evaluation

Recorded 2026-10-25. **The preselected search improved held-out mean HP by 0.91 over the
heuristic; hierarchy added no observed benefit.** This does not complete phase two. The earlier
[negative baseline](PLANNING-RESULTS.md) remains part of the evidence.

All seven conditions used the same three starter encounters, development seeds
1–10 and policy seed 773. Search used the public-conditioned opening proposal,
eight particles, at most 512 opening attempts and 128 conditioning attempts.
Every condition won 30/30 battles. Final HP includes the normal victory heal;
the maximum is 80. No learned policy is involved.

| Condition | Depth | Search calls / decision | Mean final HP | Fallback / decisions | Total search calls |
| --- | ---: | ---: | ---: | ---: | ---: |
| Random | — | 0 | 59.40 | — | 0 |
| Heuristic | — | 0 | 76.53 | — | 0 |
| Flat, legacy value | 8 | 256 | 71.27 | 9 / 327 | 80,319 |
| Flat, legacy value | 32 | 256 | 77.97 | 0 / 413 | 94,545 |
| Flat, legacy value | 32 | 1,024 | 78.33 | 0 / 406 | 404,713 |
| Flat, HP-scale value | 32 | 1,024 | 78.57 | 5 / 408 | 401,577 |
| Hierarchical, HP-scale value | 32 | 1,024 | 78.57 | 5 / 408 | 401,577 |

At the same 256-call limit, greater depth improved mean HP by 6.70. Increasing
the budget at depth 32 improved HP by 0.37 while using about 4.3 times the total
search work. Changing leaf utility added 0.23 HP in this small development set;
the hierarchical variant added no observed HP benefit. These comparisons do not
establish which effect generalizes. Particle conditioning and initialization
are additional work, listed in the [machine-readable summary](SEARCH-V2-VALIDATION.json).

## Frozen selection

Following the preregistered ordering (outcomes, then HP, then work), select
`flat-hp32-1024` as the primary search condition. It ties the hierarchical
variant on HP and model work; keep the latter as the explicit hierarchy
ablation. Keep `flat-depth32-256` as the cheaper reference and retain random
and heuristic baselines. The [selected recipe](../config/phase2-search-selected.json)
evaluated all five on **2001–2030**, preregistered before development
selection and still unseen when the selection was written. Configuration
was committed at `f2bc4c7` before those runs; it was not revised using their results. Do not interpret UI wall-clock cutoffs as this
deterministic evaluation configuration.

Implementation `075f47b` produced the 210 development episodes on a shared AMD
EPYC 7T83 host without GPU use. Independent conditions ran concurrently; latency
is diagnostic, not an isolated hardware performance comparison. All 210 actor
traces and 15 complete policy traces passed re-execution. The updated full test
suite passed 168 tests with one existing dependency warning. Raw reports and
trace hashes are recorded in the public summary; raw traces remain local.

The subsequent evaluation-runner change partitions a frozen seed inventory by
`seeds[index::count]`. It does not change the policy or simulator. The union of
shards must contain every expected encounter/seed/condition exactly once;
missing, failed or duplicate cases cannot be silently discarded.

```bash
# Use a fresh output directory; commit the selection and implementation first.
.venv/bin/python scripts/benchmark_planning.py \
  --recipe config/phase2-search-selected.json --split heldout \
  --output artifacts/search-v2-heldout
```

The known limits remain: approximate particles can deplete, only one policy
seed is evaluated, wins saturate this starter inventory, and finite combat HP
does not establish full-act success. Actual screenshots and single-act control
remain separate deliverables in [the execution plan](PHASE2-EXECUTION.md).

## New held-out results

Each condition covers 90 battles (three encounters × seeds 2001–2030). All
90 won in every condition; no win-rate improvement is established.

| Condition | Mean final HP | Difference vs heuristic | Fallback / decisions | Decision p50 / p95 (ms) |
| --- | ---: | ---: | ---: | ---: |
| Random | 56.44 | −20.59 | — | 0.02 / 0.03 |
| Heuristic | 77.03 | — | — | 0.03 / 0.05 |
| Flat, legacy value, depth 32 / 256 | 78.08 | +1.04 | 9 / 1,263 | 260 / 487 |
| Preselected flat, HP value, depth 32 / 1,024 | 77.94 | +0.91 | 0 / 1,229 | 1,005 / 1,490 |
| Hierarchical, HP value, depth 32 / 1,024 | 77.94 | +0.91 | 0 / 1,229 | 1,004 / 1,486 |

The primary search had higher HP in 27 paired cases, equal HP in 52 and lower
HP in 11. This is a finite-sample descriptive result with one policy seed, not
statistical evidence of a general gain. The cheaper comparison was slightly
better on this split; increased compute did not generalize into better HP.
The 1,024-call variants spent 1,225,074 search steps plus 21,121 conditioning
steps and 2,514 initializations each. Timing overlaps independent evaluation
shards, live validation and browser activity on a shared host.

All **450 actor traces** and **27 complete policy traces** re-executed exactly.
Combined with development, that is 660 actor and 42 policy replays. Every
expected encounter/seed/condition appeared once, with verified report and
trace hashes. [Full held-out summary](SEARCH-V2-HELDOUT.json).

## Fresh original-game and UI checks

The selected flat configuration completed Nibbit, Slimes and Sludge Spinner at
seed 1, ending at 74, 80 and 77 HP. The same hierarchical configuration also
completed Nibbit at 74 HP. All **49 confirmed actions across four battles**
matched independent simulator execution; all four policy replays passed with
no fallback. These were non-saving debug experiments in profile 2 using the
previously installed Mod. No original-game images were captured. This is
broader smoke evidence, not full content coverage or a normal single-act run.

The dashboard now explicitly sends the selected proposal/value/depth/budget
with a 2-second interactive cutoff. Its full battle, manual override, pause,
goal termination and desktop/mobile replay checks passed. Original semantic
replay also passed with zero mutation requests. Python legacy defaults and the
old recipe remain available for historical reproduction. The earlier 60
original references plus one control probe passed re-audit; captures were not
rewritten. Local raw evidence is in `artifacts/phase2-v2/`.

Decision-boundary pixels and full single-act execution are the next gates.
Neither the four live battles nor a screenshot-free dashboard completes them.
