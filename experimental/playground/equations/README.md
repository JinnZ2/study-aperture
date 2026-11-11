# Diagnostic-gated equation substitution

Status: Implemented experimental substitution infrastructure and bounded
arithmetic and [finite-graph bond percolation](PERCOLATION.md) adapters, with
constructed tests and examples. This does not
establish physical adequacy, observer validity, dimensional correctness, or
real-system applicability. Branching remains deferred.

The equation is a replaceable instrument inside an experiment, not an
alternative entry point around the diagnostic layers. `execute()` is the
supported execution path; `substitute()` preserves the fixed experiment and
calls that complete path again for the selected replacement.

## What is bound

- **Equation:** explicit identity and revision, investigated property, named
  input/output ports, declared units, arithmetic expressions, applicability
  criteria, assumptions, dependencies, selection provenance, source references,
  and arithmetic-engine version. The registry refuses in-place replacement or
  implicit "latest" resolution.
- **Experiment:** the seven-coordinate context, actual frozen anchor, boundary
  ledger, unit declarations, registered control/observer links, and optional
  context-bound experimental diagnostics. The ledger must identify this exact
  context and anchor, match their selected labels, begin at recorded anchor
  values, and declare complete accounting. These are explicit selected
  accounting decisions, not independently proved physical boundaries.
- **Validation plan:** hand-stated known-answer and null criteria, tolerances,
  units, selection rationale, evidence references, and exact equation/context
  digests. Changing an adapter, input binding, criteria, or source metadata
  changes its content binding; changing a formula cannot inherit support even
  if someone reuses the same human-readable identity and revision in another
  registry.
- **Result:** complete equation/experiment/plan records, their digests,
  selection decision, attempted stages, gate/harness results, applicability,
  supplied assessments, three-axis diagnostics, dependency snapshot, actual
  inputs, all-or-nothing outputs, remaining limitations, and parent-run digest.

The registry accepts exact built-in arithmetic and finite-bond adapter types;
arbitrary model-family plugins and subclasses are rejected. The graph backend
is narrowly versioned and preserves the same gating contract. There is
intentionally no unrestricted callable-plugin escape hatch.

## Execution order

1. Check experimental content bindings and diagnostic scope.
2. Recompute L0 accounting closure; FAIL or INDETERMINATE stops execution.
3. Assess candidate applicability and supplied adequacy evidence. Missing scope,
   uncertain boundary membership, assumptions, missing/open UNKNOWN
   dependencies, stale dependencies, or conflicting/opposing adequacy records
   stop before evaluating any equation.
4. Verify exact validation-plan, port, and unit bindings. Every equation input
   must come from a numeric context condition with a declared uncertainty and
   its own numeric applicability criterion. No free input override exists.
5. Run a fresh, nonempty known-answer harness. Failure or indeterminacy stops.
6. Run a fresh, nonempty null harness. Failure or indeterminacy stops.
7. Compute the nominal result; exceptions and non-finite/non-real results are
   INSTRUMENT failures, not PHYSICAL failures. No partial outputs are retained.
8. Record applicability and the full diagnostic/evidence trail alongside the
   calculation, without promoting physical or parent-toolkit claim support.

The default without physical/empirical adequacy evidence is a provisional
calculation in a resolved candidate domain, with applicability UNKNOWN and the
physical axis UNTESTED. This is deliberate: numerical exploration must be
possible without pretending that the exploration established physics.
Missing adequacy evidence is the only UNKNOWN prerequisite allowed through.

## Substitution and failure ownership

`ExperimentalDiagnostics` belong to the context and stay with the fixed
`Experiment`. Measurement or determination failures therefore survive equation
substitution and keep the replacement blocked. A foreign-context snapshot
cannot be silently attached.

`ScopedDiagnostics` passed to `execute()` belong to a specific
description/context pair. They describe equation-specific diagnostics, not
general measurement/design status. A replacement must supply its own scoped
diagnostics. Failures of the old equation's own arithmetic tests do not condemn
the new equation; the new adapter must pass fresh tests instead.

`substitute()` links to the previous result by digest and leaves it unchanged.
It does not inherit outputs, physical assessments, dependency states, or harness
certificates. A new equation cannot be qualified with an old plan. Context-level
diagnostics are preserved as part of the experiment, not discarded.

## Numeric and safety limits

The expression interpreter uses `ast` parsing and explicit operations, never
`eval`. It accepts finite real constants, declared input names, unary signs,
addition, subtraction, multiplication, division, and bounded powers. Calls,
attributes, indexing, imports, comprehensions, arbitrary Python, excessive
expression length/nesting, and unsupported engine versions are rejected.
All input, intermediate, and output numbers must be finite reals, excluding
booleans; runtime exponent magnitude is limited to 100.

This is API-level diagnostic enforcement, not a security sandbox against
hostile Python that imports private functions, alters objects, or rewrites the
runtime. Source references and supplied diagnostic judgments are recorded, not
semantically authenticated. The interpreter's implementation must be versioned
when its behaviour changes; the recorded engine version is not a proof of
runtime integrity.

The shared known-answer/null harnesses now preflight every case before invoking
an instrument. Empty expectations, missing or negative/non-finite tolerances,
duplicate IDs/names, and non-finite expected values cannot produce vacuous
passes. Invalid criteria are DETERMINATION failures; invalid instrument outputs
are INSTRUMENT failures. A NaN cannot evade a tolerance comparison.

Declared unit equality is checked, not dimensional algebra. Inputs are nominal
values; their uncertainty remains in the context, but uncertainty propagation
is not implemented. Output uncertainty is `null`/UNKNOWN, never zero. No
computed number is automatically used as a sensitivity-qualified absence,
return-to-anchor result, continuity finding, or lifecycle transition. Those
remain separate diagnostic determinations. The equation harness does not
validate the physical observer.

## Running the example

From the repository root:

```sh
cd experimental
python3 -m playground.equations.example
python3 -m unittest playground.validation.test_substitution
python3 -m playground.self_check
```

The example replaces `y = x` with `y = 2*x` in an identical constructed
experiment. Both run the complete diagnostic path and emit linked JSON
records; their numbers differ, but neither gains physical support. The ledger,
test cases, source references, and all outputs are synthetic, not findings
about a real instrument. No test expectations are computed from the equation
under test.

Use `Equation`, `InputPort`, `OutputPort`, and `EquationRegistry` from
`adapter.py`; `Experiment`, `BoundaryProtocol`, `ValidationPlan`, `execute`, and
`substitute` from `substitution.py`. See `example.py` for an inspectable complete
protocol. All checks are standard-library-only and run offline.

## First graph family

`FiniteGraph` and `BondPercolation` from `percolation.py` provide bounded,
undirected finite-graph bond percolation through that same runner. The
[family specification](PERCOLATION.md) documents graph/boundary selection,
independent occupation, exact enumeration with floating-point arithmetic,
component outputs, finite-grid criterion brackets, and physical limits.

```sh
python3 -m playground.equations.percolation_example
python3 -m unittest playground.validation.test_percolation
```

The example accounts for a mathematical node universe, not physical energy.
Its successful graph calculations remain provisional. A missing edge or
nonspanning realization does not become a physical absence determination.
