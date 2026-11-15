# Phase two: observable-history planning

Started 2026-10-24. The first-stage checkpoint is `f9faf0a`; its original-game
acceptance remains evidence for that checkpoint. Development uses the
`phase2/search-hierarchy` branch. Phase two is not yet accepted.

## Deliverables and order

| ID | Deliverable | Required evidence |
| --- | --- | --- |
| P2-01 | Planning contract and fixed evaluation recipe | Information boundary, budgets, provenance, development/held-out split |
| P2-02 | History-conditioned sampled worlds | No access to the acting environment; consistent public histories; resource cleanup and explicit depletion |
| P2-03 | Budgeted combat search | Reproducible root-action estimates, real simulation counts, timeout/fallback behavior, no real-game mutations |
| P2-04 | Tactical hierarchy and decision inspection | Persistent goals, termination reasons, durations, manual-override accounting, search records in live/replay UI |
| P2-05 | Baselines and ablations | Fixed budgets; random, heuristic, flat search and hierarchical search; paired outcome/HP and compute reports |
| P2-06 | Original-game search and decision-boundary images | Fresh search-policy live captures, correctly associated screenshots, install/runtime verification if the Mod changes |
| P2-07 | Incremental single-act decisions | Explicit content inventory; map/reward/rest/shop contracts and reference cases before support claims |
| P2-08 | Reproduction and delivery | Reproducible configurations, evidence limitations, documentation and verified GitHub synchronization |

P2-02 through P2-05 start with the already verified starter inventory. This is
the first execution unit, not a reduction of phase two to single-battle search.
Screenshots and single-act support remain separate acceptance gates. RL training
belongs to phase three.

## Information boundary specified before implementation

The planner receives only the declared encounter, public `Observation`, policy
configuration, its own seed, and confirmed public action/result history. It must
not receive the acting environment, an exact checkpoint from it, raw Mod data,
the environment seed, or hidden pile/RNG state. A test must reproduce identical
decisions from the same public history even when the real hidden state differs.

Sampled worlds are independent simulator instances. At the opening, accept
independent prior samples only when their public state matches. Hand order and
decision-local references are immaterial to this matching; card attributes,
multiset counts, target identity/order, public powers, intent and known draw
positions remain constraints. Equivalent duplicate actions map by their visible
card properties and living target position, not native IDs.

For each confirmed transition, propagate sampled worlds using the actual action
(including manual overrides), reject inconsistent observations and replenish
from surviving worlds. Hidden resampling may only start from these independent
particles, never from the acting environment. Validate the existing resampling
primitive before relying on it. This is an explicitly approximate belief model,
not a claim of an exact Bayesian posterior or a full-history game model.

All initialization, propagation and search work has explicit limits. Depletion
or budget exhaustion uses a recorded public-observation heuristic fallback;
never reconstruct a world from privileged data or invent a search result.
No unresolved game action updates belief or creates a training transition.

## First search and hierarchy

Use a root-action bandit with bounded observable-policy rollouts across sampled
worlds. Record each candidate's visits, value estimate and the exact forward
model calls spent. Call this rollout search, not full information-set MCTS.
Rollout actions may depend on simulated observations but never on private state.
Use the same sampled scenarios across candidates where the budget permits.
Search estimates are utility estimates, not calibrated win probabilities.

The first hierarchy selects observable tactical goals: survive the current
turn, focus an enemy, or progress combat. A goal persists across atomic actions
until its stated condition, turn boundary or maximum duration; terminal and
manual-intervention boundaries are recorded explicitly. Goal shaping affects
planning utility only. The real `terminal-win-v1` reward remains unchanged.

Search records include algorithm/configuration version, search seed, actual
model calls, sampled-world count, depletion/fallback reason, candidate visits
and estimates, goal ID/parent decision, and elapsed time. Simulated branches
never enter the real action ledger as executed actions.

## Evaluation commitments

- Development seeds 1–10; held-out seeds 1001–1010 remain separate from tuning.
- Compare random-v1, heuristic-v1, flat rollout search and hierarchical rollout
  search on the same three encounters, initial conditions and declared seeds.
- Freeze search settings before held-out evaluation. Record the freeze commit;
  preserve negative results and failed attempts rather than retuning the split.
- Report wins/losses/truncations, terminal HP, decisions, initialization and
  belief work, search calls, decision latency, fallback frequency and hardware.
- The starter matrix has a baseline win-rate ceiling. Remaining HP and compute
  are useful diagnostics; neither establishes single-act or learned-agent gains.
- Deterministic model-call budgets are the reproducibility baseline. Wall-time
  cutoffs protect interactive operation and must be reported when they fire.
- Reuse the phase-one raw captures to audit unchanged behavior after integration;
  new policies or mechanics need their own live evidence before claims expand.

## Provenance

The belief, search, hierarchy, evaluation and presentation code will be authored
in this project. The current simulator and Mod retain their upstream ownership.
Method references and any adapted implementation are recorded separately in
[CODE-PROVENANCE.md](../CODE-PROVENANCE.md). Writing this specification does not
claim that any of the planned capabilities has already been implemented.
