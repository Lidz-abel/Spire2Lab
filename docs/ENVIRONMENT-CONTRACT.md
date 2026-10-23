# Environment boundary

This contract belongs to Spire2Lab. It defines how the controller can use a
backend without importing its native handles, HTTP commands or game classes.
The mechanics engine and Mod foundation remain the attributed upstream projects
listed in [code provenance](../CODE-PROVENANCE.md).

## Shared operations

An environment exposes `observe`, `step`, `close`, its backend name, build
manifest, encounter, seed (or `None` when unknown), sequence and capabilities.
`observe` returns the versioned `Observation`; `step` takes an action ID bound to
a decision ID and returns `StepResult`. Both backends accept an optional request
ID; the controller handles duplicate requests, and the game bridge also uses it
to identify the corresponding settled result. Native steps do not provide their
own request cache.

`step` and `close` can return immediately or return an awaitable. The controller
uses the same call signature and awaits when necessary. Unsupported operations
raise `UnsupportedCapability` before any backend action. Capabilities describe
operations, not parity certification or measured performance.

| Operation | Native simulator | Original game |
| --- | --- | --- |
| `observe()` | Public semantic state | Last confirmed public semantic state |
| `step(action_id, decision_id, request_id=...)` | Synchronous | Asynchronous; waits for acknowledgment and settled state |
| `reset(encounter=..., seed=...)` | Fresh declared initial state; invalidates old decision IDs | Refused by the ordinary environment |
| `snapshot()` / `restore(snapshot)` | Exact in-process checkpoint; caller closes checkpoints | Refused |
| `sample_world(search_seed)` | Isolated clone with resampled hidden state | Refused |
| `close()` | Releases native handle | Closes transport, without taking a game action |

Native reset must construct a valid replacement before releasing the old state;
an invalid encounter or seed must leave the current environment intact. Restoring
a snapshot must not change that snapshot or another branch. A capability claim
must be backed by a callable implementation and tests.

## Branch provenance

Each native environment exposes immutable `branch_provenance` metadata with a
unique `branch_id`, `parent_branch_id`, `parent_decision_id` and `operation`.
The branch ID is the existing decision-ID epoch. A new environment or successful
reset is a root with no parent. `snapshot` and `sample_world` create a new ID and
refer to the source branch and decision at the time of cloning. `restore`
creates another new ID whose parent is the checkpoint being restored. Advancing
a source, resetting it or closing it must not rewrite a descendant's provenance.

Provenance belongs to the environment and trace header, never `Observation` or
training tensors. It contains no RNG state, resampling seed or hidden card order.
Older trace headers without this additive field remain readable; their ancestry
is unavailable and must not be reconstructed by guessing from a run name.
An original-game environment exposes `None`: it cannot be cloned. The controller
continues to create root sessions only; simulated branches do not execute game
commands or enter an original-game trace. This is branch bookkeeping, not a
search implementation or a history-conditioned belief model.

The existing `Decision.policy` already carries the baseline version, such as
`heuristic-v1` or `random-v1`; preserve that field when recording proposals.

## Training transition boundary

A starter-benchmark terminal win is observed after Burning Blood's capped
six-point heal and the expiry of combat block. The standalone arena adapter
applies this boundary once on the winning transition, before exporting state.
Loss, truncation, observation and checkpoint
operations never award victory healing. The run reward-choice workflow remains
outside this benchmark. See [native compatibility](NATIVE-COMPATIBILITY.md) for
the original-game evidence, upstream behavior reference and build transformation.

A confirmed original-game step requires an empty game action queue, an idle
action executor with no current action, empty player play piles, and no hand
play animation. After those conditions become true, require an unchanged state
token for at least 250 ms. A briefly unchanged public state while an action is
still executing is not settled. Readiness facts are private bridge metadata;
they never enter policy observations. Keep a request unresolved while busy,
poll with GETs only, and do not manufacture a training transition on timeout.

An action outside the declared Gym action space raises before taking a step.
A masked action inside that space is a no-op with zero reward,
`invalid_action=True` and `training_transition=False`; it must be filtered from
training data. It counts toward the wrapper's attempt limit, without advancing
the underlying simulator or changing its decision ID.

