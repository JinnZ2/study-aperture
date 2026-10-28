# Card 03 — Agreement, independence, and early indicators

**Provenance:** three upstream executables from Simulators `@0655e8b`: `tools/false_agree.py`, `tools/provenance_graph.py` (both vendored in `../vendored/`, with a scoped adapter `safe_provenance.py`), and `tools/presignal_ledger.py` (referenced, not vendored — run from the upstream repo). Status: upstream executable; this card describes how to apply them to a study's evidence base — **and how not to over-read their outputs.**

## Purpose

Density is not truth. A literature where many studies agree can be one source echoed downstream, several groups defining the term differently, or genuine independent convergence. These tools route the agreement by cause. They do not count, do not vote, and do not judge truth.

## 1. `false_agree.py` — route an agree-set

For each agreeing study, record: id, claim, definition, population, method, and **lineage** (the source the claim/data traces to — name the *specific* data source; generic strings like "independent data collection" misroute as `SHARED_UPSTREAM`). The tool routes each pair:

| Route | Meaning |
|---|---|
| `SHARED_UPSTREAM` | both trace to the same source → agreement is one source echoed |
| `FALSE_AGREE_DEFINITION` | same conclusion word, different definition or population → not the same claim |
| `FALSE_AGREE_MEASURE` | incompatible instruments → not the same measurement |
| `UNDERDETERMINED` | lineage missing → agreement not yet real |
| `INDEPENDENT_CONVERGENCE` | distinct lineage, comparable as far as recorded |

**Assessor's caution:** these routes are *field mismatches requiring review*, not verdicts. A string difference in the recorded definitions proves a recorded difference, not an incompatibility; different methods or populations do not automatically mean false agreement. The route tells you where to look; the judgment about whether the difference is load-bearing is yours and must be recorded as such.

Set-level rule carried over from upstream: any shared-upstream or false-agree pair downgrades the whole dense bin. **Assessor's caution:** treat that as the upstream tool's rule, not an inference license — when a pair routes badly, identify *which* pairs are affected and retain the independently supported portions. Do not let one dependent pair erase the rest of the evidence set. Missing provenance returns `UNDERDETERMINED`, never a verdict.

## 2. `provenance_graph.py` — prove lineage independence

Nodes are claims/datasets/assumptions; edge A→B means "A derives from B." Two studies are independent iff their ancestor sets are disjoint. Any shared node is a **witness** — shared ancestry is proven; whether that makes the agreement "one source echoed" depends on **what the shared node contributes** (a methods paper everyone builds on is different from one dataset everyone re-analyzes). Inspect the witness; do not score it. Decidable, deterministic, cycle-safe; judges no truth.

```
python3 ../vendored/safe_provenance.py check prov.json Ranehill2015 Ronay2016
python3 ../vendored/safe_provenance.py checkset prov.json S1 S2 S3
```

Prefer the scoped adapter `safe_provenance.py`, which renames the raw outputs to what is actually proven and refuses unknown nodes (the raw tool returns `INDEPENDENT` for nodes not in the graph — silently wrong):

- `NO_SHARED_ANCESTOR_IN_DECLARED_GRAPH` — proves a property of the declared graph only; does **not** establish real-world independence.
- `SHARED_ANCESTOR_IN_DECLARED_GRAPH` — shared ancestry is proven; whether that makes the agreement "one source echoed" depends on **what the shared node contributes** (a methods paper everyone builds on is different from one dataset everyone re-analyzes). Inspect the witness; do not score it.

**The check that matters for a literature:** do the "many studies" that agree share a common ancestor — one dataset, one re-analysis, one influential paper everyone cites? If they do, shared ancestry is proven; what it *means* (one measurement echoed, or one shared input that many datasets each test independently) is an inspection of the witness, not an automatic verdict. And remember the dual reading: replications typically share a *methods* ancestor but not a *data* ancestor — build both graphs and say which one you mean.

## 3. `presignal_ledger.py` — early indicators (optional, upstream)

For a study claiming an index or marker predicts something: the upstream tool scores an early index by its lead gain over the baseline signal and its lift over chance. Use when the publication's central claim is prognostic. Do not transplant its scoring to non-prognostic claims.

## Limits

- An incomplete graph can only return "no shared ancestor found in the declared graph" — never "independent in the world."
- `false_agree` routes by the fields you record; recording nothing yields `UNDERDETERMINED` everywhere.
- These tools route agreement. Whether the agreement is *correct* is a different question (Cards 01, 02, 04).
