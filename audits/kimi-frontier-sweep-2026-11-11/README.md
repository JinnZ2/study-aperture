Status: preserved model output (Kimi), dated 2026-11-11, filed verbatim as a record. Nothing in it has been built, run or adopted. Three cited sources are recorded as EXISTS (checked chat-side, not in this session); every number attributed to them is UNCHECKED; the remaining citations are NOT CHECKED. No core file, card, schema or test changed. Build freeze on code is in force: the follow-up specs, when supplied, are filed PROPOSED, not built.

# Kimi frontier sweep, 2026-11-11

```
input brief ──► Kimi ──► SWEEP.md (verbatim) ──► this README (provenance + ledger)
   │                         │                        │
   repo state                4 frontier areas         citation states
   + Card 02 material        4 proposed pilots        two orderings (Kimi / chat-side)
   + GPT addendum            0 executed               pending specs: 2, PROPOSED
   + Manus material
   (as supplied by Kavik)
```

## Provenance

| Field | Value |
|---|---|
| Producer | Kimi (model output; version/backend not declared) |
| Date | 2026-11-11 |
| Input brief | study-aperture repository state + prior Card 02 / GPT addendum / Manus material, as supplied by Kavik |
| Input brief bytes | not supplied; the exact prompt and attachments Kimi received are UNDECLARED |
| Capture | transcribed from a chat paste supplied by Kavik; not a signed or complete export |
| File | [SWEEP.md](SWEEP.md), text exactly as pasted; no heading, status line or correction added |
| Integrity | [manifest.json](manifest.json) pins SHA-256 and byte count. A hash detects local change; it does not authenticate the producer or any cited claim |

Capture transformation, disclosed: each inline citation in the paste arrived as the byte sequence `U+200B U+FFFC U+200B` (zero-width space, object-replacement character, zero-width space) with no link or reference text. Nine such markers are preserved unchanged. Which source each marker pointed to is NOT RECOVERED from the paste. One citation position in area 2 (`fewer effective dimensions ,`) carries no marker at all; the stray space is kept.

## Citation ledger

States: `EXISTS` = the source was located (chat-side, before filing; not re-verified in this session). `UNCHECKED` = the stated number has not been compared with the source. `NOT CHECKED` = not even existence has been checked. None of these states is evidence the sweep's reading of a source is correct.

| Sweep area | Source as named | Source state | Stated figure | Figure state |
|---|---|---|---|---|
| 1 | SAE code-correctness study, arXiv 2510.02917 | EXISTS | F1 0.821 (incorrect code) / 0.504 (correct code) | UNCHECKED |
| 3 | WorldView-Bench, arXiv 2505.09595 / JAIR | EXISTS | 0.13 average entropy over cultural perspectives | UNCHECKED |
| 4 | HAIMEDA, arXiv 2605.26942 | EXISTS | >83% structured-entity / 72% semantic-fabrication detection | UNCHECKED |
| 2 | 30-language representational-degeneration study (2026) | NOT CHECKED | monotone with data availability | NOT CHECKED |
| 3 | Frontiers 2026 epistemic-justice analysis | NOT CHECKED | quoted phrase "technological enforcement of epistemic hierarchy at scale" | NOT CHECKED |
| 4 | G-SPEC semantic firewall | NOT CHECKED | 0.2% hallucination | NOT CHECKED |

Named or implied in SWEEP.md but absent from the brief, so recorded here as NOT CHECKED rather than left out: linear concept probes over expanding context (area 1); the 2026 interaction-probe paper on behaviour vs representation (area 1); cross-lingual collapse of reasoning traces (area 2); IsoScore-type measures (area 2); Indigenous Knowledge Systems evaluation panels (area 3); Kpum & Gasa (area 3); ATA deterministic symbolic runtime (area 4).

## Repository references in the sweep, located against main

The sweep describes this repository from its brief. Where that description can be checked against `main` at filing, the result is recorded; nothing is repaired.

| Sweep reference | Located on main? | Note |
|---|---|---|
| ROTL-EXP-001 / EXP-001 §13, EXP-002, ROTL-001 | no | supplied material (GPT addendum); not present in any file on `main` |
| Cards 07/12 | no | `cards/` holds 00..06. [DIALOGUE.md E01](../card02-framing-2026-11-11/DIALOGUE.md) records the user's mention of Cards 07/11; [PROVENANCE.md](../card02-framing-2026-11-11/PROVENANCE.md) states no Card 07-12 is established |
| TB stratum frame taxonomy (RELATIONAL / NARRATIVE / CATEGORICAL) | no | supplied material |
| L0-L4 architecture, "the research report" | no | supplied material (Manus). `experimental/playground` has an "L0 closure" layer; whether it is the same L0 is not assessed |
| SCREENED_NO_INDICATORS_FOUND | no | not a value in any `assess.py` set |
| "E03 discipline" | partly | E03 on `main` is a dialogue excerpt (the user's self-description), not a stated labelling rule |
| A1 owner-held unnamed state | yes | [ADDENDUM.md](../../ADDENDUM.md) A1, state unchanged; this record does not name it |
| "assess.py already does this instinctively" (type-aware routing) | not assessed | a reading of the code, not checked here |

## Two orderings of the proposed pilots

Kept side by side; neither is adopted by filing it.

```
Kimi's order (SWEEP.md)                     chat-side reorder for Kavik's constraints
-----------------------                     -----------------------------------------
1 linear org-mode probe   [GPU, weights]    1 EXP-002 reversible-translation metric
2 EXP-002 round-trip metric [behavioural]   2 HAIMEDA-style type-aware routing spec
3 HAIMEDA routing spec    [design]          3 geometry on matched relational/narrative inputs
4 geometry measurements   [internals]       4 probe                       PARKED
```

The constraints behind the reorder were stated chat-side and are not enumerated in this brief. Visible in the repository and consistent with the reorder: the core is stdlib-only with no network, so the two pilots needing open-weight model internals (probe, geometry) sit furthest from what can run here; the probe is parked rather than dropped.

Kimi's own limits on the probe are part of the record: a failed probe proves nothing (nonlinear encoding), and probes supplement behavioural measurement, never replace it.

## Pending

Two specs from Kimi are expected. When supplied, each is filed under `experimental/` with a `Status:` line reading PROPOSED, not built, and linked from here. Until then this section is the only place they exist.

## Boundaries for future use

- This is one model's literature sweep, filtered through one brief. It is not a review, and agreement between it and earlier Card 02 / GPT / Manus material is not independent confirmation: they share the brief as an ancestor.
- No culture, model family or deployed system is characterized by this record.
- Corrections go in a separately dated record; SWEEP.md stays as filed.
