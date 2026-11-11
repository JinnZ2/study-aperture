# Playground — experimental determination laboratory

Status: Milestones 1-4 implement diagnostic infrastructure, system and
determination tracks, and context-dependent applicability records. Tests and
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
equation library is deliberately absent — the laboratory tests its own
determinations before it owns any equations.

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

## Self-check

```
cd experimental  # from repository root
python3 -m playground.self_check
```

Runs the planted-defect suite (the lab testing its own determinations), the
design-contract guards, and the control cases. Every planted defect must be
caught **and correctly classified**, or the build fails. The self-check also
runs the applicability adversarial/unit suite; both parts must pass.

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
├── equations/             percolation / branching families (stub — later)
└── lifecycle/             UNKNOWN expiry / reevaluation / state transitions
```

## Roadmap

1. Diagnostic infrastructure (done — milestone 1).
2. Continuity, transition, return, and misclosure (done — milestone 2, the system track).
3. Sensitivity-qualified absence and UNKNOWN expiry (done — milestone 3, the determination track).
4. Context-dependent applicability mapping (implemented, milestone 4; synthetic tests).
5. Equation families as validated instruments.
6. Cross-system-class testing.

The first implementation milestone is the diagnostic infrastructure, not the
equation library — otherwise we risk building a sophisticated mathematical
playground whose own determinations have not been tested.
