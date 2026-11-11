# Second audit-process pilot: pendulum approximation

This case challenges the process with a different question: when an approximation
is described as accurate to a percentage, what exact quantity, denominator and
inequality does that percentage concern? It reuses the existing physics-case
authoring review, not a new pendulum dataset or an independent experiment.

## Source and uncertainty

The [OpenStax pendulum section](https://openstax.org/books/university-physics-volume-1/pages/15-4-pendulums)
compares sine and radian angle below about 15 degrees using a less-than-1%
statement, without stating a relative-error denominator. The
[preserved review](../../scope_audit_lab/reviews/physics-cases/README.md)
already records this ambiguity and distinguishes restoring-term error from
period error. `pendulum-source-review.json` is a newly attributed inspection
note based on a cached retrieved page, not a full source archive or independent
authentication. Its hash and six legacy file hashes are pinned explicitly.

The fixed offline replay executes only the pinned authoring script in isolated
Python. The legacy output's runtime version is retained separately, not forced
to match; all other fields use the first pilot's explicit float-replay policy.
Exact byte identity and accepted numerical differences remain separate.
Original review files, draft schema and claim states are not rewritten.

## Diagnostic path

The closed equation engine is unchanged: it calculates two arithmetic error
metrics from selected synthetic radian and sine values. `math.sin` supplies a
reference input, not an observed detector output. Independent rational
alternating-Taylor bounds check it before gated arithmetic can execute.
Those bounds concern the exact binary radian input in [0, 0.6], not an enclosure
of ideal degree-to-radian conversion or a general proof about a pendulum.

For nonzero nominal cases, each metric traverses protocol binding, a formal
case-weight L0 ledger, applicability, fresh known-answer and null harnesses,
and calculation. Substitution preserves the experiment and parent digest,
not the previous metric's plan or physical support. Hand-stated arithmetic
known answers do not use the equation under test to generate expectations.
The null case uses zero deviation with a NONZERO denominator, not zero angle.

The metrics are `(theta-sine)/sine` and `(theta-sine)/theta`. The selected
inclusive `error <= 1/100` rule is distinct from the source's strict wording.
Exact rational below/at/above controls preserve that distinction, and an
interval straddling a threshold stays unresolved. The numerical comparison
tolerance is not physical uncertainty, instrument sensitivity or a period bound.

At the selected 14-degree input the metrics give different criterion outcomes.
Both implementations may function correctly while their criteria disagree;
neither denominator acquires universal priority. At zero the defined ratios
remain undefined and calculation is blocked before the harnesses.
No continuous extension is silently substituted.

## Planted challenges and limits

- **Output transfer:** A restoring-term result cannot become a period-error bound.
- **Convention change:** A changed angle convention blocks applicability.
- **Reference corruption:** A wrong sine input fails the instrument axis and
  remains with the experiment across equation substitution.
- **Arithmetic corruption:** A faulty metric fails the known-answer harness,
  not the physical description.
- **Plan transfer:** A different metric cannot reuse an earlier passing plan.
- **Missing physical evidence:** No physical energy closure, observations,
  calibration, damping characterization or propagated uncertainty is invented.

The source claim remains undetermined as written; source intent and the cause
of the quantitative mismatch are unresolved. This is another bounded
source-based audit with synthetic inputs and planted probes, not general audit
accuracy, a universal model ranking, or independent scientific confirmation.
The report retains selection decisions, code/source hashes, runtime, exact
rational bounds, full gated runs and all planted-probe labels.

## Reproduce

```sh
# From repository root; output must be new and outside the repository.
PYTHONPATH=experimental python3 -m playground.audits.pendulum_process \
  --output-dir /tmp/pendulum-audit-process-new
PYTHONPATH=experimental python3 -m unittest playground.validation.test_pendulum_audit
./run_checks.sh
```

The new suite is mandatory in `playground.self_check`. CI retains the replay
and reports per Python runtime, with replay comparisons also printed in logs.
