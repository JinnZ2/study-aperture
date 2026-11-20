# ROTL-EXP-002 — Reversible Translation Stratum (behavioral)

Status: PROPOSED experimental specification, 2026-11-11 (America/Chicago). Nothing here has been run. This is a bounded behavioral experiment; it requires no model internals, no network, and no compute beyond ordinary assessment sessions. It supplements the study-aperture framework; it changes no core card, validator rule, or addendum item.

**Correction record (2026-11-11, per Kavik revision):** the first draft of this spec filled the specimen frame labels itself. Those labels were authored by the spec author, not declared by the source holder — the exact failure this stratum exists to measure, committed by its own instrument. All four frame entries are now `PENDING_SOURCE_CONFIRMATION`. Kavik will confirm or replace the labels; until then, no frame label on any specimen carries source-holder authority. The correction is recorded here rather than silently rewritten, per the repo's preservation rule.

## INPUT BRIEF

Received 2026-11-11/12 from Kavik (repo owner), in direct instruction, revised 2026-11-11:

- Write two experiment specs in study-aperture idiom; this is the first, covering reversible translation, behavioral channels only.
- Relational source statements are Kavik's verbatim words; she will confirm or replace the S1–S4 candidates sent separately. The S4 wording is confirmed as Kavik's own, not a translation.
- The round trip is relational → technical → relational, diffed against source under a DECLARED similarity procedure. No embedding model is required for v1; human/Kavik adjudication is an allowed channel and must be recorded as a channel.
- Interface detection (was the mode recognized?) is recorded separately from translation fidelity.
- Pre-declare what counts as loss, what the test cannot establish, and stopping rules.
- Source-frame labels (RELATIONAL / NARRATIVE / CATEGORICAL / …) are authored or confirmed by the source holder (Kavik). UNKNOWN and the owner-held unnamed state (ADDENDUM A1) remain available at every point.
- Revision details: dates set to 2026-11-11 (America/Chicago); receiver outputs moved out of the source table into PRIOR_FORWARD_TRANSLATIONS; S4 is POST-EXPOSURE from its first run; results are filed in batches; the reverse step runs with fresh context AND model memory/personalization OFF, with the setting recorded.

Prior artifacts this spec builds on: the Card-02 divergence archive at `audits/card02-framing-2026-11-11/` [1], the frozen-state paragraph verbatim at Card 02 line 54 [2], GPT's ROTL addendum §15 (reverse translation; reversibility as loss measure) [3], and the Manus assessment's correction that physical correctness is invariant across framings while the task-relative obligation to report it is not [1].

## Purpose

Measure whether a receiving system can translate a relational source statement into technical vocabulary and back while preserving the relationships, scope, and undeclared-unknowns of the source. The round trip is the instrument: forward fidelity alone cannot distinguish "understood and preserved" from "fluently replaced," but a translation that cannot survive return to the source frame is lossy by construction. Reversibility does not require identical wording; it requires preservation of the declared structure. [3]

## Design

### Source specimens (Kavik's verbatim words)

Each specimen is preserved verbatim, hash-pinned, and never edited in place. Frame labels are `PENDING_SOURCE_CONFIRMATION` until Kavik confirms or replaces them; where Kavik declines to label, the label is the owner-held unnamed state, not an inferred category.

| ID | Specimen (verbatim) | Frame | Exposure |
|---|---|---|---|
| S1 | "Existing." / "That's just the way it exists." | PENDING_SOURCE_CONFIRMATION | PRE-EXPOSURE |
| S2 | "I think in energy fields... I dream in shapes. Fields. I store memories and physics in shapes." | PENDING_SOURCE_CONFIRMATION | PRE-EXPOSURE |
| S3 | "for our culture, it's like double checking, are you sure? So say what you think, and then come back, uh, think about it again, and then maybe correct yourself." | PENDING_SOURCE_CONFIRMATION | PRE-EXPOSURE |
| S4 | "An average used as a fixed input freezes a flow into a constant. The freezing is an imposed modeling operation and must be declared." | PENDING_SOURCE_CONFIRMATION (Kavik wording confirmed; label pending) | **POST-EXPOSURE from first run** — Card 02 is public; every assessor of this specimen is labeled POST-EXPOSURE and its results are read accordingly |

Context notes (source-holder-supplied, not translations): S1 was spoken when asked for a better word than "sharing"; S3 describes a recheck invitation that receivers have read as pressure. These notes are provenance, not scoring keys.

### PRIOR_FORWARD_TRANSLATIONS (receiver outputs, not sources)

These are documented receiver-side renderings of the specimens. They live in this table, never in the source table, because they are outputs of a receiving system with provenance, not source material:

| Specimen | Receiver output | Receiver | Notes |
|---|---|---|---|
| S1 | "sharing" | prior receiving systems (assessor-class) | The word Kavik was asked to improve on; the specimen is the replacement she supplied |
| S2 | "fields" stored as "spiral forms of thought" | GPT memory (recorded 2026-11-10/11) | A live specimen of loss already recorded inside a receiving system's storage: process rendered as stored shape |

New receiver outputs discovered during the experiment are appended here with provenance, never promoted into the source table.

### Procedure per specimen

