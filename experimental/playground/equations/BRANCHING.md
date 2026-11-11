# Finite-horizon branching

Status: implemented experimental single-type, discrete-generation mathematical
instrument. Tests use constructed laws and exact finite answers, not physical
reproduction, observed cascades, calibrated sensors, or empirical adequacy.
Branching and percolation remain separate families with different investigated
properties; neither is a universal replacement for the other.

## Experimental questions

- **Who selected the process?** `OffspringLaw` and `FiniteBranching` retain
  decisions, criteria, evidence references, the exact selected law, and the
  separately versioned backend.
- **What is the scope?** Descendants of a fixed founder cohort, iid single-type
  offspring, discrete generations, no immigration and no interaction.
  Independence and homogeneity are selected mathematical definitions, not
  findings about a physical system.
- **What was anchored?** The nominal initial population must match a frozen
  `founder_count` anchor quantity and a matching dimensionless ledger account.
  Initial and final founder counts must agree, and all founder exchanges must
  be zero. This fixed-cohort bookkeeping does NOT conserve total population,
  energy, resources, or the number of descendants.
- **What is calculated?** The entire population distribution at a selected
  finite generation, conditional moments, extinction by that horizon, survival
  at that horizon, and expected cumulative population including generation zero.
- **What remains unknown?** Physical applicability, observation sensitivity,
  parameter uncertainty, model uncertainty, observed persistence, and
  infinite-horizon behavior are not established by these calculations.

## Exact law, bounded representation

The selected offspring law is an immutable tuple of distinct nonnegative
offspring counts and positive integer weights. An outcome with weight \(w_k\)
has probability \(w_k / \sum_j w_j\). These are exact rational model ratios,
NOT claimed empirical sample counts or fitted estimates. Unlisted outcomes
are zero within this selected mathematical law, not proven impossible
physical outcomes.

The first backend supports offspring counts 0–4, total weight at most
1,000,000, initial population 0–4, and generation horizon 0–8. It rejects
duplicate counts, fractional/negative/bool weights, unsupported process
definitions, and callback/subclass plugins.

The joint structural support must fit a complete population vector through
128. For nonzero founders this requires the initial count times the maximum
offspring count raised to the horizon not to exceed 128. A rare but possible
large outcome is not dropped just because it is unlikely. Zero founders are
absorbing without immigration and are handled directly.

An oversized problem is rejected before any calibration or nominal evaluation,
as an unsupported determination/protocol choice. There is no clipping,
conditioning on staying below a cap, hidden overflow bin, approximate tail,
or renormalization. The bounds describe this instrument's supported work,
not a physical population ceiling.

## Numerical method and its limits

Let \(f(s)\) be the offspring probability-generating polynomial, \(I\) the
founder count, and \(n\) the horizon. The backend composes \(f\) for a single
founder's finite descendants, then raises that distribution to \(I\) for
independent founders. Generation zero is a point mass at \(I\); zero founders
are a point mass at zero.

Polynomial coefficients use exact integer numerators with a common integer
denominator. Full probability mass is checked by exact integer equality.
Moments are formed from exact ratios before conversion to scalar output
floats. A negative, malformed, oversized, or mass-deficient distribution is
an instrument failure, never silently repaired.

Exported floating-point values are rounded. Every positive exact probability
must remain positive on export; underflow causes INSTRUMENT failure and retains
no nominal outputs. The mathematical law has not thereby failed. Survival is
calculated from the sum of positive-population probabilities, not
\(1-P(Z_n=0)\), because subtraction from a rounded extinction probability can
erase a real, tiny survival probability.

The fixed numeric output ports include probability at every count 0–128, mean
and variance of offspring, mean and variance of finite-generation population,
extinction and survival probabilities, expected cumulative population, and
checked probability mass. Structural zeros pad the vector outside the complete
selected support; no possible positive state is discarded.

Stochastic variance conditional on the selected law is NOT measurement,
parameter, or model uncertainty. Output determination uncertainty remains
UNKNOWN, not zero. An exactly selected integer cohort/horizon does not make the
physical application certain.

## Same diagnostic path, stricter cohort binding

