# Native compatibility corrections

The simulator remains derived from the pinned `evangambit/sts2` engine. Verified
local-game differences are recorded explicitly; they are not fixed by rewriting
captured states, removing comparison fields or changing a recorded battle's RNG.

## Nibbit Slice block in v0.107.1

Requirement established from a live A0 battle: after Nibbit's Slice finishes,
the enemy has 5 block. The seven-step dashboard capture and a subsequent read
agree; both show idle execution, with no enemy powers modifying block. The
pinned simulator instead grants 6 block unconditionally.

Read-only inspection of the installed game's `SliceBlock` getter and
`GetValueIfAscension` signature confirms a fallback value of 5, raised to 6 by
the ToughEnemies threshold. No game method is executed on Linux. These are
compatibility facts; the game implementation is not distributed with the lab.

The build must leave `vendor/` byte-identical to its pinned archive. Generate an
attributed copy of `EnemyAI.cs` with exactly the Nibbit Slice block expression
corrected, rejecting absent or duplicated context. Record the transformation,
original input, generated source and build script in the native manifest. Apply
the correct amount inside the existing block operation, preserving modifiers,
execution order and RNG. Do not alter observations to disguise wrong effects.

Regression checks must exercise actual simulator effects and replay the original
seven-step trace against a newly initialized simulator at the same declared seed.
That partial match alone is not a complete reference case. Keep all previous
builds, failed reports and raw captures; earlier performance and parity evidence
continues to identify its original build.

Local evidence: `artifacts/live-dashboard/20261023T080937865967/report.json`,
`artifacts/windows/nibbit-block-stability-20261023T081109970255.json`,
`artifacts/windows/nibbit-model-calls.json` and `nibbit-ascension-api.json`.
Private captures and game DLLs remain outside Git.

## Starter victory boundary

The same original battle reaches rewards on step 11 with 74 HP: the player had
68 HP before the winning Strike and Burning Blood restored 6. The standalone
arena API stops at combat victory with 68 HP. The pinned run-level reward code
already models this heal; the lab's arena path does not call that run lifecycle.

The lab terminal transition must include Burning Blood's capped six-point heal
once on victory, before exporting the terminal observation. Do not heal on loss,
truncation, ordinary observation, snapshot or restore. Use the native handle's
existing victory flag to prevent repeated payout. Keep reward choices and their
RNG outside this combat benchmark; do not invoke the full run reward generator.
This is an explicit lifecycle adaptation based on the original capture and the
attributed upstream `RunRewardGenerator.GenerateCombatRewards` behavior. It does
not read original-game HP or overwrite simulator state from a reference trace.

Evidence: `artifacts/live-dashboard/20261023T081506924270/report.json` and its
linked raw terminal capture. Old reports retain the missing-heal mismatch.

The seed-1 random-policy battle supplies the separate cleanup check: its winning
Strike starts with 5 player block; the reward capture has 0. Clear player block
at the same victory boundary, without clearing it early during combat. Evidence:
`artifacts/live-cases/20261023T082235837426/report.json`, step 17. This correction
changes the native build, so regenerate candidates and re-audit existing cases.
