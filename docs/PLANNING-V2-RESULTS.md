# Search revision: development selection

Recorded 2026-10-25. **Development results improved; new held-out and live
validation are pending.** This does not complete phase two. The earlier
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
will evaluate all five on **2001–2030**, preregistered before development
selection and still unseen when this selection was written. No settings will
be selected using those results. Do not interpret UI wall-clock cutoffs as this
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