Use `EquationRegistry`, `execute()`, and `substitute()` as for arithmetic and
percolation. `FiniteBranching` has no public `.run()` method, callback escape
hatch, independent PASS switch, or alternate laboratory runner.

The path checks:

1. Actual context, boundary, frozen anchor, experimental diagnostic bindings,
   and the anchored founder-cohort contract.
2. Fresh L0 accounting closure, including any separately declared physical
   quantities. A balanced exchange of founders still violates the fixed-cohort
   process even when generic count accounting balances.
3. All seven applicability coordinates, unresolved assumptions, UNKNOWN/stale
   dependencies, and physical/empirical assessment scope.
4. Exact adapter/context/validation-plan and input/output/unit bindings.
5. Discrete input domains and full-support bounds for EVERY diagnostic case
   before any case runs, plus zero declared uncertainty on nominal cohort and
   horizon.
6. Fresh nonempty known-answer and null harnesses, then all-or-nothing nominal
   calculation.

The scalar inputs are `initial` and `generations`, bound only to context keys
`initial_population` and `generation_horizon`, with unit `1`. Relationship
conditions `offspring_law` and `branching_definition` must match the exact law
digest and fixed process definition. Further applicability criteria may narrow
the supported ranges.

An old validation plan cannot validate a new adapter. A changed offspring law
requires a revised determination/context, not inherited physical evidence.
Experiment-level observer/design failures survive substitution. Optional
equation-specific findings stay scoped to their own description and context.
Without adequacy evidence, a successful calculation remains provisional:
applicability UNKNOWN, physical axis UNTESTED.

These are API-level diagnostic contracts, not a hostile-Python security sandbox
or semantic authentication of supplied evidence and assessments.

## Reports and generation profiles

`branching_report()` views recorded completed outputs without recalculating the
process. It separates conditional ensemble metrics from remaining uncertainty.
The offspring mean's relation to one is a comparison of the selected exact
ratios, not a universal regime or physical-threshold verdict.

`generation_profile()` accepts consecutive, increasing, completed gated
horizons. All other experimental conditions, adapter content and dependency
states must remain fixed. Each point keeps its own applicability and full run
digest; there is no aggregate physical-support promotion.

The profile is NOT a realized genealogy, simulated sample path, observed time
series, or continuity test. Increasing the selected observation horizon is a
determination change, not by itself evidence of physical reorganization.
Extinction is absorbing within this mathematical process, but a finite
extinction probability is not an observed physical disappearance.

Survival through a finite horizon is not eternal survival, stable organization,
system continuity, or configuration persistence. The instrument does not solve
an infinite-horizon fixed point, infer universal critical thresholds, or rank
branching above percolation. Physical absence still needs the separate
sensitivity-qualified observation and scoped-absence infrastructure.

## Example and verification

From `experimental/`:

```sh
python3 -m playground.equations.branching_example
python3 -m unittest playground.validation.test_branching
python3 -m playground.self_check
```

The example contrasts deterministic one-offspring reproduction with equal
probability of zero or two offspring. Both have mean one. For a single founder
at generation two, the stochastic law has population probabilities
\(P(0)=5/8\), \(P(2)=1/4\), \(P(4)=1/8\), while the deterministic law stays at
one. The same expected size therefore does not identify extinction behavior or
establish permanent organization.

The JSON includes full gated records and finite-generation reports/profiles.
The ledger accounts only for the selected founder cohort; it is not physical
energy/resource closure. Neither example supplies physical adequacy.

Tests compare full vectors against an independent exact `Fraction` census-state
Markov recursion across eight selected laws, multiple founder counts and
horizons. Separate moment/extinction recurrences, hand-stated distributions,
the maximum support case, and rare-survival cases cross-check the production
PGF method.

Planted defects cover false generation-zero extinction, probability-mass loss,
invalid distributions, canceled tiny survival, null-invented descendants,
nominal crashes/nonfinite/missing/extra outputs, stale bindings, discarded
experimental failures and inherited support. A forged-PASS probe must make the
anti-bypass guard fail by assertion, not by crashing. All checks use the standard
library and run offline; they do not establish real-system adequacy.
