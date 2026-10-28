# study-aperture

A ready-to-use toolbox for AI-assisted assessment of any study or publication — reasoning tools, a record format, and a report generator that keeps incompleteness visible.

Built from five CC0 repositories by JinnZ2, distilled into one portable layer:

- [Simulators](https://github.com/JinnZ2/Simulators) (`0655e8b`) — grounding layers, agreement-independence tools, conditional claims, term-drift
- [method-layer](https://github.com/JinnZ2/method-layer) (`365669b`) — branch sets, preference-free ranking, the register map
- [drift-archive-audit](https://github.com/JinnZ2/drift-archive-audit) (`3d403a1`) — target/rendering split, the DECLINED register
- [decision-aperture](https://github.com/JinnZ2/decision-aperture) (`5f8d316`) — assessment frames, the decision ledger
- [chain-position-detectability](https://github.com/JinnZ2/chain-position-detectability) (`86cfb2b`) — OBSERVED/DERIVED/PROPOSED labeling, assumed stabilities

## What this is

- A set of **method cards** (reasoning tools), each with provenance, procedure, outputs, and limits
- A **record format + validator + report generator** (`assess.py`, Python 3 stdlib only, no dependencies, no network)
- Three **vendored upstream tools** with their selftests intact
- A **worked example** on a real contested literature, plus failure-mode examples
- An **AI entry prompt** so the toolbox works with any LLM, no Python needed

## What this is not

- Not a judge of scientific validity. It routes, records, and keeps incompleteness visible.
- Not a universal quality score. Confidence in claims stays separate from whether claims justify action.
- Not a replacement for ordinary study-design checks — confounding, selection, measurement validity, uncertainty, multiplicity, missing data, preregistration. Cards run **on top of** those, not instead of them.

## Quick start

```sh
python3 assess.py init --file s.json --title "Carney et al. 2010" --type EMPIRICAL
python3 assess.py design --file s.json --check preregistration --state CHECKED --finding "none" --source "<url>"
python3 assess.py claim --file s.json --id C1 --text "..." --evidence "p. 1365, Fig. 1" --support UNDETERMINED \
    --label OBSERVED --grade MEASURED_PRESENT --falsifiers "null at adequate power" --source "<url>"
python3 assess.py tool --file s.json --id T1 --card 03 --state RUN --output "SHARED_UPSTREAM" --source "<url>"
python3 assess.py decide --file s.json --id D1 --text "Rely on this for training decisions?" --state UNRESOLVED
python3 assess.py check --file s.json     # exit 1 on violations
python3 assess.py report --file s.json    # markdown; incompleteness printed first
python3 assess.py selftest
```

## The workflow

1. **Route** (Card 00): publication type, materials in hand, decision context. Cards that don't apply return `NOT_APPLICABLE` — a legal output.
2. **Extract claims** (Card 01): verbatim text + evidence location + conditional form + falsifiers. A claim without an evidence location is not yet a claim.
3. **Declare premises** (Card 02): each claim as a layer with measurand, range, instrument, grade, resolution. Watch for `MEASURED_DISCARDED` without a discard rule.
4. **Check the evidence base** (Card 03): is agreement independent convergence, one source echoed, or definitional false agreement?
5. **Keep alternatives alive** (Card 04): candidate explanations, cheapest discriminator first; each elimination is a result.
6. **Position and scope** (Card 05): optional; observer position, term frames, grounding layers, assumed stabilities.
7. **Record and decide** (Card 06): OBSERVED/DERIVED/PROPOSED labels, target vs. rendering, decision ledger with no silent resolution.

## File map

| Path | Contents |
|---|---|
| `cards/00_ROUTING.md` … `cards/06_RECORDS.md` | the seven method cards |
| `assess.py` | record validator + report generator (stdlib) |
| `TEMPLATE.json` | skeleton record showing where measurement declarations, design checks, falsifiers, epistemic labels, and per-finding sources live |
| `vendored/` | `provenance_graph.py`, `false_agree.py`, `conditional_claims.py` (upstream), `safe_provenance.py` (scoped adapter) — selftests intact + `PROVENANCE.md` |
| `AI_ENTRY_PROMPT.md` | copy-paste prompt for using the cards with any LLM |
| `examples/power-pose/` | worked example: real contested literature — record, machine report, `FINDINGS.md` narrative with inline source citations, `false_agree.json`, two provenance graphs |
| `examples/incomplete-input/` | failure mode: incomplete material stays visibly incomplete |
| `examples/nonempirical-note/` | routing check: commentary returns `NOT_APPLICABLE` for quantitative cards |

## Vocabulary (the short version)

- **Publication types:** EMPIRICAL, REVIEW, THEORETICAL, SIMULATION, COMMENTARY, UNDECLARED
- **Claim support:** SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNTESTED, UNDETERMINED
- **Measurement grades:** MEASURED_PRESENT / ABSENT / DISCARDED, UNMEASURED, UNDERPOWERED, IMPOSED
- **Tool states:** RUN, DECLINED, BLOCKED, NOT_APPLICABLE
- **Decision states:** DETECTED, UNRESOLVED, RESOLVED, DEFERRED, NOT_APPLICABLE

`UNDECLARED`, `NODATA`, `NOTFOUND` are values, not errors. A zero is a property of the measurement, not of the world.

## Verification state

- `assess.py` and all four vendored tools pass their selftests; the README quick-start commands and all three example records were re-run from a fresh extracted copy before shipping.
- Upstream repositories' own reading guidance (`READ_ME_THIS_WAY.md` where present) was read before adapting methods; per that guidance, mismatches and odd names upstream are data, not defects, and are not "fixed" here.
- The upstream `method-layer` test suite runs 208 tests with 3 failures, all in an unrelated fitness-bin module (Python 3.14 environment); the modules this toolbox draws on (register map, branch set, ranking) pass.
- Methods referenced but **not run** by this toolbox: `presignal_ledger` (prognostic-claims tool, upstream only), `rank_detector`, `grounding-layers` (needs NumPy), `frame_probe`, `observer_position_control`. Their cards describe documented upstream procedures; they are marked optional or NOT_APPLICABLE rather than presented as verified.

## License

CC0-1.0. The vendored files are CC0 from their upstream repositories; see `vendored/PROVENANCE.md` for exact provenance (repo, path, commit).
