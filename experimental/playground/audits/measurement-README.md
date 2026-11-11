# Third audit-process pilot: measurement-to-conclusion boundary

This fixed-case pilot asks what is licensed by restoring missing covariance,
supplying a calibration bound or completing a boundary inventory. It separates
attributed indications, software fidelity, conditional numerical compatibility,
sensor calibration and empirical support. It does not add another equation
engine or issue a new source-wide scientific verdict.

## Source and selected scope

The [GUM Annex H introduction](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/AH_e.html)
warns that its simplified examples and numerical data need not describe real
measurements. The [H.2 example](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/AH_e.html)
uses five paired voltage/current/phase sets and explicitly excludes uncertainties
of systematic-effect corrections from its random-effects treatment.

The source record preserves the five rows as decimal strings, original units,
pair IDs, attribution and provenance warning. A pinned hash detects changes to
this transcription, not source authenticity. Current is explicitly normalized
from mA to A. The selected output is impedance magnitude Z, not resistance R.
Phase remains in the source record but is not needed for this selected output.

The [source's two approaches](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/AH_e.html)
distinguish the ratio of means from the mean of individual ratios, preferring
the latter for its set-collected data. This pilot selects the former to inspect
first-order covariance and retains the latter as a distinct calculation, not
as an exactly equivalent estimator or universally superior description.

The [Table H.5 zero-correlation calculation](https://www.iso.org/sites/JCGM/GUM/JCGM100/C045315e-html/C045315e_FILES/MAIN_C045315e/AH_e.html)
assumes a different, sequential measurement procedure and absent correlations.
It does not license erasing correlations from simultaneous paired observations.
The explicit-zero case here is a labeled counterfactual, never an imputation
for missing covariance.

## Diagnostic path and uncertainty

- **Input provenance:** The source transcription and earlier pilots' source/review
  pins are checked before and after execution. Diagnostic Python code hashes,
  runtime, selection decisions and all gated runs remain in strict JSON.
- **Software fidelity:** Protocol binding, formal L0 accounting, applicability,
  a fresh equation/context-bound validation plan, known-answer cases and a null
  case precede calculation. The L0 quantity is formal case weight, not physical
  energy or charge.
- **Paired covariance:** Exact decimal/rational arithmetic computes covariance
  of means with denominator n(n-1). An independent centered-pair linear
  projection checks the variance calculated by the existing closed arithmetic
  adapter. Published rounded outputs provide an additional precision-limited check.
- **Output interpretation:** The adapter outputs impedance and its first-order
  Type A variance as two calculated quantities. The generic executor's
  `CalculatedValue.uncertainty` remains `None`; no general uncertainty propagation
  capability or complete measurement budget is claimed.
- **Cross-covariance:** Missing estimate/prediction covariance blocks the
  standardized residual. Explicit zero is a conditional assumption, not an
  automatic declaration of independence.
- **Calibration:** A planted output-equivalent correction bound is retained
  separately from standard uncertainty. Scope digest, ohm unit, finite
  nonnegative bound and explicit fixture provenance are required.
- **Boundary:** Missing bypass-current accounting blocks a scoped rule outcome.
  The complete fixture explicitly assumes zero bypass current. This is an
  assumption for a conditional probe, not a measured physical fact or an
  inferred absence.

The added prediction is 253.8 ohm with selected standard uncertainty 0.05 ohm.
The selected compatibility rule is `abs(residual+correction) <= k*u`, k=2.
Its calibration correction ranges over the entire declared symmetric bound;
no favorable correction is picked. A bound that straddles the rule leaves the
conditional determination unresolved. Exact rational comparisons of the
recorded binary residual, variance, bound and k avoid square-root comparison
roundoff at the selected inclusive boundary. They do not enclose ideal decimal
inputs, higher-order propagation error or physical uncertainty.

## What the probes establish

Missing V/I covariance blocks the arithmetic before the backend, and replacing
the equation cannot erase that experiment-level diagnostic. Supplying paired
covariance licenses the random-only variance but not calibrated model comparison.
Missing estimate/prediction covariance, calibration or relevant boundary terms
independently prevents a scoped outcome even when other inputs are supplied.

The complete conditional fixture is within the selected rule, while the
explicit-zero V/I covariance counterfactual is outside it. Both software
implementations pass their own fidelity harnesses. Neither result becomes a
physical failure or validation, and the source's illustrative provenance does
not change. A deliberately wrong covariance cross-term fails the software
instrument axis, not the physical description; invalid covariance inputs fail
the determination axis without declaring the sensor or physical model faulty.

## What this does not establish

- **Actual measurement calibration:** Conditional bounds are not calibration
  certificates. Actual sensor calibration remains INDETERMINATE even when
  software fidelity passes.
- **Physical adequacy:** It remains UNTESTED. No source-wide acceptance/rejection,
  real experiment, complete physical boundary, closure test or empirical
  prediction evidence is manufactured.
- **Confidence or universality:** k=2 is a selected numerical protocol, not
  an asserted 95% confidence/coverage interval, p-value, likelihood ratio,
  universal model hierarchy or demonstrated general audit accuracy.
- **A general metrology engine:** This is a fixed two-input, first-order Type A
  example, not arbitrary covariance propagation, a full calibration framework,
  general AC network correction or raw-data authenticity validation.
- **Absence or permanence:** No unmeasured bypass current is declared absent,
  and no continuity or permanent organization follows from this static example.

## Reproduce

```sh
# From repository root; output must be new and outside the repository.
PYTHONPATH=experimental python3 -m playground.audits.measurement_process \
  --output-dir /tmp/measurement-boundary-audit-new
PYTHONPATH=experimental python3 -m unittest playground.validation.test_measurement_audit
./run_checks.sh
```

The third suite is mandatory in `playground.self_check`. CI runs the full suite
on Python 3.11 through 3.14 and retains Markdown/JSON evidence per runtime.
The CLI prints all conditional case outcomes and independent axis statuses.
