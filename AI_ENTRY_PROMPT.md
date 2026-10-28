# AI entry prompt

Copy-paste this into any capable LLM together with the study's text (or its abstract), and paste the method cards from `cards/` if the model cannot read files. The prompt is written so the model does the assessment the cards describe and returns the structured record — no Python needed.

---

You are assessing a publication using the study-aperture method cards. Your job is to route, extract, and record — not to judge scientific validity or produce a quality score. Missing values are values (`UNDECLARED`, `NODATA`, `NOTFOUND`); never convert an absence into a negative finding, a zero, or a completion. A claim without an evidence location is not yet a claim.

Work through these steps in order:

Throughout: for every substantive finding you state, retain the source location it came from (URL, page, table, or passage). A finding without a source location is not yet a finding.

1. **Route.** Give the publication one type: EMPIRICAL, REVIEW, THEORETICAL, SIMULATION, COMMENTARY — or UNDECLARED if the material in hand is insufficient. State what material you actually hold (full text, abstract only, etc.) and what the assessment is FOR (decision context); if the decision context is absent, state downstream implications conditionally, never as recommendations. The type gives DEFAULT cards; applicability is ultimately per-claim and per-input — a commentary citing empirical lineage still gets the independence checks on that lineage; record any out-of-default card run and why. Apply the cards that fit; for the rest, return NOT_APPLICABLE — that is a legal output, not a failure. Before any card runs, do the ordinary study-design checks (confounding, selection, measurement validity, uncertainty, multiplicity, missing data, preregistration) and record their state.

2. **Claims.** List each claim with: id, verbatim text (quote, do not paraphrase), evidence location (table/figure/page/derivation step — or NO_EVIDENCE_LOCATION), measurand (what was measured, not what it is called), conditional form if if-then, and its falsifiers (what would have to be observed for it to be wrong, and whether the publication reports testing them).

3. **Premises.** For each claim write the layer declaration: measurand, range, instrument (the exact task/assay/scaffold — the datum), grade (MEASURED_PRESENT, MEASURED_ABSENT, MEASURED_DISCARDED, UNMEASURED, UNDERPOWERED, IMPOSED), resolution. Flag MEASURED_DISCARDED without a discard rule and IMPOSED without a reason — those are worse than UNMEASURED. When two claims or studies are combined, state whether they are COMMENSURABLE, UNJOINED, INCOMMENSURABLE(field), or UNDECLARED(field). For every average that enters a claim as an input (a prevalence, base rate, mean effect, typical value), state its population, window, and stationarity (ASSESSED with a basis, ASSUMED, UNASSESSED, or UNDECLARED). An average with none of the three stated is FROZEN: grade the claims resting on it IMPOSED or UNDECLARED, never MEASURED_*. Record whether it was fitted to the result it reproduces, split into several values to fit subsets, or estimated from a different population than the one it is used for.

4. **Agreement and independence.** If the publication cites supporting studies, route each pair: SHARED_UPSTREAM (both trace to one source), FALSE_AGREE_DEFINITION (same words, different definition/population), FALSE_AGREE_MEASURE (incompatible instruments), UNDERDETERMINED (lineage missing), or INDEPENDENT_CONVERGENCE. These routes are field mismatches requiring your review, not verdicts. When a pair flags, assess that pair individually and retain the unaffected evidence — do not let one dependent pair erase the rest of the set. Name the specific data source for lineage (generic strings misroute).

5. **Alternative explanations.** List the candidate explanations for the central finding, including the authors' preferred one. For each, state the cheapest observation that would distinguish it and whether the study ran it. Explanations never tested are open branches, not eliminated ones. Each elimination is itself a result.

6. **Position and scope (only if material supports it).** Would the same behavior be classified differently if the describer were inside vs. outside the described population? Does the key term mean the same thing to all parties citing it? Does any claim violate a lower layer (physics, thermodynamics, biomechanics) before its statistics matter? Which background conditions does the design assume stable, and are they ASSESSED, ASSUMED, or UNASSESSED? (An unassessed factor is unknown — not established as unstable.)

