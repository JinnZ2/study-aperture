# Denominator-change procedure audit

Status: IMPLEMENTED constructed finite-cohort audit and adversarial tests.
No observed enrollment, survival, physical adequacy, instrument calibration or
empirical claim support is established. This extends the inspection of a
selected procedure, not the equation library or a universal model hierarchy.

## Experimental question

Can equal ratios or matching declarations conceal different denominator
selection policies? Four initially enrolled members and four survivors give
the same `2/4` under both policies. A separate later-window fixture has only
two survivors: `2/4` per initially enrolled member and `2/2` per survivor.
These are two independently specified constructed snapshots, not a measured
longitudinal trajectory or a cross-context substitution.

Both quantities can be useful for different questions. Neither is universally
preferred, and arithmetic agreement in one selected snapshot does not make
their definitions interchangeable.

## What is checked

- **Calculation path:** each pair uses `execute()` and `substitute()` with a
  fixed experiment within the pair. Both equations receive fresh L0,
  applicability, known-answer and null checks. Initial enrollment is separately
  retained in the frozen anchor and the L0 account; actual survival is not
  silently treated as conservation of membership.
- **Source record:** immutable enrolled, surviving and outcome-member ID tuples,
  selected cohort/window, decisions and nonempty evidence references enter a
  content digest. Context count operands reference that exact census. A digest
  binds the selected record; it does not authenticate real-world membership.
- **Procedure:** the closed `n/d` and `n*(1/d)` forms map numerator `n` to the
  shared outcome count and denominator `d` to either the initially enrolled or
  surviving-member count. Input bindings, source references, counts, executed
  operands and retained points are checked against the membership record.
  A separate `Fraction` count oracle uses relative arithmetic tolerance
  `1e-12`, absolute tolerance zero when checking a computed point. This is not
  measurement uncertainty; calculated output uncertainty remains `None`.
- **Declaration:** the declared normalizer is checked against that actual
  input-selection policy, and cohort/window/reference/boundary scope is
  checked against the fixed procedure. Matching false declarations do not
  qualify the audited comparison.
- **Independent diagnoses:** declaration/procedure disagreement fails
  DETERMINATION, not PHYSICAL or a functioning arithmetic INSTRUMENT. A known
  policy mismatch remains visible alongside unknown membership. All findings,
  including unresolved findings, are retained.

The declaration-only comparison is preserved unchanged beside the procedure
audit. In the shared-false-label specimen it permits a declared point
comparison within its original declaration-only scope. The additional audit
refuses to promote that result into a procedure-qualified comparison.
This is an explicit limitation specimen, not an erasure or reinterpretation
of the earlier identity checker.

A consistent denominator trace is also not permission to bypass the existing
executor. Its current conservative context gate withholds the entire
calculation if any declared context value is unknown, even an unused survivor
count in an initial-enrollment comparison. That retained limitation has its
own constructed case; this audit does not silently change dependency-local
applicability policy.

## Constructed challenges and controls

- **Coincidence:** equal positive rates with identical snapshot member sets
  but different selection policies; later attrition breaks the coincidence.
- **Zero numerator:** equal zero rates despite different nonempty
  denominators do not establish quantity identity or physical absence.
- **False declarations:** one or both models label their actual survivor
  denominator as initial enrollment, including when their values agree.
- **Unknown versus empty:** missing survivor membership stays `None`.
  An explicit empty survivor tuple has known count zero and an undefined
  rate. Neither produces a computed zero rate.
- **Membership integrity:** unenrolled replacement members and duplicate IDs
  are preserved as inconsistent input specimens and block calculation.
  Same count is not proof of same membership.
- **Count/provenance integrity:** count claims inconsistent with their member
  IDs, changed censuses with unchanged counts, stripped operand provenance
  and altered retained operands/points cannot qualify the audit.
- **Positive controls:** both initial-enrollment and survivor policies permit
  scoped nominal comparisons when policy, members, declarations, operands and
  the original diagnostic comparison all qualify. Neither policy is ranked
  above the other.
- **Unsupported procedures:** expressions outside the two closed forms are
  withheld, not interpreted by guesswork. Failed original diagnostics remain
  blocked; this audit does not provide an execution bypass.
- **Guard sensitivity:** four in-memory controlled mutants remove the policy,
  declaration or cardinality check, or default an unknown count to zero.
  Each must be detected by a targeted assertion failure, not a crash.

## Replay and inspect

From the repository root:

```sh
PYTHONPATH=experimental python3 -m playground.audits.denominator_process \
  --output-dir /tmp/denominator-change-audit-new
PYTHONPATH=experimental python3 -m unittest playground.validation.test_denominator_audit
./run_checks.sh
```

The output directory must not already exist. Markdown and JSON retain the
constructed rates and complete original run snapshots beside the audited
comparison. CI captures a fresh evidence bundle for each matrix interpreter.
Earlier attempts and unrelated historical audit source records are untouched.

## This does not establish

This is a bounded procedure audit, not a general semantic proof or an
independent census verification. Outcome members are selected constructed
records of outcomes within the window; outcomes are not required to occur
only among surviving members. The survivor-normalized quantity can therefore
exceed one and is not automatically a survivor-only probability.

No causal selection-bias estimate, unbiased population estimator, sampling
uncertainty, real detection sensitivity, permanent organization, empirical
absence, physical adequacy or claim promotion follows. Same-policy eligibility
licenses a nominal point difference for the retained snapshot, not universal
interchangeability or future equivalence. The generic measurand checker and
the rest of the playground are not silently upgraded into provenance
authentication for arbitrary equations.
