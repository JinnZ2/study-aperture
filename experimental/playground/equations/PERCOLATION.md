# Finite-graph bond percolation

Status: implemented experimental mathematical instrument, with constructed
diagnostic tests. This is not a validated physical network model, a calibrated
physical observer, or a determination of an infinite-system critical threshold.
[Finite-horizon branching](BRANCHING.md) is a separate implemented family,
not an equivalent model or replacement for percolation.

## Investigated questions

- **Which system was selected?** `FiniteGraph` records the node universe,
  possible undirected edges, disjoint source and target subsets, who chose
  them, why, criteria, and evidence locations. These selections are not
  independently established physical boundaries or couplings.
- **Which configuration is being examined?** A supplied integer mask selects
  occupied edges. Bit `i` refers to edge `i` in the recorded tuple. All nodes,
  including isolated nodes, remain part of the investigated graph.
- **What connects the selected boundaries?** Spanning means an occupied path
  joins ANY source node to ANY target node. The sets must be nonempty and
  disjoint; there is no implicit geometric boundary convention.
- **What changes under an occupation rule?** A second calculation enumerates
  every mask under independent, identically distributed bond occupation with
  probability `p`. Independence is a selected mathematical definition, not a
  physical finding about a measured network.
- **What supports the result?** The complete run retains L0, applicability,
  known-answer and null checks, uncertainty, provenance, dependencies, and
  remaining conditions. Diagnostic success is not physical support.

The supplied configuration and the ensemble at `p` answer different questions.
The code does NOT assert that the mask was randomly sampled at `p`; no random
generator or seed is used. A nonspanning supplied mask can coexist with a
positive ensemble spanning probability without contradiction.

## Closed backend and gates

`BondPercolation` is a declarative adapter accepted by the same
`EquationRegistry`, `execute()`, and `substitute()` as arithmetic equations.
There is no public graph `.run()` method, alternate experimental runner,
callback registration, expression escape hatch, or exemption from diagnostics.
The registry accepts exact built-in adapter types only, not arbitrary
subclasses overriding their behavior.

The versioned backend is `finite-undirected-bond-enumeration/1`. Its fixed
occupation law, ordered graph, boundary sets, provenance, applicability
criteria, dependencies, and revision are content-bound. Different edge order
changes mask interpretation and therefore changes the digest. Node order
changes component-label encoding and is also retained.

Execution follows the existing path:

1. Verify actual anchor and experimental/protocol content bindings.
2. Recompute L0; failure or indeterminacy stops before graph evaluation.
3. Check applicability, assumed/unresolved prerequisites, dependency states,
   and experiment-level measurement/design findings.
4. Check the exact adapter/context/plan and port/unit contracts, plus the
   graph's discrete and probabilistic input domains.
5. Run fresh, nonempty known-answer and null harnesses.
6. Calculate all nominal outputs or retain none on instrument error.
7. Preserve the full determination record without promoting physical support.

Invalid late harness inputs are preflighted before ANY case runs. A fractional
mask is a determination/protocol failure, not silently rounded. Nonfinite,
missing, or unexpected backend outputs are instrument failures. A correct
replacement cannot discard a fixed experiment's failed observer or design
diagnostics. A new graph/boundary cannot inherit the old graph's evidence.

The private numerical primitives are testable implementation details, not
supported laboratory entry points. As with arithmetic adapters, this is
API-level enforcement, not a security sandbox against hostile Python or
authenticated proof of the runtime implementation.

## Inputs and applicability

The fixed scalar ports are `p` and `mask`, bound respectively to numeric context
conditions `bond_probability` and `occupation_mask`, both with declared unit
`1`. The mask must be exactly integer-valued and have zero declared uncertainty;
`p` must lie in `[0, 1]`. Numeric applicability criteria may narrow these
ranges. Unknown input uncertainty, assumptions, or straddled scope bounds
remain blocking prerequisites under the existing mapper.

The context and adapter must agree exactly on:

- **Graph:** `graph` in the relationships domain equals `FiniteGraph.digest()`.
- **Occupation law:** `occupation_law` in the relationships domain equals
  `independent-uniform-bonds`.
