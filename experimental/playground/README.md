# Playground — experimental determination laboratory

Status: Milestones 1-4 implement diagnostic infrastructure, system and
determination tracks, and context-dependent applicability records. Equation
substitution now adds diagnostic-gated arithmetic adapters. Tests and
examples are synthetic; real-system applicability and physical validation
are not established. Equation families and observer regimes remain deferred.

An instrument for examining the relationship between:

```
physical system -> experimental determination -> mathematical representation
               -> observed result -> revised determination
```

The software is organized around **experimental questions**, not equation
families. Equations enter as replaceable instruments validated by harnesses,
never trusted by construction.

Milestone 1 established the **diagnostic infrastructure**: typed
failure records, the L0 accounting-closure gate, known-answer and null
harnesses, planted-defect self-tests, and the provenance skeleton. The
physical equation-family library remains deferred. The laboratory tests its
own determinations before extending its mathematical instruments.

## Three kinds of failure, never merged

| Axis | Failure means | Reflects on |
|---|---|---|
| `PHYSICAL` | the proposed model violates physical constraints or fails to describe observations | the model |
| `INSTRUMENT` | the measurement or diagnostic mechanism cannot reliably detect what it intends to measure | inferences from measurements |
| `DETERMINATION` | the experimental choices, boundaries, controls, or provenance are insufficient to support the conclusion | the conclusion only |

The axes are orthogonal by construction: a model can be physically adequate
while the instrument is inadequate; an instrument can function correctly
while the experimental boundary is inappropriate. `FailureRecord` derives
each axis status from typed findings and refuses boolean coercion — there is
no generic `MODEL_FAILED`, and no code path can set an axis directly.

Each axis carries one of four statuses: `OK` (explicit finding, scoped),
`FAILED`, `INDETERMINATE` (posed but unsettled), `UNTESTED` (no check
addressed it). Non-detection is not absence; an expired UNKNOWN is not a
negative result.

## Forbidden promotions (guarded in the self-check)

- An instrument PASS must not silently validate a model.
- A clean determination must not silently certify an instrument.
- An integrity PASS must not silently change claim support.

The [measurand-identity substitution challenge](equations/MEASURAND.md)
additionally tests that matching names, units, values and arithmetic
diagnostics cannot license comparison of different declared quantities.
Comparison eligibility stays separate from calculation status and physical
adequacy; both run records survive a void comparison.

The [denominator-change procedure audit](audits/denominator-README.md) checks
the selected count against explicit cohort-member IDs and the actual equation
input binding. Equal rates, equal counts and shared false labels do not license
interchangeability. Unknown membership, empty denominators and inconsistent
source records remain distinct; both policies have scoped positive controls.
This is constructed procedure evidence, not independently observed membership.

The [distribution-to-mean substitution test](audits/distribution-mean-README.md)
holds the target fixed while replacing a constructed weighted distribution by
its mean. Linear controls and second-moment counterexamples distinguish
arithmetic fidelity from purpose-specific information loss. Scope is explicit;
stationarity, ergodicity, equilibrium and missing dependencies are not inferred.

The [cross-audit regression pass](audits/cross-regression-README.md) runs
separately linked denominator and mean-substitution pairs in one shared
constructed context. Findings remain separate when policy changes, target
loss and missing scope coexist; sibling certificates cannot clear failures.
This is a diagnostic interaction test, not a new jointly composed estimator.

## L0: accounting closure

L0 runs before any physics. Its question: does the boundary accounting
close? Classification follows what is *established*, not convenience:

| Situation | Outcome |
|---|---|
| registered intervention missing from the ledger | `DETERMINATION` FAILED |
| ledger not declared complete, books unbalanced | `DETERMINATION` FAILED (nothing asserted about the model) |
| complete ledger, no measured values, books unbalanced | `PHYSICAL` FAILED |
| complete ledger, measured values involved, books unbalanced | `PHYSICAL` + `INSTRUMENT` INDETERMINATE (error vs description failure unresolved) |
| books balance | `DETERMINATION` OK — a bookkeeping fact, not a physical validation |

## Harnesses

- `known_answer.py` — validates an instrument against known-answer cases.
  A pass certifies the instrument **within the tested case set only**; the
  record says so explicitly. Zero cases is INDETERMINATE, not a pass.
- `null_harness.py` — the instrument must not detect what is absent. A
  clean null does not establish detection sensitivity.

## Two kinds of change (two state tracks)

- **System track:** anchor → perturbation → return → misclosure.
- **Determination track:** issued → conditions recorded → expiry → reevaluation.

Misclosure is to the system what UNKNOWN expiry is to the determination.
A transition in one track is never mapped onto the other.

## System track (milestone 2)

- **Return test** (`reference/return_test.py`): does the system return to
  the frozen anchor within declared tolerances? Classification mirrors the
  L0 gate: an asserted return violated by measured values is INDETERMINATE
  on the physical and instrument axes; violated by the description's own
  values it is a PHYSICAL failure; a non-return with no assertion is an
  observed transition, not a failure; an incomplete record is a DETERMINATION
  indeterminacy.
