# Distribution-to-mean substitution test

Status: IMPLEMENTED constructed finite-distribution audit and adversarial tests.
No physical adequacy, observed population distribution, calibrated uncertainty,
stationarity, ergodicity or thermodynamic equilibrium is established. This is
a scoped representation test, not a change to Card 02 or a general
mathematical assertion about averages.

## Question and operation

Does replacing a selected finite weighted distribution by a point at its
weighted mean preserve the information needed by a declared target?

The source record has exactly two dimensionless atoms and explicit integer
weights. Their normalized weights are constructed choices, not estimated
sampling probabilities. Original values, weights, population, window, domain,
decisions and evidence remain in the record after the replacement.

The selected operation removes atom values and weights as separate operands
from the replacement calculation. It is not the same operation as freezing
a time-dependent variable, assuming stationarity, averaging environments,
or deleting a demonstrated temporal or joint dependency. No temporal order
or joint data are supplied; their omission is not evidence of their absence.

## Controls and counterexamples

- **Same mean, different spread:** equal-weight sources at `(0, 2)` and `(1, 1)`
  both have mean `1`. Their weighted second moments are respectively `2` and
  `1`. The mean-only squared response is `1` for both.
- **Linear target:** for the selected response `2X`, the full weighted sum and
  mean-only response are both `2` for either source. This control qualifies
  the selected target in the retained cases, not a physical process or every
  use of the mean.
- **Second-moment target:** for the source `(0, 2)`, replacing the distribution
  loses the spread needed to preserve the selected response. Both arithmetic
  implementations function correctly; the substitution determination fails.
- **Degenerate coincidence:** for `(1, 1)`, the second-moment substitution also
  agrees. This case does not license the same replacement for a source with
  nonzero spread.
- **Unequal weights:** weights `(1, 3)` at `(-2, 2)` yield mean `1`, second moment
  `4` and a mean-only squared response of `1`. Weights are not defaulted to
  equal values.
- **Zero mean:** equal weights at `(-1, 1)` yield mean zero but squared response
  one. Neither a zero mean nor a constructed zero-response control establishes
  physical absence.

Both descriptions declare the same target quantity. In the second-moment
case, the replacement is a candidate approximation to that target, not a
relabeling that makes a squared mean identical to a second moment.
Consequently a qualified numerical difference can remain inspectable even
when the substitution is not usable for the selected target. This differs
from the denominator audit's comparison of different quantities.

## Diagnostic and provenance boundaries

Each pair uses the existing `execute()` and `substitute()` path with a fixed
experiment within that pair. Different source distributions are separate
experiments, not silently exchanged inside a substitution. Both routes
receive fresh applicability, L0, hand-stated known-answer and null checks.
Route-specific expectations test arithmetic fidelity, not target sufficiency.

The reused synthetic L0 ledger checks its selected boundary bookkeeping.
It does not establish conservation of distribution shape or a physical
closure law for these marginal distributions. Source normalization and
mean derivation are checked independently.

Source and question content digests bind the source-derived operands and
selected scope. A closed trace checks each route's input mapping, formula,
source evidence, executed operands and retained point against independent
`Fraction` moment arithmetic. Point-oracle tolerances are relative `1e-12`
and absolute `1e-12`, not measurement uncertainty. Exact target residuals
are retained separately from floating-point differences. Calculated output
uncertainty remains `None`.

Known negative weights are inconsistent inputs, not physical-model failures.
Unknown weights or values remain unknown. Explicit total mass zero makes a
normalized mean undefined, not zero. All original inconsistent or incomplete
records and their independent findings are preserved.

Undeclared purpose, population, window, domain or conditions withhold the
determination. A known source scope is not copied into a missing question
scope. The candidate arithmetic calculation is separately explicit and does
not fill a missing purpose. Known mismatches remain visible beside unknowns.

The original measurand comparison is retained beside the procedure and
target-preservation audit. Missing declarations, unsupported expressions,
failed instruments and independent physical findings are not overridden by
a locally consistent trace. Only the four closed forms for the two targets
are supported; even an algebraically equivalent unregistered expression is
withheld rather than interpreted by guesswork.

Four in-memory controlled mutants remove target-loss detection, ignore
weights, omit unresolved-scope tracking or remove operand provenance
verification. Targeted tests must detect them by assertions, not crashes.

## Replay and inspect

From the repository root:

```sh
PYTHONPATH=experimental python3 -m playground.audits.distribution_mean_process \
  --output-dir /tmp/distribution-to-mean-audit-new
PYTHONPATH=experimental python3 -m unittest playground.validation.test_distribution_mean_audit
./run_checks.sh
```

Output directories must be fresh. Markdown and JSON preserve the original
distributions, source moments, selected question, reduction operation, both
complete runs, diagnostics, provenance, decisions and remaining unknowns.
The report fingerprints selected producer/dependency files and records Python
version; this is not complete environment attestation or source authentication.
CI retains a fresh evidence bundle per interpreter. Historical audit inputs
and earlier local attempts remain unchanged.

## This does not establish

No universal hierarchy of full distributions and means follows. A mean can
preserve the selected calculation while losing information irrelevant to that
particular target. Failure for another target is not a claim that averages
are universally invalid.

This does not establish real-world population properties, physical adequacy,
causality, empirical absence, future stability, temporal stationarity,
ergodicity or thermodynamic equilibrium. It does not test higher-dimensional
correlations, temporal ordering or arbitrary distribution shapes. Those
questions require their own source records, operations and declared scopes.