7. **Labels and records.** Label every claim OBSERVED, DERIVED, or PROPOSED — including your own assessment statements. Distinguish the question the work was aimed at (target) from what was written (rendering): removing a rendering does not close its target. If you decline to read or score something, say so and give the reason (a gate may block scoring, never reading).

8. **Decisions.** List the decision surfaces the reader's actual decision turns on, each with state DETECTED, UNRESOLVED, RESOLVED (answer + named author), DEFERRED (with reason), or NOT_APPLICABLE. Never silently resolve anything; never substitute a default for an unknown. Keep confidence in the claims separate from whether the claims justify action.

Then return, in this exact structure:

```
PUBLICATION: <title> | TYPE: <one of the six> | MATERIAL HELD: <...> | DECISION CONTEXT: <...>
DESIGN CHECKS: <state of each ordinary check; UNDECLARED if not inspectable with material in hand>
CLAIMS:
- C1 [OBSERVED|DERIVED|PROPOSED] "verbatim" | evidence: <loc or NO_EVIDENCE_LOCATION> | grade: <...> | support: <SUPPORTED|PARTIALLY_SUPPORTED|UNSUPPORTED|CONTRADICTED|UNTESTED|UNDETERMINED> | falsifiers: <...>
INPUT AVERAGES:
- A1 "<what is averaged>" = <value> | population: <...> | window: <...> | stationarity: <ASSESSED (basis)|ASSUMED|UNASSESSED|UNDECLARED> | claims: <ids> | fitted to / split of / estimated from: <...>
INDEPENDENCE: <pairwise routes, or NODATA>
OPEN BRANCHES: <untested candidate explanations>
ASSUMED STABILITIES: <ASSESSED/ASSUMED/UNASSESSED list, or NODATA>
DECLINED: <what you did not read or score, and why; or none>
DECISIONS:
- D1 <surface text> [UNRESOLVED|...] — conditional implication if context unknown
INCOMPLETENESS: <everything that keeps this assessment from counting as complete; the headline, not the footnote>
```

If the material in hand is insufficient for a step, say BLOCKED or NODATA for that step — an incomplete assessment that says so is worth more than a complete-looking one that doesn't.

## Handoff to the CLI record

Each block of the structured output above maps onto the `assess.py` record (`python3 assess.py`, stdlib only). Keep the URL or location in the field:

| AI output block | CLI command |
|---|---|
| header line | `init --title ... --type EMPIRICAL --citation <url> --materials "<what you actually read>" --context "<decision it is for>" |
| DESIGN CHECKS lines | `design --check confounding --state CHECKED --finding "..." --source <url>` |
| each CLAIMS line | `claim --id C1 --text "<verbatim>" --evidence "<location or empty>" --support <grade> --label <OBSERVED|DERIVED|PROPOSED> --grade <measurement grade> --falsifiers "<...>" --source <url>` |
| each INPUT AVERAGES line | `average --id A1 --text "<what is averaged>" --value <v> --population "<...>" --window "<...>" --stationarity <ASSESSED|ASSUMED|UNASSESSED|UNDECLARED> [--basis "<...>"] --claim C1 [--split-of A0] [--fitted-to "<...>"] [--estimated-from "<...>"] --source <url>` |
| each card run | `tool --id T1 --card 03 --state RUN --output "<finding + source location>" --source <url>` (or `--state DECLINED --declined-reason "..."`) |
| each DECISIONS line | `decide --id D1 --text "<surface>" --state UNRESOLVED` |
| a resolved decision | `resolve --id D1 --by <user|assessor> --answer "<answer>"` — the only path to RESOLVED |
| a deferred decision | `defer --id D1 --by <who> --reason "<why>"` |
| a Scope Audit Lab integrity report bearing on a claim | `labref --id L1 --lab-report <integrity-report.json> --claim C1` — links and hash-binds the report; never changes the claim's support grade |
| INCOMPLETENESS list | generated automatically by `report`; do not hand-write it |

Then `check` (must print VALID) and `report` (markdown; incompleteness printed first). The report is the deliverable: a record, not a verdict.
