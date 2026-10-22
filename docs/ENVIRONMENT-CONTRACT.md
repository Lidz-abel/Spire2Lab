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
adapter. Native ABI calls are confined to `simulator.py`, but content coupling
remains: `Card.native_id` exposes an upstream numeric ID, and `gym_env.py` reads
the simulator's upstream name tables to encode entities. A project-owned content
vocabulary and a versioned observation/encoding migration are still needed to
finish this boundary. Independent bindings, game rules and Mod replacement are
separate migration work, not capabilities established by this interface.

## Evidence and limits

Native tests exercise real local simulator behavior, including invalid reset,
decision invalidation and branch isolation. Original capability refusal tests
use a transport that must receive no requests. Transport tests use synthetic
responses and do not prove real-game correctness. Full original-game UI, battle,
randomness and reference-matrix acceptance remain separately required.
