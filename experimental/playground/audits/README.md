# Inspecting the audit process

The first pilot uses the preserved Tolman VI phase-to-probability audit.
It is an existing research-assessment case, not a new synthetic physical system,
but the additional adversarial inference probes are planted inputs rather than
observations. Nothing in this pilot establishes independent scientific
confirmation, detector sensitivity or a whole-publication verdict.

## Question

Can an audit reproduce its calculations and still refuse to turn them into
unsupported physical conclusions? The pilot inspects that question at the
mathematical-to-physical and calculation-to-observation boundaries.

The [publication's equation 35](https://link.springer.com/article/10.1140/epjc/s10052-026-16462-w)
contains a mixing-angle prefactor. Under an explicitly selected full-phase
average, writing M = sin²(2θ), the retained expression is P = 1 − M/2.
The existing audit's restricted comparison asks whether phase averaging alone
instead warrants P = 1/2 for every fixed mixing amplitude.
That is a scoped formalization of the inference, not a claim that no additional
physical equilibration mechanism could ever justify an equal-population limit.

## Replay before interpretation

The runner checks a newly inspected hash-pinned snapshot of original source
captures, review code, interpretation mappings, evidence outputs and publication
claim/decision records. A changed or missing pinned input blocks execution;
locks are not refreshed automatically. The original trace runs in a fresh
directory through Python's isolated mode, using only its pinned, locally
authored code. No code from the publication is executed.

Four outputs are compared against preserved hashes: calculations,
evidence bundle, integrity JSON and integrity Markdown. Byte identity is
reported separately from numerical agreement. Only finite float leaves in
the calculations and evidence bundle may differ within declared absolute
and relative replay tolerances of 1e-12; all accepted changes are retained.
Keys, shape, types, strings, booleans and integers must match exactly, and
both integrity reports must remain byte-identical. These tolerances are
not physical uncertainty, sensitivity or detectability. Execution time is
recorded anew, not forced to match the historical manifest. The original
snapshot is checked again after the run. The pilot records its own Python
version and the playground's Python-code hashes, but hash identity is not
source authentication, evidence independence or scientific validity.

## Competing propositions, functioning implementations

Two reduced declarative descriptions run through the normal diagnostic-gated
executor: retaining the mixing prefactor and the universal-half test proposition.
Both receive hand-stated implementation-fidelity known-answer and input-null
tests. Correct implementation of a false proposition must not be mislabeled
as a defective instrument.

At the selected M = 3/4, the two outputs are 0.625 and 0.5.
The difference rejects the universal-half mathematical criterion under the
declared conditions. It does not produce a physical-failure finding, establish
which full physical description should be corrected or predict detectability.
At M = 1 the reduced descriptions agree; that special case is retained.

The L0 ledger concerns total probability normalization only. Its selected
mathematical anchor is not a measured physical reference, and the ledger does
not close physical energy, matter or source-detector exchanges.
The pilot explicitly does NOT construct a physical `Experiment` where the
necessary boundary, anchor and accounting evidence are absent.

## Inference probes

- **Math-to-physics promotion:** A mathematical assessment and clean calculation
  do not supply physical support.
- **Observer/kernel substitution:** Changing a uniform phase average into a
  radial-window observer puts the reduced expression outside its declared scope.
  Calculation is blocked rather than silently applying the wrong average.
- **Absence:** A planted hypothetical non-detection without established
  sensitivity cannot become an absence claim. It is never presented as data
  acquired from a detector.
- **UNKNOWN expiry:** A simulated new-response trigger requires revision.
  Stale reliance fails determination, not the physical description; no new
  detector evidence is claimed to have arrived.
- **Missing physical bridge:** Normalization, valid propagation/spin derivation,
  physical boundary/closure, detector response, observations and uncertainty
  remain unresolved prerequisites.

The original publication claim C1 remains UNDETERMINED/UNMEASURED.
The original decisions D1 and D2 remain UNRESOLVED. New formal calculations
neither overwrite those records nor settle their questions by implication.
The previous draft criterion mappings remain draft declarations; this pilot
is a fixed-case inspection, not a generic inference executor.

## Run

From the repository root:

```sh
PYTHONPATH=experimental python3 -m playground.audits.tolman_process \
  --output-dir /tmp/tolman-audit-process-new
PYTHONPATH=experimental python3 -m unittest playground.validation.test_audit_process
./run_checks.sh
```

Use a new output directory outside the repository. Existing output directories
are refused, and repository output targets are rejected to protect original
records. Outputs include `tolman-vi-audit-process-report.md`,
`tolman-vi-audit-process-report.json` and the fresh legacy replay artifacts.
The JSON retains full gated runs, scope/selection decisions, exact bindings,
original claim/decision states, unresolved physical obligations and probe labels.

The tests are mandatory in `playground.self_check`. They test one bounded
existing audit and explicitly planted failure opportunities, not general
improvement in audit accuracy, empirical validation or completeness of all
possible inference failure modes.

## Portability correction

Pilot 0.1 reproduced all four outputs byte-for-byte on the local Python 3.12
and 3.14 runtimes, but requiring that on every runtime blocked the
[first CI run](https://github.com/JinnZ2/study-aperture/actions/runs/42995494254)
at the computed-output hash check. Pilot 0.2 therefore distinguishes
byte identity from an explicit numerical comparison, records every accepted
float difference, and continues rejecting structural changes or altered
conclusions. The preserved artifacts and their reference hashes are unchanged.
