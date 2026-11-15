# Card 07 — Read ceiling: read depth per source

**Provenance:** JinnZ2/Simulators `mining-increment/SOURCE_DROP_V2.md`, paragraph "READ CEILING", and the audit claim `MI_010` in `mining-increment/CLAIM_TABLE.md` (CC0, co-authored; read at Simulators `main` `38a77bc`). Status: documented procedure adapted from one upstream instance. The depth vocabulary below is this card's, not upstream's: upstream states one depth (abstracts and citation metadata) in prose. Enforced by `assess.py` (schema `study-aperture/2`, 2026-11-15): every source carries a depth, and every graded claim names the sources and depths it rests on (section 5). The ceiling rule itself (section 4) is not checked by code. Co-authored.

## 1. What the card is for

Card 00 asks for the material held, once per record. A record usually rests on several sources read to different depths, and one record-level line hides which claim rests on which depth.

Upstream's case: a source was entered from its abstract, the row is right at that depth, and the content the assessment actually needs (a model's boundary condition) is not visible at that depth. That is its own state:

```text
not CARRIED-and-unverified   the source was read, at a stated depth
not absent                   the source exists and is cited
below ceiling                the load-bearing content sits deeper than the read
```

Upstream: "This is a capability limit on the audit, not an open question about the work."

## 2. Read depth, per source

Declare one depth for every source a claim, tool output or design check rests on.

| Depth | Meaning |
|---|---|
| `SNIPPET` | a search-result fragment or index entry; not the document |
| `PRESS_RELEASE` | coverage or a release about the work, not the work |
| `ABSTRACT` | the abstract and citation metadata only |
| `FULL_TEXT` | the document itself, read; name the sections if only some were |
| `CARRIED` | not read: taken from another document's report of it, or from memory |
| `UNDECLARED` | depth not stated; kept, never read as `FULL_TEXT` |

Rules:
- Depth is per source, not per record. Two sources in one claim can have two depths.
- `CARRIED` names what it was carried from.
- A preprint, a corrected version and a published version are different sources, not different depths.
- `FULL_TEXT` of some sections (methods only, figures only) is written as `FULL_TEXT` plus the sections read. Anything outside them is at the next depth down that was actually read.

## 3. The ceiling declaration

When a claim needs content a source's depth cannot show, write the three parts upstream's paragraph has (counted in `MI_010`):

1. **Depth read at.** For example `ABSTRACT`.
2. **What is not visible at that depth**, named: the exact quantity, method detail or formulation the claim needs.
3. **The retrieval step**, routed into the method as a next step, not as a caveat.

## 4. What the ceiling forbids

