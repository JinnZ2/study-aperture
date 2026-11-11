# Cross-system-class diagnostic tests

The experimental questions are the organizing structure. Five selected
constructed classes enter the existing diagnostic path; equations remain
replaceable instruments within that structure. These tests establish software
behavior on supplied cases, not physical adequacy of a thermal cell, capacitor,
spring, porous medium or biological population.

## Questions and selected accounts

| Selected class | Experimental question | Hand-stated nominal answer | Accounting meaning |
| --- | --- | --- | --- |
| Thermal storage | What does a constant-capacity cell store over a selected temperature increment? | Capacity 2 J/K and increment 3 K give 6 J. | Energy account with separately stated 6 J input. No transport, phase change or ambient loss model. |
| Electrical storage | What charge and energy does an ideal linear capacitor store? | Capacitance 2 F and voltage 3 V give 6 C and 9 J. | Separate charge and energy accounts with independently stated inputs. No source-circuit, leakage or breakdown model. |
| Mechanical storage | What force and energy does a linear spring produce? | Stiffness 2 N/m and displacement 3 m give 6 N and 9 J. | Work/energy account with separately stated 9 J input. No hysteresis, yielding or trajectory model. |
| Porous-connectivity surrogate | Does a finite diamond graph connect its selected boundaries? | At independent bond probability 1/2, spanning probability is 7/16; expected component count 33/16 and largest size 45/16. Selected mask 3 spans. | Fixed four-node universe only, not mass/energy closure or physical flow. No pressure, conductance or permeability prediction. |
| Lineage-reproduction surrogate | What finite descendant distribution follows a selected offspring law? | With two founders and P(0)=P(1)=1/2, generation-two probabilities are 9/16, 6/16 and 1/16 for counts 0, 1 and 2; mean 1/2, variance 3/8. | Fixed founder cohort, not conserved total population, biomass, energy or resources. No interaction or immigration model. |

All nominal answers and harness criteria are hand-stated in
`cross_system.py`; the backend under test does not generate them.
The existing backend suites retain their independent exact-oracle coverage.
Every fixture declares all seven context domains, a frozen anchor, selected
one-second readout window, units, input uncertainty declarations and selection
provenance. The readout window is an acquisition-scope selection, not a
dynamical trajectory or evidence of long-term stability.

## Diagnostic contracts

- **Native calculations:** Protocol binding, fresh L0, scoped applicability,
  plan/input/unit checks, nonempty known-answer tests and nonempty null tests
  precede nominal calculation. Diagnostic success leaves physical adequacy
  UNTESTED and applicability UNKNOWN when no bound adequacy assessment exists.
- **Orthogonal failures:** Stated energy/charge misclosure fails the physical
  axis for the selected storage accounts. Measured misclosure remains
  indeterminate between physical change and instrument error. Backend faults
  fail the instrument axis; incomplete experimental choices fail determination.
- **Independent support:** An explicitly supplied synthetic physical-OK finding
  can coexist with instrument failure. Such a record is assessor input, never
  inferred from arithmetic agreement, L0 closure or harness success.
- **Return and continuity:** Measured and specified nonreturns retain different
  classifications. Unasserted nonreturn is a transition, not automatic failure.
  System return and configuration persistence populate four separate cells.
  Fixed-node/founder returns say nothing about transport or living populations.
- **Sensitivity and absence:** A separate constructed threshold readout tests
  calibration plumbing. Its declared effect unit and exact context scope must
  match the non-detection before a scoped absence claim is issued. This is
  not a calibrated physical observer and does not derive sensitivity from
  equation outputs.
- **UNKNOWN lifecycle:** Registered expiry triggers create determination-track
  revisions, not physical refutations. Reliance on an explicitly declared
  expired dependency blocks calculation. Unrelated expired determinations do
  not contaminate other classes; reevaluation preserves the original and
  issues a fresh UNKNOWN successor.

## Transfer traps

All 20 directed foreign-class pairs are exercised. Foreign plans fail their
content bindings, and merely rewriting their digests does not hide mismatched
ports or units. Foreign model substitutions remain blocked within the original
experiment rather than silently changing its boundary.

Adequacy evidence, equation-specific diagnostic records and sensitivity do not
transfer between contexts. That includes the dimensionless graph and lineage
surrogates. Capacitor and spring numerical outputs deliberately coincide,
while their output quantities, units, scopes and account meanings differ.
Numerical resemblance is not physical equivalence.

A compatible new revision reruns every diagnostic, retains its parent digest
and does not inherit adequacy evidence. Measurement/design defects remain with
the fixed experiment through replacement. Changes to selected boundary,
observer, environment or observation window require fresh scope evaluation.
The 5-by-5 applicability map reports cells independently, without a winner or
universal ranking.

## Fail-open regressions closed

Cross-class tests exposed existing diagnostic gaps; their guards now live in
the shared diagnostics, not in a privileged fixture executor.

- **Empty return protocol:** No declared quantities or tolerances cannot count
  as an observed return. The result remains indeterminate rather than asserting
  persistence from no comparisons.
- **Invalid return criteria/readouts:** Nonfinite or negative tolerances,
  malformed provenance and invalid reference records fail determination.
  Nonfinite or non-real return readouts fail the instrument axis, without
  asserting a physical change.
- **Invalid sensitivity ladders:** The full criteria set is checked before
  readout, using the shared finite numeric contract. Malformed sizes, empty
  output assertions, missing/negative tolerances and nonboolean expectations
  fail determination. Nonfinite, non-real or missing asserted instrument
  outputs fail the instrument axis, including a NaN at the null rung.
- **Invalid absence thresholds:** NaN, infinity, booleans and negative
  magnitudes cannot qualify a non-detection or become an absence threshold.

## Limits that remain explicit

Structural accounting completeness is not semantic completeness. A declared
energy-only ledger can close even if a person omitted a physically relevant
charge account. A regression deliberately demonstrates this limitation:
passing that ledger does not promote physical adequacy or applicability.
The laboratory does not discover the correct physical boundary, authenticate
evidence references, prove SI dimensions, validate selected idealizations or
propagate uncertainty automatically.

Finite connectivity is not physical permeability, model extinction is not
observed absence, and finite survival or a return observation is not permanent
organization. The suite does not validate continuum transport, fluid or
chemical dynamics, interactions, ecosystems or additional untested classes.
Its scope is cross-class diagnostic behavior under explicit constructed
conditions, not a universal theory or production physics library.

## Run and inspect

From the repository root:

```sh
cd experimental
python3 -m unittest playground.validation.test_cross_system
python3 -m playground.validation.cross_system
python3 -m playground.self_check
```

The example emits strict JSON with five complete native `EquationRun` records,
the hand-stated nominal criteria, selected scope and accounting limitations,
and a 25-cell applicability map. Conditions, decisions, anchors, ledgers,
validation criteria, evidence references, findings, content digests and
unpropagated output uncertainty remain inspectable. It does not issue a
single physical success verdict. The root `./run_checks.sh` includes this
suite through the mandatory playground self-check.
