# Card 06 — Records, drift, and decisions

**Provenance:** three upstream sources: `decision-aperture/decision_ledger.py` and `assessment_frame.py` (executable, `5f8d316`, stdlib), `drift-archive-audit` (documented procedure, `3d403a1`, stdlib), and `chain-position-detectability`'s claim labeling (documented note). Status: mixed — vocabulary and rules adapted; the executable ledger is re-implemented inside `assess.py` rather than vendored, because the upstream ledger is built for software requests.

## 1. Claim labeling: OBSERVED / DERIVED / PROPOSED

From `chain-position-detectability`: every statement in the record carries one of three labels —

- `OBSERVED` — directly measured or witnessed in the material
- `DERIVED` — follows from an observed statement plus a stated rule
- `PROPOSED` — put forward without observation or derivation

Applied to a publication: label each claim from Card 01, and label your own assessment statements the same way. A review that quietly upgrades `PROPOSED` claims to `OBSERVED` in its summary table has committed the exact failure this labeling makes visible.

## 2. Target vs. rendering (from `drift-archive-audit`)

The target is what the work was aimed at; the rendering is what got written. **Removing a rendering does not close its target.** When a study is retracted, corrected, or superseded, the question it was aimed at remains open — the gap does not close with the artifact. Rules carried over:

- `UNSET`, `UNCLEAR`, `UNATTRIBUTABLE` are **values**, not invitations to infer.
- No verdicts on whether changes were good; report where things moved.
- **A gate may block SCORING. It may NOT block READING.** Every declined read is logged in a `DECLINED` register when declined — a gate can look like "nothing found" downstream, and the register makes the decision-not-to-look visible.
- Authorship caution: a git author field or byline identifies the pusher, not necessarily the content author. Read targets as renderings of aims, not as the aims.

Applied to a publication: distinguish the question (target) from the paper (rendering). A failed rendering of a good question is a gap; a good rendering of an unexamined question is also a gap.

## 3. The decision ledger (re-implemented in `assess.py`)

The assessment separates **confidence in a publication's claims** from **whether those claims justify an action**. The ledger holds decision surfaces — questions the reader's decision actually turns on — with states:

| State | Meaning |
|---|---|
| `DETECTED` | surface located; nothing more known |
| `UNRESOLVED` | exposed; no answer on record |
| `RESOLVED` | answer + named author on record — the only path requires both |
| `DEFERRED` | deliberately postponed; owned, with reason |
| `NOT_APPLICABLE` | bears no consequence here |

Two prohibitions enforced in `assess.py`'s code, not promised in prose:

- **No silent resolution.** The only transition into `RESOLVED` requires an answer string and a named author.
- **No defaults for unknowns.** A surface with no answer stays `UNRESOLVED`, and the report prints unresolved surfaces **first** — the absence of a decision is the headline, not the footnote.

Missing decision context produces **conditional implications** ("if you need X, then the hormone claims matter and are unsupported"), not invented recommendations.

## 4. Classifying a miss before repairing it (glyph E1-E4)

**Provenance:** JinnZ2/Simulators `tools/glyph_reasoning.md` (CC0, co-authored, delivered 2026-10-25; blob `3f91affa` on `main` at `b2a9a1a`), section "error types". Status: four types adopted as a closed set; the six-step procedure is not adopted here. The source's own limit carries over: nothing measures how often each type occurs, and no instrument checks that a classification is right.

A stated miss is tagged with the type it is, because the four call for different repairs:

| Type | The miss | Repair it calls for |
|---|---|---|
| `E1_DROPPED_VARIABLE` | a variable the environment holds was left out | add the variable; re-run |
| `E2_STALE_CONDITIONS` | values from earlier conditions used after they changed | re-measure under current conditions |
| `E3_DEFAULTED_SLOT` | a slot assumed from history or a claim, not tested | test the slot |
| `E4_UNCHECKED_OBSERVER` | the observer's own state, frame or calibration unchecked | check the observer |

Enforced in `assess.py`: `--error-type` (repeatable) on `tool` and `design`. A tag is accepted only on a `RUN` tool or a `CHECKED` design check whose output or finding states the miss; an unknown type, a duplicate, an empty list, a tag on something not run, or a tag on an empty field is rejected and the file is left unchanged. The report lists tagged entries under each type. Untagged entries are **unclassified, not clean**, and an empty type is not printed as a zero.

## 5. What this card refuses to do

- No universal numerical quality score for publications.
- No mixing of vocabularies: measurement grades (Card 02), tool states, claim support, and decision states are separate fields; a low support grade is not a decision, and a resolved decision is not a truth.
- A zero or a blank is a property of the measurement, not of the world.
