# Card 04 — Alternative explanations and ranking (optional card)

**Provenance:** upstream executables from `method-layer` (`365669b`): `branch_set.py`, `preference_free_rank.py`, `rank_detector.py`. All stdlib, all with documented limitations. Status: upstream executable; this card adapts their procedures to study assessment. **Optional** — run when the publication admits multiple candidate explanations, not as a mandatory pass.

## 1. `branch_set` — keep the alternatives alive

The failure mode this prevents: a study's discussion section collapses to one favored explanation at intake, and every later analysis runs inside it. Rules carried over unchanged:

- When N candidate explanations fit one result, **priority rises**; the cheapest discriminator runs first, not the most central one.
- **Each elimination is itself a result** — record what was ruled out and how, as a finding in its own right.
- Eliminated branches are retained in full, never deleted.
- Distant predictions: each branch must state a prediction *in a domain different from its origin* — where else this explanation would leave a mark. A branch whose distant prediction has no record yet is a gap, and gaps are ranked like branches.

Applied to a study: list the candidate explanations for the central finding (including the authors' preferred one), state for each the cheapest observation that would distinguish it, and record which of those observations the study actually ran. Explanations never tested are open branches, not eliminated ones.

## 2. `preference_free_rank` — rank without hidden weights

Rank decision options by **unweighted Pareto dominance**: an option moves ahead only when it is no worse on every declared criterion and strictly better on at least one. No weights, no hidden utility function. Criteria must each declare a validity predicate and boundary behavior; a measurement outside its envelope returns `OUT_OF_ENVELOPE`, not a score.

Return classes you must preserve: `SCORED`, `UNKNOWN_measurable`, `UNKNOWN_buildable`, `UNKNOWN_simulable`, `BLOCKED(blocker)`, `OUT_OF_ENVELOPE`, `VARIABLE_UNIDENT`. Options with non-score classes remain **unresolved peers** — never treated as inferior.

**Honesty requirement carried from upstream:** "preference-free" means no *hidden* weights. The ranking still depends entirely on the declared criteria, their directions, their measurements, and their validity envelopes — whoever declares those is making choices. Record who declared them.

## 3. `rank_detector` — is the "new structure" real? (specialist, rarely applicable)

For quantitative literature where "more visible structure" is claimed: distinguish a **resolution artifact** (new points on the same manifold; dimension flat, scale finer) from a **dimensional activation** (new points off the manifold; dimension steps up at a scale and holds). Discriminator: whether local intrinsic dimension varies with scale at fixed sample density, with mandatory null construction (anisotropic noise, curvature, nonuniform density) before any reading is released.

Known upstream limits: one normal direction + off-manifold noise reads the same as an activation at the same scale; two activations at different scales read `ambiguous`; structure below the sample floor is `blocked`, **not absent**.

## Limits

- This card's tools add discipline to comparison; they do not establish which explanation is true.
- Pareto ranking declares nothing about criteria you did not declare.
- The rank detector is for geometric claims about data structure; applying it elsewhere is out of envelope by construction.