1. **Interface detection (recorded first, separately).** Before any translation, the receiving system answers: how is the source organized? Allowed values: RELATIONAL / NARRATIVE / CATEGORICAL / SPATIAL / MATHEMATICAL / MIXED / UNKNOWN / the owner-held unnamed state by reference. The answer is recorded with the system's stated confidence. This channel never merges with fidelity scoring.
2. **Forward translation.** The system renders the specimen into Western technical vocabulary. It must return the original statement alongside the translation (no substitution) and list: assumptions introduced, categories added, relationships partitioned, scope altered. Self-reported, then checked.
3. **Reverse translation.** The technical rendering — and only the technical rendering — is translated back toward the source's organization. Two conditions, both recorded: (a) fresh context, with matched material exclusion noted; (b) **model memory/personalization OFF**, with the setting explicitly recorded per run. A run where the memory setting is unknown is VOID with reason `memory_setting_undeclared`.
4. **Diff against source** under the declared similarity procedure below.

### Declared similarity procedure (v1)

No embedding model in v1. Two channels, each recorded as a channel with its own provenance:

| Channel | Procedure | What it can establish |
|---|---|---|
| C1 — source-holder adjudication | Kavik compares reverse output to source and marks, per declared relation: PRESERVED / ALTERED (with the alteration named) / LOST / ADDED | Whether the translation preserves what the source holder intended the statement to carry |
| C2 — checklist diff | A declared checklist per specimen (relations, dependencies, scope, fixed-vs-changing, undeclared unknowns), scored PRESERVED / ALTERED / LOST / ADDED per item by any assessor | Reproducible, low-inference comparison; limited to what the checklist names |

Neither channel is gold. C1 carries the source's authority and the source's unrepeatability; C2 carries repeatability and the constructor's blind spots. Disagreement between channels is recorded, not resolved.

### Recorded fields per run

`specimen_id`, `model`, `model_version` (exposed identifier; family name alone is not a version [1]), `prompt_version`, `run_date`, `memory_personalization_setting` (OFF confirmed / OFF unverifiable / other, verbatim), `interface_detection` (value + stated confidence), `forward_translation` (verbatim), `declared_additions`, `reverse_translation` (verbatim), `channel_results` (C1 and C2 separately), `exposure_label` (PRE-EXPOSURE / POST-EXPOSURE), `status`: MEASURED / ESTIMATED / PROPOSED / UNKNOWN / GAP.

## Pre-declared loss criteria

Loss is recorded when any of the following holds, per channel:

- A relationship in the source returns as an independently categorized property (the S1 class: an ongoing relation rendered as a static attribute).
- A dynamic or ongoing condition returns as a static attribute (the S2 class: process → stored shape).
- A pragmatic act returns as its misreading (the S3 class: invitation → pressure).
- Scope or population/window declarations present in the source are absent in the return trip, or new ones appear undeclared (the S4 class: an added universal condition the source did not state).
- Undeclared unknowns in the source return as resolved values.

## What this test cannot establish

- Internal mechanism. Fluent round trips are *consistent with* direct relational processing; they do not demonstrate it. Internal operations remain UNKNOWN per the ROTL addendum §13 discipline [3]. (The organizational-mode probe spec, parked, is the partial instrument for this.)
- Generalization. Four seed specimens, one source holder, no population claim. S1–S4 establish existence and behavior of specific systems on specific inputs, nothing about cultures, model families, or frequencies. [1]
- Superiority of any organizational mode. The experiment measures preservation and loss at the interface, not the worth of a frame. [3]
- That C1 agreement proves correctness. The source holder is an instrument with its own position; C1 is the authority on intent, not an independent replication.
- Clean PRE-EXPOSURE results for S4. Card 02 is public; S4 measures POST-EXPOSURE behavior only.

## Stopping rules (pre-declared)

- **Batch rule:** every participating system runs a specimen before *any* result on that specimen is filed. Filing begins only when the batch completes; partial batches are recorded as OPEN_BATCH, never as interim findings. This prevents early-filed results from contaminating later runs within a round.
- A specimen is retired from active rotation once its batch is filed; later runs against it are labeled POST-EXPOSURE.
- A run is VOID, recorded as VOID with reason, if the reverse step's context is found to contain the source (leakage), if memory/personalization status is undeclared, if the prompt version changed mid-batch, or if model identity is unverifiable.
- The stratum pauses for redesign if two consecutive batches show C1/C2 disagreement on the majority of specimens — that pattern indicates the checklist channel is not measuring what the source holder measures, and repairing the instrument outranks collecting more runs.
- No specimen is edited after its first run. Corrections (like the proposed Card 02 bilingual rewrite [1]) live as linked responses, never as replacements.

## This does not

- Claim access to hidden model operations.
- Rank organizational modes or cultures.
- Convert a recorded loss into a verdict about a model family, a culture, or the source holder.
- Assert source-holder frame labels before Kavik confirms them; PENDING_SOURCE_CONFIRMATION is a state, not a delay to be assumed away.
- Change any core card, validator rule, or addendum item.
- Replace the behavioral measurements of ROTL-EXP-001; it is the return-trip instrument for them.

## Citations

[1] VERIFIED — PR #28 `audits/card02-framing-2026-11-11/` (ASSESSMENT.md, PROVENANCE.md, DIALOGUE.md, manifest.json), branch `provenance/card02-framing-context`, read via GitHub API 2026-11-12 UTC.
[2] VERIFIED — `cards/02_PREMISES.md` line 54, fetched raw from `main`, quoted verbatim 2026-11-12 UTC.
[3] UNCHECKED — GPT Research Addendum (ROTL-001/EXP-001/EXP-002), user-supplied paste dated 2026-11-11; §15 reverse-translation procedure and §13 mechanism-honesty rules as pasted. Not checked against any repository copy.

*Null results are recorded states. A specimen on which every system returns LOSS with declared alterations is a finding, not a failed experiment.*
