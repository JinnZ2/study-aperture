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
4. For any average used as an input, run the frozen-state check below.

## Averages used as inputs (frozen state)

*Toolbox addition, 2026-10-28; not in upstream `register_map.py`. Arose from [examples/reproducibility-model](../examples/reproducibility-model/FINDINGS.md).*

An average is a state variable only where the system is at equilibrium: the average over time equals the average over the population. A literature, a workforce, a market or an ecosystem under selection is a flow. A mean taken from it is a snapshot of that flow. Used as a fixed model input, it freezes the flow into a constant, and the gradients (where the quantity varies, how fast it moves) drop out.

```
what the average stands for              what enters the model
───────────────────────────              ─────────────────────
a distribution over units          ──►   one number
  (by field, era, site, design)
a flow under selection over time   ──►   a constant
```

For every average that enters a claim as an input (a prevalence, a base rate, a mean effect, a typical value), the layer declaration states:

| Field | Question |
|---|---|
| population | averaged over which units? |
| window | averaged over which period? |
| stationarity | is the population assumed not to change within and beyond the window, and is that `ASSESSED`, `ASSUMED`, or `UNASSESSED`? |

- An average with none of the three stated is graded `IMPOSED`, with the reason "frozen across an unstated population and window."
- An average stated but carried outside its window or population is an `INCOMMENSURABLE(range)` join, not a fit.
- Where a single average is split into two to fit two subsets (one per observed rate), record the split: it is the distribution reappearing, and each split adds a free value.
- A fitted average that reproduces one observed rate carries no information about mechanism. One free number can fit one number.

Not a rule against averages. A stated, stationary, in-range average is an ordinary input. The check is that the freezing is declared.

## Limits

- Upstream `project()` supports coarsening only (integer factor, never upsample); this card uses the vocabulary, not the projection machinery.
- The register map records declarations; it cannot tell you whether a declaration is honest.
