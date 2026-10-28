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
python3 assess.py average --file s.json --id A1 --text "effect prevalence" --value 0.25 \
    --population UNDECLARED --window UNDECLARED --stationarity UNDECLARED --claim C1   # an input average; all three unstated = FROZEN
python3 assess.py labref --file s.json --id L1 --lab-report integrity-report.json --claim C1   # optional: lab evidence
python3 assess.py selftest
```

## The workflow

1. **Route** (Card 00): publication type, materials in hand, decision context. Cards that don't apply return `NOT_APPLICABLE` — a legal output.
2. **Extract claims** (Card 01): verbatim text + evidence location + conditional form + falsifiers. A claim without an evidence location is not yet a claim.
3. **Declare premises** (Card 02): each claim as a layer with measurand, range, instrument, grade, resolution. Watch for `MEASURED_DISCARDED` without a discard rule. Any average used as an input declares population, window and stationarity; with none stated it is FROZEN, and a claim resting on it cannot be graded as measured.
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
| `examples/reproducibility-model/` | run on a 2026 preprint arguing the OSC 2015 replication rate is a power artifact: record, report, `FINDINGS.md`, and `recompute.py` (stdlib recomputation of the paper's arithmetic, pinned) |
| `examples/lab-link/` | synthetic: a Scope Audit Lab integrity report linked to a claim with `labref`; support unchanged, gaps listed as incompleteness |

## Vocabulary (the short version)

- **Publication types:** EMPIRICAL, REVIEW, THEORETICAL, SIMULATION, COMMENTARY, UNDECLARED
- **Claim support:** SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNTESTED, UNDETERMINED
- **Measurement grades:** MEASURED_PRESENT, MEASURED_ABSENT, MEASURED_DISCARDED, UNMEASURED, UNDERPOWERED, IMPOSED
- **Epistemic labels:** OBSERVED, DERIVED, PROPOSED
- **Tool states:** RUN, DECLINED, BLOCKED, NOT_APPLICABLE
- **Decision states:** DETECTED, UNRESOLVED, RESOLVED, DEFERRED, NOT_APPLICABLE
- **Design check states:** CHECKED, NOT_CHECKED, NOT_APPLICABLE
- **Stationarity states:** ASSESSED, ASSUMED, UNASSESSED (for an average used as a model input; see Card 02)
- **Lab report statuses:** NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE, INTEGRITY_GAPS_RECORDED (the lab checker's own words; not claim support)

`UNDECLARED`, `NODATA`, `NOTFOUND` are values, not errors. A zero is a property of the measurement, not of the world.

## Verification state

- `assess.py` and all four vendored tools pass their selftests; the README quick-start commands and all three example records were re-run from a fresh extracted copy before shipping.
- `./run_checks.sh` runs every selftest and test suite in one pass; GitHub Actions runs it on each push and pull request. `tests/test_repo_integrity.py` checks that vendored files still match their recorded upstream hashes (`vendored/SHA256SUMS`), that example reports regenerate byte-identically from their records, and that the vocabulary above matches `assess.py`.
- Upstream repositories' own reading guidance (`READ_ME_THIS_WAY.md` where present) was read before adapting methods; per that guidance, mismatches and odd names upstream are data, not defects, and are not "fixed" here.
- The upstream `method-layer` test suite runs 208 tests with 3 failures, all in an unrelated fitness-bin module (Python 3.14 environment); the modules this toolbox draws on (register map, branch set, ranking) pass.
- Methods referenced but **not run** by this toolbox: `presignal_ledger` (prognostic-claims tool, upstream only), `rank_detector`, `grounding-layers` (needs NumPy), `frame_probe`, `observer_position_control`. Their cards describe documented upstream procedures; they are marked optional or NOT_APPLICABLE rather than presented as verified.

## Experimental proposals

[Scope Audit Lab](experimental/scope_audit_lab/README.md) contains draft evidence schemas, scoped physics reference anchors, and a narrow standard-library-only [offline integrity checker](experimental/scope_audit_lab/docs/offline-integrity-checker.md) for local references, exact version bindings, anchor-condition coverage, and explicit assessment-subject links. Scoped synthetic tests and inspectable reports are included; semantic criterion-to-verdict justification, mathematical/empirical validation, full requirements conformance, prototype compatibility, and live voice instrumentation are not established.

The lab also includes [draft criterion-to-conclusion mappings](experimental/scope_audit_lab/docs/criterion-conclusion-mappings.md) and a [worked study published October 27, 2026](experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27/README.md). This bounded run keeps exact algebra, sampled numerical comparisons, a candidate internal discrepancy, and unresolved physical/empirical questions separate; it does not validate an entire publication.

A separate [phase-to-probability follow-up](experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1/README.md) traces whole-phase versus partial-phase sign changes, retained quartic terms, mixing-angle-dependent phase averaging, and the need for an explicit response kernel. It preserves the earlier study run unchanged and does not select a corrected physical prediction.

## In situ learning (experimental)

[In situ learning](experimental/in_situ_learning/README.md) — gap analysis of an in situ machine-learning DNP study (Jensen et al., arXiv:2603.19448), a stdlib toy of the learning loop (in situ vs in silico, transfer between instruments, best-observed overstatement, single-run comparisons, mean vs worst case), and a proposed learning program for AI. The toy is constructed; the program has not been run.

## Work to be done

[ADDENDUM.md](ADDENDUM.md) lists open work, each item with a state: the translation layer (oral reasoning → English → code), remaining toolkit gaps, independence and testing, and repository housekeeping.

## License

CC0-1.0. The vendored files are CC0 from their upstream repositories; see `vendored/PROVENANCE.md` for exact provenance (repo, path, commit).
