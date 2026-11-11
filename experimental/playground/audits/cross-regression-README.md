# Cross-audit regression pass

Status: IMPLEMENTED constructed shared-context regression and retention tests.
This is a diagnostic regression of existing audit paths, not an expansion of
the equation library. No physical adequacy or empirical support is established.

## What is being tested

Do denominator changes, distribution-to-mean substitutions and missing scope
retain their separate meanings when they coexist in one selected protocol
context?

The runner constructs one context, enrollment anchor and L0 ledger from the
two existing synthetic fixtures. It then runs two separate linked pairs
through the existing `execute()` / `substitute()` paths:

- **Denominator pair:** initially enrolled versus surviving-member counting,
  or a same-policy control.
- **Mean-substitution pair:** a full finite weighted response versus its
  mean-only replacement, with a linear control or second-moment target.

All four runs bind to the same freshly constructed context. Each pair keeps
its own parent linkage, plans, arithmetic certificates, audit view and
uncertainty. The source populations are not asserted to be physically linked.
This is not a sequentially composed joint estimator.

Common conditions must agree before composition. Original context, anchor
and diagnostic bindings must be current; stale bindings are rejected rather
than requalified. Common reference quantities, boundary bookkeeping, declared
completeness, units and intervention selections must be compatible.
Only a closed list of source-structural DETERMINATION findings from the freshly
constructed fixtures may be explicitly rebound to the extended context.
Other source diagnostics are rejected; no physical-support clearance or old
arithmetic certificate is copied.

## Expected distinctions

- **Two known findings:** denominator-policy change remains a void comparison;
  mean-target information loss remains a failed selected-purpose determination.
  Both arithmetic instruments can function correctly while PHYSICAL remains
  UNTESTED.
- **One valid control:** a valid mean result cannot clear a denominator
  mismatch, and a mean failure cannot relabel the independent valid
  denominator comparison.
- **Missing scope:** the conservative shared-context gate blocks calculations.
  A known policy mismatch remains visible alongside the unknown scope, but
  no scope-qualified mean-target loss is asserted. Exact source moments stay
  inspectable as source mathematics, not a licensed experimental conclusion.
- **Unknown membership:** unknown survivors remain `None`; missing scope and
  the known policy distinction survive alongside that unknown.
- **Multiple coincidences:** equal ratios and a degenerate mean-substitution
  coincidence do not become general policy or representation equivalence.
- **Inconsistent source derivation:** an incorrect mean operand withholds the
  mean audit rather than being treated as valid evidence of target loss.
- **Instrument and physical findings:** a failed mean-route harness does not
  inherit a sibling's certificate. An independently planted physical finding
  remains physical, with its constructed origin explicit.
- **Empty denominator:** an explicitly empty survivor denominator remains
  undefined while a separately well-scoped mean-target loss can still be
  assessed. The affected denominator route is not assigned a zero rate.

The finding union is a retention view, not an overall model verdict. Both
original finding lists remain unchanged and separately available. A derived
axis summary never replaces or redistributes component statuses. Expected
diagnostic failures are successful regression specimens when the independent
test expectations are met.

## Verification

The suite checks an independent expected-outcome matrix, exact finding-list
retention, shared snapshots, separate lineage, missing-scope preservation,
cross-chain parent rejection and unchanged results when the execution order
is reversed. Three controlled in-memory mutants drop the denominator view,
the mean view or all union findings; each must be caught by an assertion,
not a runtime crash.

From the repository root:

```sh
PYTHONPATH=experimental python3 -m unittest \
  playground.validation.test_measurand \
  playground.validation.test_denominator_audit \
  playground.validation.test_distribution_mean_audit \
  playground.validation.test_cross_audit_regression
PYTHONPATH=experimental python3 -m playground.audits.cross_audit_regression \
  --output-dir /tmp/cross-audit-regression-new
./run_checks.sh
```

The evidence runner only generates records; test success comes from the
assertions, not from interpreting its status label as PASS. Output directories
must be fresh. Markdown and JSON retain complete component runs, source
records, scopes, decisions, findings and unresolved conditions. CI captures
fresh per-interpreter evidence. Source fingerprints cover selected producer
and dependency files, not complete environment attestation.

## This does not establish

This does not test a new composed estimator, a joint physical population,
causal linkage, physical adequacy, general model ranking, absence,
stationarity, ergodicity or equilibrium. It does not weaken the conservative
unknown-context gate or resolve its dependency-local applicability limitation.

Existing audit implementations, historical source records and prior local
attempts remain unchanged. This is a bounded regression of their interaction,
not a universal certificate for arbitrary combinations of audits.