- No support grade may rest on content above a source's read depth. If the claim needs it, the claim's support stays `UNTESTED` or `UNDETERMINED` until the retrieval step runs.
- Nothing may be filled in to stand where the unread content would be: no reconstructed formulation, figure or number.
- Compliance can be checked in both directions (upstream's falsifier): the record should contain nothing that only a deeper read could have supplied. Upstream checks this mechanically on its scaffold. Here, the part a depth label can decide is checked by the table in section 4a; the rest is a reviewer check.

### 4a. The ceiling table (mechanical part, enforced)

The highest grade each depth can carry. `FULL_TEXT` has no row: what a full read can carry depends on the sections read, which the table cannot see.

| Depth | Support not allowed | Measurement grade not allowed |
|---|---|---|
| `SNIPPET` | anything above `UNTESTED`: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED` | any `MEASURED_*` |
| `PRESS_RELEASE` | anything above `UNTESTED` | any `MEASURED_*` |
| `ABSTRACT` | (none) | any `MEASURED_*`, unless the value is quoted word for word from the abstract text stored on the source |
| `CARRIED` | anything above `UNTESTED`: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED` | any `MEASURED_*` |
| `UNDECLARED` | no row: flagged separately (section 5) | no row |

Rules:
- **Any one source can carry the grade.** A claim exceeds the ceiling only when no source it rests on permits its grade. A claim on a press release and on the full text can be SUPPORTED.
- **Exceeding the ceiling is a FLAG, not a violation.** The record stays valid and is not clean.
- **A quoted value lifts an ABSTRACT ceiling, and is checked.**
  - Store the abstract on the source: `source --depth ABSTRACT --abstract-text "..."` or `--abstract-file path`.
  - Quote from it on the claim: `claim ... --quoted S1="<the value as the abstract gives it>"`.
  - The quote must appear in the stored text word for word. Only whitespace is normalised, and a fragment of a word does not match.
  - These are violations: a quote not in the text, a quote on a source with no stored abstract, a quote on any depth other than ABSTRACT, and abstract text stored on a non-ABSTRACT source.
- **A reviewer can override a ceiling only with a logged reason and a named author**: `override --id C1 --by <who> --reason "..."`.
  - An override is refused when nothing exceeds the ceiling.
  - An override missing its reason or author is a violation.
  - Overrides are printed in `check` and in their own report section.
  - An override left over after the claim no longer exceeds the ceiling is FLAGGED as stale.

### 4b. Section-level ceiling (enforced)

A FULL_TEXT read of some sections is not a full read of the others.

- On a FULL_TEXT source, `--sections "abstract,intro,methods"` lists the sections read in full, and `--section-depth results=ABSTRACT` gives the depth a section was read at by another route.
- A claim names the section it rests on: `--rests-on S1:results` (stored as `{source, depth, section}`).
- The ceiling for that rest uses the section's depth: FULL_TEXT when the section is in `sections`; the `section_depths` value when one is given; otherwise **UNDECLARED**, which flags any grade resting on it.
- A rest naming no section takes the source's depth, as before (records written before sections existed).
- Section names compare case-insensitively, whitespace normalised. A section both in `sections` and in `section_depths`, a `section_depths` value of FULL_TEXT or outside READ_DEPTHS, and a section on a source that is not FULL_TEXT are violations.

## 5. How `assess.py` enforces it

```text
source --id S1 --location <url> --depth ABSTRACT [--detail ...] [--basis ...]
   depth missing                        -> violation (UNDECLARED is legal; omitted is not)
   FULL_TEXT / CARRIED without --detail -> violation (name the sections / the origin)
any `--source <url>` elsewhere          -> must be a listed source, else violation
claim graded (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, or MEASURED_*)
   no rests_on                          -> violation
   rests_on depth != the source's depth -> violation
   rests on an UNDECLARED depth         -> FLAGGED: valid, not clean
   above the ceiling of every source    -> FLAGGED (table 4a), unless overridden with a logged reason
                                           `check` prints "VALID — FLAGGED"; `check --strict` exits 3
study-aperture/1 record                 -> read through an in-memory migration (all depths
                                           UNDECLARED); never rewritten until `migrate` runs
```

- `--source` on `claim` adds that source to `rests_on`; `--rests-on S2` adds others.
- `migrate --depths decl.json` takes a depth only from a declaration whose `basis` quote appears verbatim in the record's own text, and writes every change into the record's `migrations` log.
- A ceiling declaration (section 3) goes in `notes`, or in the tool output that hit it.

The repository's own examples were migrated this way. Depths came from their `materials` text; where a record states no depth for a source, the source stays UNDECLARED.

Applied to the examples (decided 2026-11-15, by evidence, no override):
- `arase-may2024` C1 (SUPPORTED, MEASURED_PRESENT on a press release) and `aaiw-reversal-2026` C1 (PARTIALLY_SUPPORTED, MEASURED_PRESENT on press coverage) were downgraded to the ceiling: UNTESTED, grade UNDECLARED.
  - Each was lowered with `downgrade --reason "graded above read depth" --by user`.
  - The old grades stay in each claim's `downgrades` log.
- C4 in both examples (PARTIALLY_SUPPORTED on press material) was downgraded to UNTESTED the same way, on the same date.
  - Neither example is flagged now.
  - `arase-may2024` tool run T3 still reads "C1 graded MEASURED_PRESENT", because a run's output is never edited. It now carries a dated note pointing to the claim log (`annotate`).

## 6. Limits

- One upstream instance. The vocabulary in section 2 is a proposal, not upstream's and not tested across records.
- A record can declare every depth UNDECLARED and still check VALID. Only graded claims on those sources are FLAGGED.
- What `assess.py` checks is that a depth is declared and restated consistently, and that a grade is within the table in 4a. It does not check that the content a grade relies on is visible at the depth, for example which sections a FULL_TEXT read covered. That stays a reviewer check.
- The table is coarse by design. On a snippet or a press release, nothing above UNTESTED is allowed, partial support included. A reviewer who reads a case differently records an override.
- A declared depth is recorded provenance, not verified provenance (same rule as every `source` field).
- The card says nothing about whether a source is right, only about how deeply it was read.
