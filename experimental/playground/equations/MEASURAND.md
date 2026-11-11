# Measurand identity under equation substitution

Status: Implemented experimental identity declarations, comparison eligibility
and constructed adversarial tests for arithmetic output ports. This does not
establish physical measurand identity, calibrated route equivalence, empirical
adequacy, or a general ontology of quantities.

## Experimental question

Can two descriptions have the same output name, units and nominal value,
pass their own known-answer and null harnesses, and still describe unlike
quantities? The constructed challenge says yes, and tests that the playground
retains both calculations while refusing the inference of agreement.

The design is informed by the distinction between quantity identity and
measurement route in
[Simulators measurement-fork](https://raw.githubusercontent.com/JinnZ2/Simulators/34eb3cfbf42d3947092858f6b8449da550eed125/measurement-fork/README.md).
No source code is vendored or executed from that repository, and no claim
about its whole-tree runtime behavior is made.

## Declared identity and route

`Measurand` binds seven explicit identity coordinates:

- **Quantity:** the property being investigated, not its output symbol.
- **Object-of:** the selected object or relationship the quantity concerns.
- **Normalizer:** the selected denominator; explicit `raw` means
  unnormalized, while `None` remains unknown.
- **Population:** the selected membership or cohort.
- **Time window:** the selected temporal scope.
- **Spatial scope:** the selected region or boundary.
- **Reference state:** the selected reference or anchor.

The protocol is recorded separately as a declared route, not an identity
coordinate. Each declaration also retains a selection decision and nonempty
evidence references. Those pointers are provenance records, not proof that
the declared identity or route is physically correct.

Missing coordinates use `None`, not a guessed default. Empty fields and
common unknown-placeholder strings are rejected rather than treated as
matching identifiers. Declared strings are compared exactly; there is no
semantic alias resolution or implicit transformation.

## Substitution path and comparison path

`OutputPort.measurand` is optional so existing constructed calculations do
not acquire invented metadata. When supplied, the complete declaration,
including route, decision and evidence, enters the equation digest and hence
the description digest used to bind adequacy assessments.

Every replacement still calls `substitute()` and the full existing runner:
protocol binding, fresh L0, applicability, exact validation-plan binding,
known-answer harness, null harness, then nominal calculation. The identity
layer does not skip, replace or certify any of those stages.

`compare_substitution()` accepts the two retained run records, an explicit
output mapping and a selection decision. It requires exact parent linkage,
the same fixed experimental snapshot, completed diagnostic results and
content-bound plans. It records identity eligibility separately:

| Condition | Identity | Comparison | Point difference |
|---|---|---|---|
| Complete matching declarations, declared routes, bound completed runs and units | Same declared measurand | Eligible for declared point comparison | Replacement minus previous |
| Any known difference in identity | Different declared measurands | VOID | Withheld |
| Missing identity, including both declarations missing | UNKNOWN | Withheld | Withheld |
| Matching identity, undeclared route | Same declared measurand; route unknown | Withheld | Withheld |
| Matching identity, different declared routes | Same declared measurand; routes differ | Eligible only if other prerequisites hold | Point difference only |
| Failed/blocked calculation, broken lineage, missing output, or unit mismatch | Identity assessed separately where possible | Withheld unless already VOID | Withheld |

A known mismatch is not hidden by another missing coordinate. Both the
mismatch and the unresolved field remain in the report. A finite-output
subtraction that overflows is an INSTRUMENT failure, not a physical verdict.

## Failure ownership and retained uncertainty

Known unlike identities fail the comparison's DETERMINATION axis. They do
not change the physical or instrument status of either run, erase an output,
or prove either description wrong. A missing declaration is an indeterminate
determination, not an instrument failure or a negative physical finding.

Existing run findings remain in the comparison record, including instrument
failures and the absence of physical adequacy evidence. Even an eligible
nominal comparison can therefore retain an INDETERMINATE determination axis
from unresolved physical applicability; eligibility is not a general verdict.

Output uncertainty remains unknown. A zero point difference is not an
agreement or compatibility test; a nonzero point difference does not by
itself establish physical failure. No ratio, uncertainty propagation,
significance threshold or coverage probability is supplied by this layer.

## Reproduce and inspect

From the repository root, use a fresh output directory. The generator refuses
to overwrite an existing directory so earlier evidence remains intact.

```sh
PYTHONPATH=experimental python3 -m unittest playground.validation.test_measurand
PYTHONPATH=experimental python3 -m playground.equations.measurand_example \
    --output-dir /tmp/fresh-measurand-substitution-probe
./run_checks.sh
```

The example emits Markdown and JSON for fifteen constructed cases, including
every identity coordinate, missing identity, missing route, a changed output
symbol, numerical disagreement and a failed known-answer harness. Each
comparison retains both complete run snapshots, declarations, decisions,
evidence pointers, remaining unknowns and exact run digests.

The test suite additionally plants units/numbers-only matching, unknown-as-
match, protocol-as-identity and physical/determination-axis conflation.
The guard checks require assertion failures from those mutants, not test
crashes. The suite is part of `playground.self_check` and the existing
repository checks; CI also captures the generated evidence per interpreter.

## This does not do

- **Physical authentication:** matching declarations do not establish
  physical sameness, calibration, valid observation or empirical support.
- **Route equivalence:** different protocols are recorded, not proven
  unbiased, equally sensitive, interchangeable or calibrated.
- **Automatic identity:** property labels, output symbols, equal units,
  equal numbers and diagnostic success never supply a missing measurand.
- **Conversions:** no aliases, unit conversion, rebinning, population
  transport, reference transformation or mathematical identity proof is
  inferred. Such bridges need their own explicit future protocols.
- **Input ontology or family migration:** this milestone qualifies arithmetic
  output comparisons. It does not infer input identities or automatically
  annotate graph/branching metric ports or retrofit earlier audit pilots.
- **Global enforcement:** extracting raw values and comparing them in
  arbitrary external code is not prevented. This is the supported scoped
  comparison API, not a security sandbox or runtime attestation mechanism.
- **Historical repair:** earlier source records, correction specimens and
  unresolved findings are not rewritten. New arithmetic records include the
  optional declaration field in their content digests; old digests are not
  promised to remain identical after the record schema gains that field.
- **Cross-track promotion:** no absence, continuity, permanent organization,
  lifecycle state, physical support or parent-toolkit claim support follows.
