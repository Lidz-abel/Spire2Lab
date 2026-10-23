# Controlled original-game scenarios

Status: the first staging build loaded in the original game, but its first live
initialization failed while creating the combat room. The mutable-encounter fix
has compiled and related checks pass; its Windows installation and successful
live initialization remain pending. No battle parity has been established.

The fixed phase-one benchmark remains Ironclad A0, floor 2, zero completed
combats, the ten-card starter deck, Burning Blood, no potions, 80/80 HP and
99 gold. A new profile's first natural battle was observed at floor 1. That run
supports a separate bridge probe and cannot enter the reference matrix.

## Required contract

A staging request specifies one supported encounter, one declared integer seed,
a unique request ID and the expected game-state token. The controller must:

1. Verify the current game release, DLL, Mod build and protocol before staging.
2. Operate only in the dedicated experiment profile, with the profile ID checked
   immediately before execution. Never delete profiles or change other saves.
3. Use the game's own run, encounter, card and combat APIs to construct the
   declared initial conditions. Record this as a debug-staged scenario, distinct
   from a naturally reached run.
   Resolve the canonical encounter into a fresh mutable game model before starting
   the run. Never pass a shared canonical model into combat-room creation.
4. Initialize named RNG streams from the declared seed before combat begins.
   Document the original game's stream seeding and the simulator's corresponding
   derivation. Never search seeds, copy simulator outcomes into the original,
   or overwrite states/RNG during a recorded battle to make a comparison pass.
5. Wait for an actual settled player decision. Validate all public opening
   fields and privately compare draw order and RNG provenance before recording.
6. Persist request, initialization provenance, failures and final opening capture.
   An interrupted setup must remain unresolved until inspected; never blindly
   retry a mutation. Repeating a request ID must not create another scenario.

Staging metadata must identify the actual floor, completed-combat count, seed,
stream initialization method, profile, encounter, character, inventory, game/Mod
hashes and initializer version. Raw RNG and draw order are verification data;
policies, the ordinary dashboard and Gym observations must not receive them.

## Validation sequence

Start with one Nibbit scenario and one fixed seed. Repeat its initialization to
check reproducibility, then play a complete battle and compare every decision
with an independently initialized simulator. Preserve the first mismatch.
Extend to Slimes and Sludge Spinner only after the first path is established.

Only complete, independently captured battles that pass the existing opening,
policy, trajectory and build checks may enter the 60-case matrix. Additional
boundary probes remain separately labeled. A successful setup or a single
matching action is not a full reference case.

## Implementation constraints and provenance

The current `debug_start_encounter` upstream endpoint can enter an encounter in
the current run. It does not by itself establish the benchmark's floor, inventory
or RNG initialization. It therefore cannot certify controlled setup.

Spire2Lab implements the staging contract and validation. Existing pinned
Mod plumbing remains attributed to `evangambit/STS2MCP`. API signatures and RNG
compatibility facts must be checked against the received local DLL. Record any
copied or adapted upstream implementation in `CODE-PROVENANCE.md`; inspection
alone is not a claim of independently implemented game mechanics.

The current draft spans `bridge/ScenarioContract.cs`, `bridge/McpMod.Scenario.cs`,
`sts2lab/scenarios.py` and `scripts/prepare_scenario.py`. It requests a non-saving
run in profile 2 and records explicit debug setup, including a noncombat history
anchor when needed and numeric run-stream initialization before entering combat.
The first live attempt created a non-saving run in profile 2, initialized the
declared numeric RNG streams, then failed before entering combat: the game's
`CombatRoom` rejected the canonical `NibbitsWeak` model with
`CanonicalModelException`. The failed request and raw state are preserved in
`artifacts/windows/scenario-20261023T071207228987.json` and its journal. No battle
was validated, and the failed setup must not be retried in its partly initialized
run. The model must be cloned through the game's `ToMutable()` API first.

The initial build compiled with no errors and one upstream nullable warning,
and its runtime fingerprint, main menu and profile 2 were verified after the
Windows installation. That did not establish correct scene initialization.
Install the corrected build after compilation and restart to the main menu before
another setup attempt. Compilation and synthetic tests cannot replace this check.

## Operator workflow

Install the current bridge bundle, restart the game and select experiment profile
2. Stay at the main menu with no run active. The configured SSH tunnel must reach
the running game. From the Linux repository root:

```bash
.venv/bin/python scripts/prepare_scenario.py --encounter nibbits-weak --seed 1
```

The tool verifies the local bundle and running game/Mod fingerprints, persists a
request journal, sends one setup request, and waits for its matching settled
opening. It compares that opening with an independently initialized simulator.
It does not play cards or finish a battle. This first live path remains unverified;
a successful compile or contract test is not a promised successful setup.

Every attempt writes a new private `artifacts/windows/scenario-*.json` report and
`.jsonl` journal. Keep failures. Exit code 0 means only the opening checks matched;
1 means failed, rejected, unresolved or mismatched; 130 records cancellation.
Neither successful setup nor opening agreement enters the 60-battle reference set.

If the result is `outcome_unknown`, use its actual report path to resume:

```bash
.venv/bin/python scripts/prepare_scenario.py --resume artifacts/windows/scenario-<timestamp>.json
```

Replace `<timestamp>` with the filename reported by the original attempt. If a
process terminated before writing the report, pass its `.jsonl` journal instead.
Resume sends GETs only and remains bound to the original process and build. A
restarted process, changed build or unrelated request cannot certify completion.
Do not submit another setup request to resolve a missing acknowledgment.

Contract checks use synthetic HTTP, synthetic files and the compiled C# input
parser without game DLLs. Run them with:

```bash
.venv/bin/python -m pytest -q tests/test_scenarios.py tests/test_scenario_contract.py tests/test_acceptance.py
```