- **Misclosure** (`reference/misclosure.py`): per-quantity residuals of the
  return loop, pure computation; classification lives in the return test.
- **Continuity matrix** (`reference/continuity.py`): system persistence and
  configuration persistence answered separately. Four distinct cells —
  CONTINUOUS, RETURN_WITH_RECONFIGURATION, DRIFT_WITH_STABLE_CONFIGURATION,
  DISCONTINUOUS — plus INDETERMINATE. A system can return to its anchor
  state while its configuration changed, and vice versa.
- **State transitions** (`lifecycle/state_transitions.py`): typed
  transitions on either track, with the six system-change types
  (reorganizes, accumulates energy, loses connectivity, crosses threshold,
  adapts, changes relationships). Track crossing is refused by design.

## Determination track (milestone 3)

- **Sensitivity** (`detection/sensitivity.py`): the detection limit,
  established per instrument and per condition set from a ladder of known
  effect sizes. Not transferable between conditions. A miss on an
  expected-detectable rung, or a detection where none should be possible,
  is an INSTRUMENT failure; an empty or undetectable ladder is a
  DETERMINATION indeterminacy — no limit established is not zero sensitivity.
- **Non-detection** (`detection/non_detection.py`): a non-detection is
  recorded as a non-detection. It becomes evidence of absence only when an
  established sensitivity covers the effect size of interest; without
  sensitivity, without an effect size, or below the detection limit, it is
  DETERMINATION INDETERMINATE — it establishes nothing.
- **Scoped absence** (`detection/scoped_absence.py`): an absence claim
  carries what is absent, at what magnitude floor, within which scope, and
  up to which detection limit. The sensitivity's conditions must cover the
  observation's conditions; a mismatch or an undeclared condition yields
  INDETERMINATE, never a qualified claim. Outside the recorded scope, the
  claim says nothing.
- **UNKNOWN expiry** (`lifecycle/unknown_expiry.py`): UNKNOWN determinations
  carry expiry triggers (new evidence, condition change, instrument change,
  revision dependency). Expiry is a revision trigger, not a negative
  result — there is deliberately no REFUTED state. An expired UNKNOWN
  produces a determination-track transition and no failure findings.
- **Reevaluation** (`lifecycle/reevaluation.py`): reevaluation reopens the
  determination; it does not overturn it by default. The original is
  preserved as REEVALUATED and the successor is issued alongside it, never
  in its place. A determination resting on an expired or superseded UNKNOWN
  is stale (DETERMINATION failure); resting on an open UNKNOWN is allowed
  and is not a failure.

## Context-dependent applicability (milestone 4)

[Applicability mapping](applicability/README.md) keeps declared-domain membership
separate from evidence of physical adequacy. Contexts retain all seven
determination coordinates, selection provenance, uncertainty, and anchor
bindings. Descriptions retain their property-specific scope criteria and
dependencies; evidence assessments bind to exact context/description digests.
Matching a scope, mathematical consistency, or a diagnostic PASS cannot supply
physical support.

Numeric uncertainty intervals crossing a scope boundary remain unresolved.
Missing information and open UNKNOWN dependencies remain UNKNOWN; stale
dependencies or failed instruments/determinations block conclusions without
declaring a model false. Multiple descriptions may overlap without a winner.
Maps report independent cells, evidence, unresolved questions, and conditions
that require reassessment, with no interpolation or extrapolation.

Run the constructed, non-empirical example from `experimental/`:

```sh
python3 -m playground.applicability.example
```

## Equation substitution

[Equation substitution](equations/README.md) keeps explicit adapter
identity/revisions, context-bound inputs, actual frozen anchors, boundary
accounting, independently stated diagnostic cases, and selection provenance.
Each execution reruns L0, applicability preflight, and nonempty known-answer
and null harnesses before the nominal calculation. A different formula cannot
inherit old tests or physical support; context-bound measurement/design
failures remain with the experiment during substitution.

Successful computation without adequacy evidence remains provisional, with
applicability UNKNOWN and the physical axis UNTESTED. NaN, infinity, missing
criteria, stale context bindings, or unresolved prerequisites cannot silently
qualify a run. Outputs retain UNKNOWN uncertainty because propagation is not
implemented. The first finite-graph bond family now uses that same path;
branching uses a separate bounded backend through the same gates.

```sh
# from experimental/
python3 -m playground.equations.example
```

## Finite-graph percolation

[Finite bond percolation](equations/PERCOLATION.md) is the first graph-backed
family, not an alternate laboratory entry point. A selected, provenance-bound
undirected graph and its source/target sets produce component and spanning
results for a supplied mask, alongside exhaustive independent-bond ensemble
metrics. The graph engine is versioned and bounded; arbitrary callbacks and
subclass plugins are not accepted.

Finite-grid reports bracket a selected spanning-probability criterion while
keeping every experimental condition except nominal `p` fixed. They do not
infer a physical transition or universal critical threshold. Disconnection is
not physical absence, diagnostic success is not empirical support, and the
example's mathematical node-count ledger does not establish physical energy
closure. Input uncertainty is retained but not propagated.

```sh
# from experimental/
python3 -m playground.equations.percolation_example
```

