# Original-game validation

The live reference campaign runs against Steam public build `23811903`, release
`v0.107.1`. Its acceptance scope is deliberately finite: Ironclad A0, the starter
deck and Burning Blood, no potions, 80/80 HP, 99 gold, floor 2, and the three
encounters in [the benchmark configuration](../config/phase1.json).

**Local technical acceptance passed on 2026-10-23:** 60/60 required battles,
one additional loss/control probe and all nine boundary categories. The
[versioned summary](PHASE1-VALIDATION.json) records case and source fingerprints;
[project status](../PHASE1-STATUS.json) tracks remaining remote delivery. The required matrix is **60 independent complete battles**: three
encounters, development seeds 1–10, and two baseline policies. Additional probes
cover boundary behavior without replacing any of those battles. Held-out seeds
1001–1010 are not used in this campaign. This is environment validation, not an
evaluation of a trained agent.

## What a passing case means

Each case starts a new, explicitly debug-staged, non-saving run in experiment
profile 2. [Scenario preparation](SCENARIO-STAGING.md) checks the game and Mod
fingerprints, declared initial conditions, private initialization provenance and
settled opening. Seed selection is fixed before observing results.

The platform then records one request per decision and waits for confirmed
settlement. Its policy uses player-visible observations only. A separate
simulator runs the same semantic actions; the first difference stops that case.
Raw captures, request records and failed attempts remain available locally.
Neither future states nor RNG streams are overwritten during a battle to force
agreement.

After a natural win or loss, an immutable copy of the complete reference trace
is independently replayed again. The acceptance audit checks capture hashes,
build/source fingerprints, policy behavior, required cases and boundary coverage.
The active index is updated only after all registered cases pass those checks.
Earlier comparisons remain bound to the simulator build that produced them.

The comparison profile is `starter-live-observables-v1`. It compares observed
combat state, semantic cards, legal actions and terminal outcome. It excludes
catalog-derived printed card values, hidden RNG, hidden draw order, localization
and fields unavailable after combat. See [the contract](ENVIRONMENT-CONTRACT.md)
and [`parity.py`](../sts2lab/parity.py) for the exact projection. Passing this
matrix does not establish full-game parity or complete hidden-RNG equivalence.

## Live execution and browser boundaries

On 2026-10-23, a separate 12-step original-game probe passed these checks:

| Check | Observed behavior |
| --- | --- |
| Deliberately lost action response | The real game received one Strike request; its response was discarded by the test transport. The dashboard entered an unknown-outcome state and blocked further execution. |
| Reconciliation | GET requests recovered the resulting state and recorded exactly one transition, without another game POST. |
| Duplicate and stale requests | Repeating the request at the lab API returned the cached result. A new request carrying the old decision was refused. Neither sent another game action. |
| Automatic execution and pause | Pausing during execution allowed the current action to finish and prevented the next automatic action. |
| Manual override and loss | Overrides were marked in the trace. Repeated end-turn decisions reached a real loss at 0 HP, without a victory heal. |
| Read-only replay and layout | First/last-step replay sent no game action; desktop and narrow-screen browser checks completed without JavaScript errors. |
| Trace export | The browser-downloaded archive matched the server ledger byte for byte, retained a valid hash chain and contained all 12 transitions. Download and replay issued no mutating browser requests. |

The response loss was **injected**, not a naturally observed network outage. Game
states and actions were real. Twelve recorded transitions correspond to twelve
game action POSTs. The loss trace matched independent simulator re-execution and
was registered separately as `probe:live-loss-recovery`; it does not count toward
the 60-case matrix. It supplies the ninth required coverage category, `lost`.

The private report is
`artifacts/live-boundaries/20261023T085145678089/report.json`. Its request journal,
reference/candidate traces and browser captures are retained beside it. These
files contain local experiment data and are not distributed in Git.
The subsequent read-only download check is recorded in `download-check.json`
in the same directory.

## Corrections established by live evidence

The campaign exposed a premature bridge confirmation, a missing secondary
intent, Nibbit's A0 block amount, and arena victory cleanup/healing differences.
The earlier failed captures remain unchanged. The bridge now waits for idle game
execution before its stability window, and explicit
[native compatibility corrections](NATIVE-COMPATIBILITY.md) address the finite
simulator differences. These corrections do not make the upstream engine an
independently authored game implementation; [provenance](../CODE-PROVENANCE.md)
records the boundary.

## Reproduction and evidence access

On the operator checkout containing the private evidence, recompute the gate:

```bash
.venv/bin/python scripts/audit_acceptance.py
```

Missing or invalid evidence produces exit code 1. A fresh clone intentionally
does not inherit the operator's local verification status. The gate binds to
the actual files and current build, not this document's prose.

At source commit `4f8447b`, the primary checkout passed 133 tests. A separately
installed environment on the same host was upgraded and rebuilt: 132 tests
passed, with one optional PowerShell check skipped. Its 300 simulator episodes
(60 cases repeated five times, 4,875 decisions) matched the primary build's
public trajectories. Native binary hashes differed; this establishes behavioral
reproduction for those cases, not byte-for-byte builds or a second-machine test.

The same source passed trajectory checks across 1, 2 and 4 workers, three timing
repeats, 2,700 episodes and 43,875 decisions. Timing overlapped live capture and
part of a native build on a shared host, so it is not an isolated performance
claim. Evidence paths and versions are recorded in the project status; earlier
reports remain separate.
