# Controlled original-game scenarios

Status: design in progress; no staging endpoint is implemented or game-verified.

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

Spire2Lab will implement the staging contract and validation. Existing pinned
Mod plumbing remains attributed to `evangambit/STS2MCP`. API signatures and RNG
compatibility facts must be checked against the received local DLL. Record any
copied or adapted upstream implementation in `CODE-PROVENANCE.md`; inspection
alone is not a claim of independently implemented game mechanics.

A new bridge build will require Windows installation and runtime verification.
Preserve the installed build and its manifest before producing a replacement.
Compilation and synthetic tests alone cannot establish that staging works.
