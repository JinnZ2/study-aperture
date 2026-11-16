# Reading notes: common misreads and a short glossary

Status: a list of misreads of this repository, recorded so the next reader can avoid them, plus a glossary of terms that are not in the vocabulary table. Each entry says what the repository records and where to check it. First entries come from one AI deep-research audit of this repository and formula-audit, dated 2026-11-17, which the owner pasted into a session on 2026-11-16 and which was checked against the repositories at `4af5786` (this one) and `19ff7df` (formula-audit); the audit text itself is not in this repository. Not established: that this list is complete, or that every reader makes these misreads. The closed vocabulary is defined in `assess.py` and listed in [CLAUDE.md](CLAUDE.md); this file does not define or extend it, and does not name the unnamed state in ADDENDUM A1.

## Misreads already made

| Misread | What the repository records | Check |
|---|---|---|
| C1 is about Simulators: "no independent run of the Simulators suite" | C1 is about the whole toolkit: all five upstream repositories share one author, so the toolkit's own methods are `SHARED_UPSTREAM`. The route it names is someone else running `AI_ENTRY_PROMPT.md` on a paper they chose. | [ADDENDUM.md](ADDENDUM.md) C1 (title reworded 2026-11-16 to put this first) |
| The C2 run-count numbers are settled | The 67 HOLDS / DIRECTION-HOLDS verdicts were not re-verified (C2b); verification overturned 13 of 25 first-pass failures, all toward false failure. The audit covers 43 candidate folders, not the 173 outside them. | ADDENDUM C2, C2b; [audits/simulators-run-count](audits/simulators-run-count/README.md) Status line |
| Four upstream repositories are vendored and SHA-256 pinned | Three files from one repository (Simulators `0655e8b`) are vendored and hashed. `safe_provenance.py` is a toolbox-written adapter. The other four upstream repositories are pinned by commit in the README only. | [vendored/PROVENANCE.md](vendored/PROVENANCE.md), `vendored/SHA256SUMS` |
| Stdlib-only holds for every file | It holds for the core toolkit and the lab runtime. One authoring script, `experimental/scope_audit_lab/reviews/draft-0.2/review_schema.py`, declares and imports `jsonschema` and `referencing`; it is not run by `run_checks.sh`. | that file's header; CLAUDE.md "Commands" |
| The arXiv 2611.05459 LLM-review benchmark is a worked example | It is an audit (`audits/`), quotes and checks only, with no `assess.py` record. | [its README](audits/arxiv-2611.05459-llm-review-benchmark-2026-11-14/README.md) Status line |
| `assess.py` is a small script | It is about 2,100 lines (2,095 at `4af5786`). | `wc -l assess.py` |
| A passing `run_checks.sh` means the assessments are correct | It means the records, reports, vocabulary and vendored hashes are internally consistent, within tested scope. It says nothing about whether any assessed paper is right. | CLAUDE.md "Writing conventions" |
| A VALID record is a complete one | A record can be VALID and INCOMPLETE; the report prints incompleteness first. | CLAUDE.md "Invariants" |

## Glossary (terms outside the vocabulary table)

| Term | Meaning here | Defined in |
|---|---|---|
| `SHARED_UPSTREAM` | Two agreeing items trace to the same source, so their agreement is one source echoed, not independent confirmation (and not evidence against). | [Card 03](cards/03_INDEPENDENCE.md) |
| `FROZEN` | An input average with none of population, window or stationarity stated. Derived, never set by hand; a claim resting on it cannot carry a `MEASURED_*` grade. | [Card 02](cards/02_PREMISES.md) |
| `IMPOSED` | A measurement grade: asserted without measurement, with a reason. Not a defect label; it says how the number entered. | Card 02 |
| `CARRIED` | A read depth: the source was not read; the claim was taken from another report of it, named in the detail. | [Card 07](cards/07_READ_CEILING.md) |
| read ceiling | The highest grade a claim may carry given the depth at which its sources were read. Above it = `FLAGGED`. | Card 07 §4a |
| `FLAGGED` | Valid but not clean; `check --strict` exits 3. Overridden only with a logged reason and name. | CLAUDE.md "Invariants" |
| `UNDECLARED` / `UNDETERMINED` | `UNDECLARED`: no one recorded a value. `UNDETERMINED`: the evidence in hand cannot decide. Both are values, never zeros. | ADDENDUM A1 |
| `NO_FIT` | A logged case where no value in a closed set describes what was observed. Kept as text in `no_fit_log.json`; no enum changes. | ADDENDUM A3; [no_fit_log.json](no_fit_log.json) |
| central | A claim marked `--central` (the paper's headline claim, in the assessor's reading); incompleteness touching it is flagged in reports. | ADDENDUM B5 |
