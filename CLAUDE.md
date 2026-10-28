# CLAUDE.md

study-aperture is a toolbox for AI-assisted assessment of publications. It **routes, records, and keeps incompleteness visible**. It does not judge scientific validity and does not produce a quality score. Every change here must preserve that.

## System shape

```
                         ┌───────────────────────────┐
  publication ──► cards/ (00 route → 01..06) ──► AI_ENTRY_PROMPT.md (LLM path, no Python)
                         └────────────┬──────────────┘
                                      ▼
                     assess.py  (record ⇄ JSON, schema study-aperture/1)
                     init/claim/design/average/tool/decide/resolve/defer ──► check ──► report
                                      ▲
            vendored/  provenance_graph · false_agree · conditional_claims · safe_provenance
                       (Card 03 independence / conditional-form tools)

  experimental/scope_audit_lab/   ← independent subproject, separate schema + tests
      integrity_checker.py  (offline bundle checker, exit 0/1/2)
      schemas/draft-0.1, draft-0.2 · docs/ · reviews/<run>/ · tests/
      exchange with parent = explicit JSON only, never shared mutable state

  experimental/in_situ_learning/  ← gap analysis + stdlib toy of an in situ learning loop
      (GAPS.md, THEORY.md all PROPOSED, loop.py pinned by test_loop.py); no link to assess.py
```

| Path | Role | Edit rules |
|---|---|---|
| `assess.py` | validator + report generator | stdlib only, no network; keep the docstring schema in sync with code |
| `cards/00..06_*.md` | method cards (provenance, procedure, outputs, limits) | each card keeps its **Provenance** line; routing table in 00 is a default, not a gate |
| `AI_ENTRY_PROMPT.md` | LLM prompt + CLI handoff table | update the handoff table when CLI flags change |
| `TEMPLATE.json` | skeleton record | keep valid against `assess.py check` |
| `vendored/*.py` (3 upstream) | verbatim from Simulators `0655e8b` | **do not modify**; upstream oddities are data, not defects. Changes go in `safe_provenance.py` (toolbox adapter) or upstream |
| `vendored/PROVENANCE.md`, `vendored/SHA256SUMS` | repo / path / commit / hash for each vendored file | update both on any re-vendor |
| `tests/test_repo_integrity.py`, `run_checks.sh`, `.github/workflows/checks.yml` | repo-level enforcement + CI | stdlib only; add new suites to `run_checks.sh` |
| `examples/*/` | worked example + failure-mode examples | regenerate `report.md` from `assessment.json`; never hand-edit reports |
| `experimental/scope_audit_lab/` | experimental lab | see Lab section |
| `experimental/in_situ_learning/` | gap analysis of Jensen et al. (in situ DNP learning), stdlib toy loop, proposed AI learning program | toy is CONSTRUCTED: never describe its numbers as findings about instruments or AI; regenerate `samples/run.txt` and README results together |
| `ADDENDUM.md` | open work list with states (OPEN / OWNER / UNDETERMINED) | update an item's state when work lands; never resolve an OWNER item without the owner; don't name the unnamed state in A1 |

## Commands (run from repo root; Python 3, stdlib only)

```sh
./run_checks.sh                      # EVERYTHING; must print ALL CHECKS PASSED before committing
                                     # (same script runs in CI: .github/workflows/checks.yml, Python 3.11–3.14)

# individual pieces
python3 assess.py selftest
python3 -m unittest discover -s tests                              # repo integrity (below)
python3 -m unittest discover -s experimental/scope_audit_lab/tests
python3 assess.py report --file examples/<name>/assessment.json > examples/<name>/report.md   # regenerate a report
```

`tests/test_repo_integrity.py` enforces three rules from this file:

```
vendored/*.py        == vendored/SHA256SUMS      re-vendor → update SHA256SUMS + PROVENANCE.md together
examples/*/report.md == assess.py report output  edit assessment.json, then regenerate; never edit report.md
vocabulary in README / CLAUDE.md / AI_ENTRY_PROMPT == sets in assess.py
```

The lab checker exits 1 on `examples/schema-draft-0.2/records.json` on purpose (the bundle is incomplete); `run_checks.sh` treats 1 as the pass condition there. No dependencies may be added (no pip, no NumPy) to the core toolkit or the lab runtime.

## Invariants (enforced in code; do not weaken)

