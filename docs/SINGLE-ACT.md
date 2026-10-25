# Single-act control contract

Specified 2026-10-25 before inspecting new upstream run/action implementations.
This is deliverable 4 of [the ordered plan](PHASE2-EXECUTION.md), following the
verified decision-image gate. A completed starter battle is not a single act.

## Scope and completion

Build an executable Ironclad / ascension 0 / single-player first-act controller
for the pinned original game. Start a normal, seeded, non-saving experimental
run in profile 2. Preserve the game's actual starter inventory, map generation,
events, rewards, combat and boss. Do not jump between debug rooms, reseed RNG
after startup, grant resources, rewrite card effects or assemble a mock route.
Do not overwrite an existing saved run. Stopping the experiment must preserve
its evidence and distinguish loss, interruption and successful act completion.

Required primary decision families are map, reward, rest and shop, integrated
with combat. The normal route also needs explicit event, treasure, card-choice
and proceed boundaries where encountered. A complete acceptance run must reach
and defeat the first-act boss through ordinary game actions. Preserve distinct
real examples for every required family, including a real shop operation and a
rest/upgrade operation; separate probes cannot be presented as one continuous
act. Report route, content inventory, unsupported cases, overrides and failures.

Full-game simulator parity and learning are not silently assumed. The current
search model is certified only for the starter combat inventory. The run layer
must expose which decisions actually use search, which use a public-observation
heuristic, and which cannot be supported. A run heuristic is a baseline, not a
trained hierarchical agent or proof of planning gains across an entire act.

## Public observations and actions

Use a new explicit `single-act-v1` contract so old combat traces retain their
meaning. Every observation has a decision ID, act/floor, current phase, public
player/deck/relic/potion state, legal semantic actions and unavailable fields.
Keep the raw bridge response, environment seed, hidden draw order and RNG state
outside policy inputs. Stable content names are game facts, not original art or
rules authored by this project.

| Phase | Required public input | Semantic actions |
| --- | --- | --- |
| Map | Current position, visible nodes/edges and selectable destinations | Choose one legal destination |
| Reward | Available rewards, quantities and whether they are claimable | Claim reward, enter card offer, skip/proceed |
| Card offer | Visible offered cards with identity, upgrade and public text | Choose offered card or legal skip |
| Rest | Visible enabled options, HP, deck upgrade eligibility | Rest, select upgrade, proceed if offered |
| Shop | Visible goods/services, prices, gold, availability | Buy available affordable item, remove a card, leave |
| Event/treasure | Visible text/options and enabled state | Choose visible option or open/claim/proceed |
| Card selection | Visible selectable cards, selection bounds, confirmation state | Select/deselect card, confirm or cancel if legal |
| Combat | Public hand/piles/intent/resources, playable flags and legal targets | Play card, end turn, use a supported potion/choice |
| Terminal | Observed death or explicit first-act boss completion | No further gameplay action |

IDs and transport indexes are decision-local; no position from an earlier state
may be used after the expected state token changes. Do not infer price, legality,
upgrade state, boss completion or a hidden event outcome from a label alone.
Missing or unrecognized required data produces an explicit unsupported state.
The first supported content inventory must be recorded from actual interfaces;
generic parsing is not proof that every mechanic is supported.

## Execution and decisions

The bridge must bind every supported mutating run command to an expected token
and unique request ID, deduplicate identical requests and reject conflicts or
stale decisions before execution. Poll after one submission; an uncertain reply
is reconciled by reads, never blind resubmission. Serialize experiment owners.
The existing combat protocol stays available and cannot concurrently act on the
same game while an act controller owns it.

The settlement condition must model real decision boundaries. A player-choice
prompt may intentionally suspend an executing game action; support it only with
an explicit stable-choice gate. Never declare an arbitrary busy animation done.
Action acceptance, intermediate choices, confirmed transitions and terminal
outcomes remain distinct. Pending or unsupported states stop automatic actions.
Pause prevents the next action; manual overrides are legal, recorded actions.

Run decisions return scored legal candidates, an explanation and a persistent
strategic goal with a termination reason. The baseline can prefer safe routes,
HP recovery and explicit deck upgrades while preserving a fixed recipe. Combat
search is invoked only where its model/input contract is valid; every heuristic
or unsupported branch is visible. Planning utility never overwrites real reward.
Use an explicitly versioned act reward: success +1, observed death −1, otherwise
0; interruption/step limit is truncation, never a synthetic death or victory.

## Records, UI and acceptance

Record confirmed public observations/actions, request IDs, private capture
references, decision images, policy/goal reports, source/build fingerprints and
termination in a hash-chained run trace. Images use the same strict association
as [decision images](DECISION-IMAGES.md). The act page displays phase, floor,
public choices, selected action, actual changes and original pixels. Replaying
the full run must issue no game actions or screenshot capture requests.