## Finite-generation branching

[Finite branching](equations/BRANCHING.md) examines selected single-type iid
offspring laws without immigration or interaction. Its initial cohort is bound
to a frozen anchor and fixed-founder ledger. The backend computes complete
finite-generation population distributions and conditional moments using exact
integer ratios internally; it rejects oversized support rather than dropping
a tail, and fails as an instrument if a positive probability underflows on
float export.

Generation profiles keep all conditions except the finite horizon fixed and
retain each point's diagnostic and applicability record. A stable mean does
not establish organization, finite survival does not establish permanence,
and model extinction does not establish physical absence. Conditional
stochastic variance is not propagated determination uncertainty. Branching
and percolation remain distinct families with no automatic equivalence or
universal ranking.

```sh
# from experimental/
python3 -m playground.equations.branching_example
```

## Cross-system-class diagnostics

[Cross-system diagnostics](validation/CROSS_SYSTEM.md) exercise the same layers
against five constructed classes: thermal storage, electrical storage,
mechanical storage, finite porous-connectivity and lineage-reproduction
surrogates. These are explicitly selected scopes, not empirical validations
or an equation-family hierarchy.

Each native run passes through protocol binding, fresh L0, applicability,
unit/plan binding, known-answer and null harnesses before calculation. Tests
also cover return/misclosure, independent configuration continuity, scoped
sensitivity/absence, and UNKNOWN expiry. Deliberate cross-context transfers
must not carry plans, adequacy evidence or calibration into a different class.
A runnable report retains the five full run records and their 25-cell map.

```sh
# from experimental/
python3 -m playground.validation.cross_system
python3 -m unittest playground.validation.test_cross_system
```

## Inspecting an existing audit

The [Tolman VI audit-process pilot](audits/README.md) replays preserved audit
artifacts and examines the route from mathematical results to physical claims.
It does not alter the original audit, repair unresolved registry references,
manufacture a physical experiment or extend the closed equation engine.
Planted scope/absence/expiry probes are explicitly distinguished from replayed
records and actual observations.

```sh
# from experimental/; use a new output directory OUTSIDE the repository
python3 -m playground.audits.tolman_process --output-dir /tmp/tolman-audit-process-new
python3 -m unittest playground.validation.test_audit_process
```

The [second audit-process pilot](audits/pendulum-README.md) examines the
pendulum approximation review: explicit error denominators, undefined relative
error at zero, independent sine-reference bounds, and prohibited transfer to
period error. It retains source ambiguity instead of promoting a selected metric
into a source-wide or physical verdict.

```sh
python3 -m playground.audits.pendulum_process --output-dir /tmp/pendulum-audit-process-new
python3 -m unittest playground.validation.test_pendulum_audit
```

The [third audit-process pilot](audits/measurement-README.md) inspects the
measurement-to-conclusion boundary using attributed GUM illustrative data:
paired covariance, calibration scope, a missing boundary term and explicitly
planted prediction probes. Restored numerical comparability cannot promote
worked-example provenance into empirical validation.

```sh
python3 -m playground.audits.measurement_process --output-dir /tmp/measurement-boundary-audit-new
python3 -m unittest playground.validation.test_measurement_audit
```

## Self-check

```
cd experimental  # from repository root
python3 -m playground.self_check
```

Runs the planted-defect suite (the lab testing its own determinations), the
design-contract guards, and the control cases. Every planted defect must be
caught **and correctly classified**, or the build fails. The self-check also
runs applicability, equation-substitution, finite-percolation, finite-branching
and cross-system-class
adversarial/unit suites, plus all three bounded audit-process pilots. All
parts must pass.

## Module map

```
playground/
├── failures.py            typed failure records (three orthogonal axes)
├── gates/                 L0 closure gate, gate registry, typed gate results
├── reference/             anchors, return tests, misclosure, continuity
├── validation/            known-answer + null harnesses, planted defects, metrics
├── provenance/            claim status, derivations, hash-bound evidence chain
├── observation/           passive / perturbative / strategic regimes (stub)
├── detection/             sensitivity / non-detection / scoped absence
├── applicability/         scoped matching, evidence binding, context maps
├── equations/             gated arithmetic + finite bonds + finite branching
└── lifecycle/             UNKNOWN expiry / reevaluation / state transitions
```

## Roadmap

1. Diagnostic infrastructure (done — milestone 1).
2. Continuity, transition, return, and misclosure (done — milestone 2, the system track).
3. Sensitivity-qualified absence and UNKNOWN expiry (done — milestone 3, the determination track).
4. Context-dependent applicability mapping (implemented, milestone 4; synthetic tests).
5. Equation substitution (implemented with arithmetic adapters and synthetic tests).
6. Finite-graph bond percolation (implemented with exact-oracle and diagnostic tests).
7. Finite-generation branching (implemented separately with exact-oracle and diagnostic tests).
8. Cross-system-class testing (implemented with five constructed scopes and cross-context guards).

The first implementation milestone is the diagnostic infrastructure, not the
equation library — otherwise we risk building a sophisticated mathematical
playground whose own determinations have not been tested.