```
missing value        → stays a value: UNDECLARED · NODATA · NOTFOUND · NO_EVIDENCE_LOCATION
                       never → zero, negative finding, or completion
RESOLVED             → only via `resolve --answer --by` (both non-sentinel); `decide --state RESOLVED` rejected
invalid mutation     → nonzero exit, file unchanged
DECLINED tool        → requires reason
valid ≠ complete     → a record can be VALID and INCOMPLETE; incompleteness is printed FIRST in reports
confidence in claims ≠ whether claims justify action
NOT_APPLICABLE       → a legal output, not a failure
lab evidence         → enters only via `labref`: hash-bound to one report, linked to claims,
                       never changes support or decisions. Changed report = violation;
                       missing report = incompleteness; INTEGRITY_GAPS_RECORDED = incompleteness
input average        → declares population, window, stationarity (UNDECLARED allowed, kept);
                       none stated = FROZEN (derived, never set by hand): a claim resting on it
                       cannot carry a MEASURED_* grade; ASSESSED needs a basis + stated
                       population and window; frozen/partial/split/fitted/transferred = incompleteness
no shared ancestor in declared graph ≠ independent in the world
```

Vocabulary (closed sets, defined in `assess.py`; `UNDECLARED` is also accepted in grades, labels, and design checks as the missing-value sentinel):

| Set | Values |
|---|---|
| publication types | EMPIRICAL · REVIEW · THEORETICAL · SIMULATION · COMMENTARY · UNDECLARED |
| claim support | SUPPORTED · PARTIALLY_SUPPORTED · UNSUPPORTED · CONTRADICTED · UNTESTED · UNDETERMINED |
| measurement grades | MEASURED_PRESENT · MEASURED_ABSENT · MEASURED_DISCARDED · UNMEASURED · UNDERPOWERED · IMPOSED |
| epistemic labels | OBSERVED · DERIVED · PROPOSED |
| tool states | RUN · DECLINED · BLOCKED · NOT_APPLICABLE |
| decision states | DETECTED · UNRESOLVED · RESOLVED · DEFERRED · NOT_APPLICABLE |
| design check states | CHECKED · NOT_CHECKED · NOT_APPLICABLE |
| stationarity states | ASSESSED · ASSUMED · UNASSESSED |
| lab report statuses | NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE · INTEGRITY_GAPS_RECORDED |

This table, the README vocabulary list, and `AI_ENTRY_PROMPT.md` are checked against `assess.py` by the integrity tests. Adding or renaming a value touches: `assess.py` sets + `check()` + selftest, the cards that emit it, `AI_ENTRY_PROMPT.md`, README vocabulary, this table, and `TEMPLATE.json`.

## Scope Audit Lab (`experimental/scope_audit_lab/`)

- Independent subproject. It does **not** replace or extend `assess.py`; parent ↔ lab exchange is explicit JSON.
- An imported test pass must never promote a claim to SUPPORTED, turn an interpretation into an observation, or establish empirical validity.
- The one implemented import path is `assess.py labref` (see `examples/lab-link/`). It reads the checker's JSON report locally and copies its own status words; lab statuses are a separate vocabulary from claim support. Don't paste lab results into `tool --output` free text instead.
- `integrity_checker.py` reads only explicitly supplied local JSON: no URL fetching, no directory scanning, no "latest version" selection, never overwrites an existing output path (exit 2).
- Draft schemas are **proposals**, not stable interfaces. Status lines in each README/doc state what is and is not established — keep them accurate when behavior changes.
- Review runs under `reviews/<run>/` are records. Preserve earlier runs and `attempt-NN-*` directories unchanged; corrections go in a new run or `correction-record.json`, not by editing history. Generated `artifacts/` come from the run scripts (they refuse to overwrite); regenerate into a new directory rather than editing outputs.
- Active focus: mathematics and physics evidence. Voice work is DEFERRED; do not add voice instrumentation unless the owner resumes it.

## Writing conventions

- Status-first docs: every README/doc opens with a `Status:` line saying what is implemented, what is draft, and what is **not established**. Do not overstate — "passes its tests within tested scope," never "validated" or "correct."
- Every substantive finding carries a source location (URL, page, table, derivation step).
- Methods referenced but not run (`presignal_ledger`, `rank_detector`, `grounding-layers`, `frame_probe`, `observer_position_control`) stay marked optional / NOT_APPLICABLE, not verified.
- Keep the README "Verification state" section truthful after changes.
- License is CC0-1.0; vendored files retain upstream CC0 provenance.