Test legality and target/index mapping, public-data filtering, route continuity,
affordability, card choices, goal boundaries, stale/deduplicated/uncertain
commands, pause/manual override, unsupported states, image binding and terminal
recognition. Label synthetic tests separately. Freeze a run recipe before real
acceptance; retain the complete run and any failed attempts. Only the observed
continuous original act plus family coverage and replay verification completes
this deliverable. Publish factual summaries, not private game assets or saves.

## Interface inspection findings

Pinned `sts2mcp-v107` revision `18bc23be` exposes the needed screen families,
but its state builder automatically opens normal/fake merchant inventories and
treasure chests during reads. Remove these three side effects in the generated
build copy, with exact-match source hooks; retain the vendor files unchanged.
Opening a shop or chest becomes a guarded, recorded action. This is a derived
bridge adjustment, not independent game logic. A closed inventory must not
publish goods as though the player had opened it.

The existing `lab_settled` combat gate remains strict. Add a separate act
boundary that explicitly identifies a visible, interactive card-choice prompt
when a game action is waiting for input. Neither a stationary state hash nor an
arbitrary enabled button alone is sufficient. Screenshot requests must opt into
that boundary; old combat clients keep their original settlement contract.

## Implemented checkpoint, pending original-game acceptance

The controller is available at `/act` on the phase-two server. The normal game
must be at its settled main menu in profile 2, with the current laboratory Mod
installed. Keep the existing SSH tunnel connected. The old combat laboratory
must have archived its original-game session before the act controller starts.

```bash
# From this checkout, using the already prepared native/reference environment:
.venv/bin/python -m uvicorn sts2lab.server:app --host 127.0.0.1 --port 8766
```

Open the forwarded phase-two address with `/act`. **Start experimental act**
creates a normal seeded run without saving. **One decision** executes one
guarded action; **Run** repeats the frozen baseline; **Pause** prevents the next
action. **Reconcile** only reads after an uncertain response. An unavailable
image clears the image panel. **Archive** closes recording without clicking the
game. **Replay** reads the stored trace and images and disables control buttons.

Current modules:

- `bridge/ActContract.cs`, `bridge/McpMod.Act.cs`: normal startup, guarded choice
  catalogue, instance-local request ledger and explicit card-choice boundary.
- `sts2lab/act_contracts.py`, `act_bridge.py`: public whitelist projection,
  decision-local action mapping and one-submit/read-reconcile transport.
- `sts2lab/act_policy.py`: fixed public-screen heuristic, persistent room goals,
  visible-map scoring and explicit zero-model-call decisions.
- `sts2lab/act_runtime.py`, `act_server.py`, `web/act.*`: ownership, controls,
  private captures, hash-chained act traces, images and cached live/replay views.

`artifacts/act-runs`, `artifacts/act-raw` and `artifacts/act-images` are private,
ignored output. New traces use `single-act-v1`; legacy combat traces remain 0.3.
Do not feed a normal-run trace to the starter-only simulator replay adapter.

The [acceptance recipe](../config/single-act-v1.json) lists three seeds in attempt
order, a 1,200-action cap, the policy and required continuous-route coverage.
Freeze the implementation before attempting them. A loss, unsupported screen,
transport failure or incomplete family coverage is retained, not relabeled as
success. This is an execution/observability gate, not a win-rate benchmark.

The baseline reads only the public observation. Card ranks, route preferences,
the 72% resting threshold and numeric text estimates are fixed heuristics.
Text numbers are only ranking estimates, never substituted for game damage or
legality. Fake merchants, bundle/relic-choice overlays, Crystal Sphere and
unrecognized selection modes stop the controller. Generic support for a screen
is not verification of every card/event on that screen. No normal act has yet
been accepted at this checkpoint.

The bridge's visible-card clickability check reads `_isClickable` from the
actual `NCardHolder` hierarchy. Read-only assembly call/field metadata confirmed
that its input handler uses that field. Shop opening disables the proceed
button, so closing the inventory is a separate recorded action; the policy
remembers closing it and proceeds instead of reopening forever. No game method
was executed during this metadata inspection.

## Offline acceptance audit

After recording, audit the hash chain, every private capture's SHA-256 and
instance/build/startup binding, the public projection, one matching submitted
request per transition, route continuation, deterministic policy decisions and
stored image associations. The auditor must not contact the game. A passing
primary run needs observed boss combat and act completion, no unresolved action
or manual override, successful shop payment/inventory change and an observed
rest heal or card upgrade. Missing images are reported and fail the complete
visual-run gate. Failed and incomplete runs remain useful diagnostic records;
neither a compiled Mod nor a synthetic record establishes original acceptance.

```bash
.venv/bin/python scripts/audit_act.py artifacts/act-runs/RUN_ID.jsonl \
  --output artifacts/single-act/RUN_ID-audit.json
```

Replace `RUN_ID` with the archived run ID from the dashboard. A structurally
valid but incomplete attempt writes a failing report and exits 1. A changed
capture, invalid transition or policy mismatch raises an error; preserve that
failure alongside the trace. The current source fingerprints must match the
run's frozen implementation before deterministic policy replay is claimed.
