# Context-dependent applicability mapping

Status: Implemented experimental record/matching layer with synthetic tests.
Physical adequacy, evidence truth, evidence independence, and real-system
applicability are not established by the software or its example.

The mapper answers two separate questions: does a context fall inside the
description's declared domain, and what do explicitly recorded assessments
support in that exact context? The first is a scope check; it cannot answer
the second. Descriptions remain replaceable, overlapping instruments, not
members of a universal hierarchy.

## Records and scope

- **Context:** records system description, revision, anchor content binding,
  uncertainty notes, and conditions in all seven determination coordinates:
  boundary, controls, observer, environment/energy, relationship structure,
  uncertainty, and anchor. A condition retains its selection/assumption/
  measurement/derivation basis and who chose it, why, and by which criteria.
- **Description:** records model identifier/revision, the specific property
  investigated, selected applicability constraints, assumptions, and UNKNOWN
  dependencies. All seven coordinates need an explicit criterion before the
  scope can be resolved. There are no implicit wildcards or universal domains.
- **Assessment:** records an assessor's judgment, evidence references,
  rationale, criteria, uncertainty, and optional typed diagnostic findings.
  It is bound to digests of the entire description and context. Judgments are
  inputs, not automated scientific conclusions.
- **Map cell:** retains the full context, description, per-condition matching,
  included assessments, excluded assessment IDs, diagnostics on all three
  failure axes, unresolved questions, dependency-state snapshot, and conditions
  requiring reassessment. The JSON report includes both content digests.

Selected boundaries remain selected boundaries. Assumed conditions and
unresolved model assumptions remain visible and prevent affirmative support;
record an investigated assumption as an explicit condition/criterion with its
actual evidence, rather than deleting it to obtain a favourable status.
Evidence reference presence is checked, but reference contents are not fetched
or semantically verified.

## Matching and uncertainty

Categorical constraints match literal strings. Numeric constraints are closed
intervals with exactly matching declared units. Numeric conditions carry
bounded uncertainty half-widths; `None` means unknown, never zero.

- **Inside:** the entire uncertainty interval fits inside the constraint.
- **Outside:** the entire interval is disjoint from the constraint.
- **Unresolved:** it overlaps an edge, lacks a bound/value, has incompatible
  units/types, or lacks a required coordinate or criterion.

No implicit unit conversion, probability calculation, monotonicity assumption,
interpolation, extrapolation, or physical-transition inference occurs.
A known outside constraint is sufficient to put the cell outside the domain;
other missing information and typed failures are still retained. Scope exit
is not a physical failure.

## Applicability states

| State | Meaning within this exact property/context |
|---|---|
| `supported-within-recorded-context` | At least one bound physical/empirical assessment supports it, with no opposing or unresolved adequacy assessment, unresolved prerequisite, or blocking finding |
| `contradicted-within-recorded-context` | Bound physical/empirical assessments oppose it, without support or unresolved prerequisites; this is not a global model refutation |
| `conflicting-evidence` | Both supporting and opposing adequacy judgments remain; no majority vote or tie-break is applied |
| `unknown` | Missing/inconclusive evidence, scope information, uncertainty, assumptions, or prerequisites |
| `outside-declared-domain` | A context constraint is demonstrably outside the selected domain, without declaring the model false |
| `blocked-determination` | Instrument/determination failure or stale UNKNOWN reliance prevents a conclusion inside the candidate domain |

Mathematical and diagnostic assessments are retained but cannot generate
physical/empirical support. Typed failures remain independent of applicability
labels: the mapper does not automatically manufacture `PHYSICAL OK` or
`PHYSICAL FAILED` from any label. A supplied physical failure cannot be
overridden by a favourable assessment; reconciliation remains UNKNOWN.

## Dependencies and revision

The mapper consults explicitly supplied UNKNOWN states using the existing
`stale_reliance` checker. Missing or open UNKNOWN dependencies keep a cell
UNKNOWN; expired or superseded ones block the dependent determination.
It does not poll an external source, infer expiry triggers, or change the
system track. Revising a context, description, property, provenance, anchor,
or uncertainty changes its content binding; old evidence is excluded from
the new cell, not copied across automatically.

Scope constraints describe candidate applicability regions. Support applies
only to supplied exact contexts, never every point in a candidate region.
Thus two descriptions may overlap and both be supported, one may have a gap,
and neither needs to outrank the other. A finite observation window must be an
explicit condition if conclusions depend on it; the example uses a 10-second
window and cannot support permanent organization.

## Running and using it

From the repository root:

```sh
cd experimental
python3 -m playground.applicability.example
python3 -m unittest playground.validation.test_applicability
python3 -m playground.self_check
```

The example emits JSON to stdout. It constructs two descriptions at four
contexts: both supported at one point, only one supported at a second, both
unresolved at an uncertainty-straddled edge, and both outside at another.
All judgments and references in the example are synthetic fixtures, not
experimental findings. No equations are added in this milestone.

The Python entry points are `assess(description, context, assessments, ...)`
and `build_map(descriptions, contexts, assessments, ...)`. For maps, diagnostic
records use `(description.digest(), context.digest())` keys, keeping failures
cell-local; for single assessments the caller must supply diagnostics belonging
to that exact context. `ApplicabilityMap.to_dict()` / `.to_json()` produce
inspectable reports without changing claim support in the parent toolkit.
