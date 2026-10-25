# Phase-two execution: four ordered deliverables

User authorization: 2026-10-25, complete items 1, 2, 3 and 4 in the stated order.
The goal remains all four items; a working combat prototype alone is not completion.
The baseline checkpoint is `64f34eb`; historical evidence remains immutable.

## Completion evidence

1. **Reliable public-history sampling.** Diagnose rejection and depletion on the
   existing development inventory. Improve independent proposals without reading
   the acting environment's seed, snapshot, RNG or hidden order. Require exact
   public consistency of retained particles, deterministic policy-seed replay,
   bounded work and cleanup. Compare opening success, particle survival, fallback
   frequency and cost against v1 on identical recorded public histories. Target
   at most 5% depleted decision points on that finite development regression;
   this is an engineering gate, not a universal statistical guarantee.
2. **Better search decisions.** Compare rollout depth, leaf value and tactical
   goals separately at recorded model-call and belief-work budgets. Preserve
   negative results. Select settings only on development data; commit the
   implementation/configuration before evaluating a new preregistered split.
   Verify legality, noninterference, reproducibility and original-game execution.
   Report HP, outcomes, compute and fallback; do not call a failed comparison a
   gain or silently replace the intended search with a heuristic-only policy.
3. **Original-game decision images.** Capture the actual game viewport at a
   confirmed decision boundary, bind bytes to game instance/build, state token,
   run and decision, verify hashes, and show the association in live/replay UI.
   Reject stale/mismatched images. Synthetic image tests are not live evidence;
   verify an installed bridge and real Windows captures before completion.
4. **Single-act flow.** Add explicit map, reward, rest and shop observations and
   legal semantic actions, policies and trace/UI support. Integrate these with
   combat into an executable single-act controller, including endings and
   unsupported/unresolved-state handling. Test each decision family, preserve
   reference cases, and verify an end-to-end original-game act. A disconnected
   set of fixtures, a mock route or another starter battle cannot prove this.

All items require implementation, relevant tests, traceable evidence, current
handoff/status/provenance documents and reviewable commits. Remote delivery is
recorded separately and is not inferred from a local commit. Stage-three model
training is outside these four items.

## Sampling proposal contract (specified before new upstream inspection)

V1 rejects whole seeded openings, even for already public HP and hand values.
The proposed replacement constructs **independent hypothetical openings** from
the public opening and an independent proposal seed. It must never change an
acting environment or overwrite a recorded transition to make it agree.

- Create an independent starter arena using its own seed. Condition only public
  enemy opening HP within valid ranges, and public hand membership using the
  arena's actual starter-card instances. Randomize the remaining unknown order.
- Preserve enemy identities, latent AI state and initializer side effects from
  the independent arena. Reject any remaining public mismatch, including intent,
  powers, resources and known draw positions. No arbitrary state-deserialization
  interface is exposed to policy code.
- Perform any native conditioning through a new constructor/factory restricted
  to a fresh opening. Validate all inputs before mutation, publish only a world
  whose full public projection matches, and close failed proposals.
- Propagation still executes actual confirmed actions in independent worlds and
  rejects mismatched results. Do not patch post-transition HP, damage, powers or
  results from the observed game. Any later rejuvenation must likewise use only
  public history and disclose its additional model work.
- This conditioned proposal remains an approximation: a new independent RNG
  seed plus public constraints is not an exact posterior over game seeds. The
  report identifies its version and distinguishes it from the v1 rejection model.

Archive the native library and re-audit historical traces if a native factory is
added. That audit establishes unchanged execution behavior only; new policy or
single-act mechanics need fresh original-game evidence.
