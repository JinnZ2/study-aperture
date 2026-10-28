# Card 00 — Routing and the applicability gate

**Provenance:** adapted from `decision-aperture` (routing over assessment frames) and the Simulators `grounding-layers` scope guards. Status: toolbox adaptation of two upstream documented procedures. Upstream code exists (`decision-aperture/assessment_frame.py`) but is built for software-development requests; this card is the publication-assessment rewrite.

## Purpose

Decide which cards apply to *this* publication before any of them run. "Assess any publication" means **routing**, not universal validity. A card that does not apply returns `NOT_APPLICABLE` — a legal output, not a failure. Forcing every tool onto every paper is the failure mode this card exists to prevent.

## Procedure

1. **Identify the publication type.** One of:
   - `EMPIRICAL` — study generating data from the world
   - `REVIEW` — synthesis of prior studies (including meta-analysis)
   - `THEORETICAL` — argument, derivation, model
   - `SIMULATION` — computational experiment on constructed inputs
   - `COMMENTARY` — essay, editorial, position, research note
   - If you cannot tell from the material in hand: record `UNDECLARED`. Do not guess.
2. **Record the material you actually hold** (full text, abstract only, preprint, methods only). Every later grade is conditioned on this. Do not claim material you have not read.
3. **Record the decision context** — what the assessment is *for*. If absent, downstream implications must be stated conditionally, not as recommendations.
4. **Route (defaults, not gates):**

| Type | Cards suggested by default |
|---|---|
| EMPIRICAL | 00, 01, 02, 03, 04, 05, 06 |
| REVIEW | 00, 01, 02, 03, 04, 06 |
| THEORETICAL | 00, 01, 04, 06 |
| SIMULATION | 00, 01, 02, 04, 06 |
| COMMENTARY | 00, 01, 06 |
| UNDECLARED | none — stop and declare first |

**The table is a default, not a gate.** Applicability is ultimately determined by
the *claims* and the *available inputs*, not the type alone: a COMMENTARY that
cites an empirical literature still runs card 03 on that lineage; a THEORETICAL
paper with competing candidate explanations still runs card 04. When you add a
card outside the default, record the override as a tool run with its reason.

## Standing rules

- **Ordinary study-design checks are not optional.** Confounding, selection, measurement validity, uncertainty treatment, multiplicity, missing-data handling, and preregistration status must be checked on every empirical study *before* the toolbox's distinctive cards run. The cards in this toolbox add discipline on top of ordinary appraisal; they do not replace it.
- `NOT_APPLICABLE` is a first-class output.
- A quantitative card applied to a non-quantitative publication must return `NOT_APPLICABLE`, not a zero and not silence.
