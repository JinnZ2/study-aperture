# CLAUDE.md

study-aperture is a toolbox for AI-assisted assessment of publications. It **routes, records, and keeps incompleteness visible**. It does not judge scientific validity and does not produce a quality score. Every change here must preserve that.

## System shape

```
                         ┌───────────────────────────┐
  publication ──► cards/ (00 route → 01..06) ──► AI_ENTRY_PROMPT.md (LLM path, no Python)
                         └────────────┬──────────────┘
                                      ▼
                     assess.py  (record ⇄ JSON, schema study-aperture/1)
                     init/claim/design/tool/decide/resolve/defer ──► check ──► report
                                      ▲
            vendored/  provenance_graph · false_agree · conditional_claims · safe_provenance
                       (Card 03 independence / conditional-form tools)

  experimental/scope_audit_lab/   ← independent subproject, separate schema + tests
      integrity_checker.py  (offline bundle checker, exit 0/1/2)
      schemas/draft-0.1, draft-0.2 · docs/ · reviews/<run>/ · tests/
      exchange with parent = explicit JSON only, never shared mutable state
```

| Path | Role | Edit rules |
|---|---|---|
| `assess.py` | validator + report generator | stdlib only, no network; keep the docstring schema in sync with code |
| `cards/00..06_*.md` | method cards (provenance, procedure, outputs, limits) | each card keeps its **Provenance** line; routing table in 00 is a default, not a gate |
| `AI_ENTRY_PROMPT.md` | LLM prompt + CLI handoff table | update the handoff table when CLI flags change |
| `TEMPLATE.json` | skeleton record | keep valid against `assess.py check` |
| `vendored/*.py` (3 upstream) | verbatim from Simulators `0655e8b` | **do not modify**; upstream oddities are data, not defects. Changes go in `safe_provenance.py` (toolbox adapter) or upstream |
| `vendored/PROVENANCE.md` | repo / path / commit for each vendored file | update on any re-vendor |
| `examples/*/` | worked example + failure-mode examples | regenerate `report.md` from `assessment.json`; never hand-edit reports |
| `experimental/scope_audit_lab/` | experimental lab | see Lab section |

## Commands (run from repo root; Python 3, stdlib only)

```sh
# core toolkit
python3 assess.py selftest
(cd vendored && for f in provenance_graph false_agree conditional_claims safe_provenance; do python3 $f.py selftest; done)

# example records must stay VALID and reproduce their reports
python3 assess.py check  --file examples/power-pose/assessment.json
python3 assess.py report --file examples/power-pose/assessment.json

# lab
python3 -m unittest discover -s experimental/scope_audit_lab/tests
python3 experimental/scope_audit_lab/integrity_checker.py \
  experimental/scope_audit_lab/examples/schema-draft-0.2/records.json   # exit 1 is EXPECTED (incomplete bundle)
(cd experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27     && python3 -m unittest test_case.py)
(cd experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1 && python3 -m unittest test_trace.py)
```

Run all of the above before committing changes to code, schemas, or examples. No dependencies may be added (no pip, no NumPy) to the core toolkit or the lab runtime.

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
no shared ancestor in declared graph ≠ independent in the world
```

Vocabulary (closed sets, defined in `assess.py`):

| Set | Values |
|---|---|
| publication type | EMPIRICAL · REVIEW · THEORETICAL · SIMULATION · COMMENTARY · UNDECLARED |
| claim support | SUPPORTED · PARTIALLY_SUPPORTED · UNSUPPORTED · CONTRADICTED · UNTESTED · UNDETERMINED |
| measurement grade | MEASURED_PRESENT / _ABSENT / _DISCARDED · UNMEASURED · UNDERPOWERED · IMPOSED |
| epistemic label | OBSERVED · DERIVED · PROPOSED |
| tool state | RUN · DECLINED · BLOCKED · NOT_APPLICABLE |
| decision state | DETECTED · UNRESOLVED · RESOLVED · DEFERRED · NOT_APPLICABLE |

Adding or renaming a value touches: `assess.py` sets + `check()` + selftest, the cards that emit it, `AI_ENTRY_PROMPT.md`, README vocabulary, and `TEMPLATE.json`.

## Scope Audit Lab (`experimental/scope_audit_lab/`)

- Independent subproject. It does **not** replace or extend `assess.py`; parent ↔ lab exchange is explicit JSON.
- An imported test pass must never promote a claim to SUPPORTED, turn an interpretation into an observation, or establish empirical validity.
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