Reaching the attempt limit yields `truncated=True`, not a fabricated loss.
A genuine win/loss on the final allowed action yields `terminated=True` and
`truncated=False`, with the versioned terminal reward. Either ending zeros the
returned action mask and requires reset before another step. Invalid attempts
can make the wrapper truncate before the simulator; the simulator's still-live
state must not be relabeled as a terminal game outcome.

## Initialization and information boundary

Controlled original-game setup is a separate operator workflow, described in
[scenario staging](SCENARIO-STAGING.md). It is not an ordinary environment reset
and must not silently start a new game while a policy is running. The staging
tool's initial-state and RNG checks remain private verification data.

Policies consume only `Observation`. Raw bridge states, RNG seeds/counters and
hidden draw order stay in private verification captures. The dashboard consumes
the same public observations plus controller decisions and execution records.
Card catalog values are attributed reference data, not measurements taken from
the game. Native snapshots and debug exports must not become a policy oracle;
`sample_world` is not yet a full history-conditioned belief model.

The controller's backend factory still selects the native simulator or original
adapter. Native ABI calls and numeric-ID translation are confined to adapters.
Protocol 0.3 removes `Card.native_id`; Gym encoding reads the public observation
and the project vocabulary without consulting native name tables. Content facts
and the mechanics engine still have upstream sources. Independent bindings, game
rules and Mod replacement remain separate migration work.

## Content vocabulary migration contract

The current semantic protocol is `0.3.0`; its `Card` records retain game-facing
`type_id` strings and remove `native_id`. The benchmark's deck and relics use
semantic identifiers too. Its version changes to `ironclad-starter-v2` solely
for that representation change: character, inventory, floor, seeds, encounter
scope and combat conditions must remain identical.

Training encoding `combat-entities-v3` uses explicit project-assigned categorical
tokens from `config/content-v1.json`. Tokens are scoped by category; 0 is padding,
positive tokens are fixed, and unknown content raises an error. Never derive a
token from an upstream enum or silently map unknown content to padding. Freeze
the vocabulary version and SHA-256 with Gym observations and experiment metadata.
Adding content requires reviewed appended tokens and a declared version change.

Native IDs are still used privately inside adapters to call the existing engine.
This migration changes ownership of the public interface and tensor vocabulary,
not ownership of the underlying game mechanics or content facts. The initial
vocabulary is limited to the current starter scenarios and includes their status
cards, enemies, powers, relic and intent/action types.

Validation compares independently executed pre/post-migration simulator
trajectories on the existing development and held-out seed lists, excluding only
the removed ID and protocol-version fields. Do not search seeds or modify game
rules to obtain agreement. Preserve old traces and encodings as old-version data:
they remain readable as raw records but are refused by current semantic replay
until explicitly migrated. Never relabel old training tensors as version 3.

### Visible intent projection

The original v0.107.1 Nibbit exposes both Attack and Defend for its Slice move.
The pinned engine already applies Slice's block, but omits that displayed Defend
entry from `SecondaryIntent`. The lab's read-only native export must expose the
missing intent for the currently selected Slice move, without changing the engine
state, applying effects, reading future RNG or dropping original-game fields.
The public Defend magnitude remains unavailable (`None`); no hidden block amount
is supplied to policies. Other moves and existing secondary intents are preserved.
This correction changes observed trajectories and the native build fingerprint;
earlier simulator reports remain evidence for their recorded build only.

The local migration check matched 120 fixed simulator battles and 2,180 decisions
across the existing development and held-out seed lists, three encounters and two
baseline policies. It compared public observations (excluding only protocol version
and removed card IDs), selected actions, rewards and termination flags. Private
evidence is in `artifacts/vocabulary-migration-before.json` and `-after.json`.
This is finite simulator regression evidence; it does not establish original-game
parity, improve a learned policy or replace the 60 original reference battles.

## Evidence and limits

Native tests exercise real local simulator behavior, including invalid reset,
decision invalidation and branch isolation. Original capability refusal tests
use a transport that must receive no requests. Transport tests use synthetic
responses and do not prove real-game correctness. Full original-game UI, battle,
randomness and reference-matrix acceptance remain separately required.