- **Experiment:** all seven determination coordinates remain required.

The initial backend supports 2–32 nodes and at most 12 edges, allowing at most
4096 enumerated states per evaluation. Duplicate/reversed duplicate edges,
self-loops, undeclared endpoints, overlapping boundary sets, unsupported laws,
and unversioned engines are rejected rather than assigned hidden semantics.
There are no directed, weighted, correlated, site-occupation, growing-network,
or infinite-network variants in this milestone.

## Outputs and finite transition behavior

For the supplied mask, outputs include spanning, component count, largest
component size, occupied-edge count, and a canonical component label per node.
Labels use the smallest node index in each component. The report reconstructs
labeled node groups from those recorded outputs, without rerunning a graph
algorithm.

For the ensemble, the backend sums each configuration's contribution with
weight \(p^k(1-p)^{m-k}\), where \(m\) is the number of possible edges and \(k\)
the occupied count. It reports spanning probability, expected component count,
and expected largest-component size. Enumeration is exhaustive; the arithmetic
is floating point, not symbolic or exact rational arithmetic.

`finite_transition_bracket()` uses completed gated runs on a strictly
increasing supplied `p` grid. All other experimental conditions, adapter
content, and dependency states must stay fixed. The selected probability
criterion has its own who/why/criteria record. It returns an adjacent grid
bracket, or explicitly says the criterion was already met at the grid start
or was not reached on the supplied grid.

There is no interpolation, extrapolation, inferred threshold uniqueness,
confidence interval, infinite-size critical point, or physical transition
claim. Changing the selected probability criterion can change the reported
bracket without any physical-system change. The bracket is a grid-resolution
statement about the selected finite mathematical ensemble.

## Uncertainty, absence, and physical limits

Output uncertainty remains UNKNOWN, not zero. Nonzero bounded `p` uncertainty
is retained in a nominal run but is not propagated to ensemble outputs.
The finite-grid bracket helper rejects nonzero `p` uncertainty rather than
presenting an unqualified crisp bracket.

A disconnected graph/mask does not prove absent physical coupling. A clean
mathematical null does not calibrate an observer's ability to see missing or
weak edges. Existing sensitivity and scoped-absence determinations remain
separate; without sensitivity, an attempted physical absence claim is rejected.
The example's observer is a constructed graph readout, not a physical sensor.

The example declares a complete ledger for a FIXED MATHEMATICAL NODE UNIVERSE,
with selected node counts and zero node exchanges. Its L0 pass is not energy
closure or proof that all relevant physical exchanges have been accounted for.
A physical application must specify and justify its relevant quantities,
controls, observer coupling, environment, boundary, and evidence separately.
No energy law, empirical applicability, continuity, return, organization, or
lifecycle transition is inferred by this graph family.

## Verification and example

From `experimental/`:

```sh
python3 -m playground.equations.percolation_example
python3 -m unittest playground.validation.test_percolation
python3 -m playground.self_check
```

The example uses a two-edge chain with hand-stated partitions and the
polynomials \(P_{\mathrm{span}}=p^2\), \(E[C]=3-2p\), and
\(E[L_{\max}]=1+2p\). It emits full JSON run records, labeled reports, and
the finite-grid bracket for a selected spanning probability of 0.5.
No physical adequacy is supplied; applicability remains UNKNOWN.

The tests additionally use independent transitive-closure reachability and
exact `Fraction` sums to check every mask at `p=0, 0.5, 1` across chains,
cycles, a star, disconnected graphs, an edgeless graph, multiple boundary
nodes, and a small mixed graph. Independent hand-stated chain, triangle, and
cycle polynomials cross-check the oracle. Production expected answers are
never generated by the production backend under test.

Planted defects include invented spanning, lost isolated vertices, a dropped
bridge, null false positives, nominal-only crashes/nonfinite/incomplete
outputs, stale bindings, and discarded experimental diagnostics. A forged-PASS
probe verifies that the anti-bypass test actually fails under that mutation.
Everything uses the standard library, offline. These checks validate bounded
mathematical behavior and diagnostic enforcement, not real-system physics.
