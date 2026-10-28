# Card 02 — Premise traceability (the register map)

**Provenance:** upstream executable, `method-layer/premise-traceability/register_map.py` (commit `365669b`, stdlib, CC0). Ported from GIS: a layer will not load without projection and datum; blank is a value; silent coarsening is the failure mode. This card reuses the upstream vocabulary with minimal change. Status: upstream executable, used as a *recording* discipline, not as code you must run — the vocabulary is the tool.

## Purpose

Hold each declared claim as a **layer** with its measurement declaration attached, so that two claims are only combined when their declarations permit it. The tool does not rank, judge truth, or infer. It catches two failures: joining layers whose declarations forbid it, and silent coarsening.

## The layer declaration

Every layer requires — no defaults, no guesses, a missing required field is an error naming every missing one:

| Field | Meaning |
|---|---|
| `measurand` | what was measured, not what it is called |
| `range` | sector / domain where it holds |
| `instrument` | what produced the number, **including the scaffold/harness** — the datum |
| `grade` | one of the six grades below |
| `resolution` | coarseness, stored as a value, never as an absence |

## The six grades

- `MEASURED_PRESENT` — measured, something there
- `MEASURED_ABSENT` — measured, nothing there
- `MEASURED_DISCARDED` — measured, dropped (requires a `discard_rule`)
- `UNMEASURED` — not measured
- `UNDERPOWERED` — measured with too little information to answer
- `IMPOSED` — asserted without measurement (requires a `reason`)

Blank is a value: `NODATA` (region exists, not measured) and `NOTFOUND` (region measured, nothing there) are distinct and never collapse to zero or null. A field may carry the sentinel `UNDECLARED` — the declarant *states* the absence, which is retained as data. `MEASURED_DISCARDED` without a discard rule, or `IMPOSED` without a reason, loads but is flagged **worse than `UNMEASURED`**: handling occurred and was not declared.

## Joining

`can_join(a, b)` checks measurand, range, grade, then instrument last, and returns one of:

- `COMMENSURABLE` — may be combined
- `UNJOINED(measurand)` — different measurands, no declared relation; **closable** when the bridging measurement arrives
- `INCOMMENSURABLE(field)` — values disagree on the named field; do **not** join
- `UNDECLARED(field)` — the named field is the sentinel

Three non-joins, three different next actions — never one blanket "incompatible."

## Application to a publication

1. For each claim from Card 01, write the layer declaration. Most of the work is finding the `instrument` field: the exact task, assay, or scaffold that produced the number. If the publication does not state it, the grade is `IMPOSED` or `UNDECLARED`, and that is the finding.
2. When the publication compares its result to prior results (or you do), run the join check on the two layers. `INCOMMENSURABLE(instrument)` on a "replication" is a specific, actionable finding: the studies did not measure the same thing.
3. Watch for `MEASURED_DISCARDED` without a discard rule — exclusions, outliers dropped, conditions removed — the highest-value catch in the whole card.

## Limits

- Upstream `project()` supports coarsening only (integer factor, never upsample); this card uses the vocabulary, not the projection machinery.
- The register map records declarations; it cannot tell you whether a declaration is honest.
