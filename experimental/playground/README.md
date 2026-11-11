# Playground — experimental determination laboratory

An instrument for examining the relationship between:

```
physical system -> experimental determination -> mathematical representation
               -> observed result -> revised determination
```

The software is organized around **experimental questions**, not equation
families. Equations enter as replaceable instruments validated by harnesses,
never trusted by construction.

Milestone 1 (this package) is the **diagnostic infrastructure**: typed
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

## Self-check

```
python -m playground.self_check
```

Runs the planted-defect suite (the lab testing its own determinations), the
design-contract guards, and the control cases. Every planted defect must be
caught **and correctly classified**, or the build fails.

## Module map

```
playground/
├── failures.py            typed failure records (three orthogonal axes)
├── gates/                 L0 closure gate, gate registry, typed gate results
├── reference/             anchor states (system track); return/misclosure stubs
├── validation/            known-answer + null harnesses, planted defects, metrics
├── provenance/            claim status, derivations, hash-bound evidence chain
├── observation/           passive / perturbative / strategic regimes (stub)
├── detection/             sensitivity / non-detection / scoped absence (stub)
├── equations/             percolation / branching families (stub — later)
└── lifecycle/             UNKNOWN expiry / reevaluation / state transitions (stub)
```

## Roadmap

1. Diagnostic infrastructure (done — milestone 1).
2. Continuity, transition, return, and misclosure (done — milestone 2, the system track).
3. Sensitivity-qualified absence and UNKNOWN expiry.
4. Context-dependent applicability mapping.
5. Equation families as validated instruments.
6. Cross-system-class testing.

The first implementation milestone is the diagnostic infrastructure, not the
equation library — otherwise we risk building a sophisticated mathematical
playground whose own determinations have not been tested.
