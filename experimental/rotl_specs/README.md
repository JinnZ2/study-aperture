Status: two PROPOSED experiment specifications from Kimi, filed verbatim 2026-11-11. Neither is built or run: no harness, schema, fixture or test exists for either. The probe spec carries its own status PARKED (blocked on compute); that is kept. All S1-S4 frame labels stay PENDING_SOURCE_CONFIRMATION until the source holder confirms or replaces them. No core card, validator rule, ADDENDUM item or `assess.py` behaviour changed.

# ROTL experiment specs (proposed, not built)

```
audits/kimi-frontier-sweep-2026-11-11/   (the sweep that proposed four pilots)
        |
        |  chat-side order: 1 EXP-002 -> 2 HAIMEDA routing -> 3 geometry -> 4 probe PARKED
        v
experimental/rotl_specs/
   EXP-002-reversible-translation-spec.md     PROPOSED   behavioural only; relational -> technical -> relational
                                                         2 channels (C1 source-holder, C2 checklist); batch filing
   organizational-mode-probe-spec-PARKED.md   PARKED     linear probe on an open-weight model; needs a GPU or hosted
                                                         compute + the EXP-001 matched corpus; neither exists yet
   manifest.json                              hash pins for both files
```

The HAIMEDA routing spec and the geometry pilot (positions 2 and 3) have no spec on file. Their absence is a state, not an omission to fill.

## Provenance

| Field | Value |
|---|---|
| Producer | Kimi (model output; version undeclared) |
| Requested by | Kavik (repo owner), per each spec's INPUT BRIEF |
| Supplied | as two uploaded files, 2026-11-11 |
| Bytes | copied unchanged (`cmp` against the upload: identical); SHA-256 in [manifest.json](manifest.json) |
| Edits | none. Corrections go in a dated, linked response; the specs stay as filed |

EXP-002 carries its own correction record (first draft had filled the frame labels itself; now all PENDING). That record is part of the filed text.

## Citations in the specs, checked against this repository at filing

Only references to this repository can be checked here. The specs' own VERIFIED / UNCHECKED tags are copied, not endorsed.

| Spec | Ref | Spec's tag | Located at filing? |
|---|---|---|---|
| EXP-002 | [1] `audits/card02-framing-2026-11-11/` (PR #28) | VERIFIED | yes, on `main` (merged in c26fbd2) |
| EXP-002 | [2] `cards/02_PREMISES.md` line 54 | VERIFIED | yes; line 54 is the frozen-state paragraph ("An average is a state variable only where...") |
| EXP-002 | [3] GPT Research Addendum §13 / §15 | UNCHECKED | not in the repository (supplied material) |
| probe | [1] GPT Research Addendum §13 | UNCHECKED | not in the repository |
| probe | [2] `SCREENED_NO_INDICATORS_FOUND` in `experimental/publication_provenance/README.md` "This does not" | VERIFIED | **NOT LOCATED.** That section exists; the token appears in no file on `main` or any fetched branch, other than the sweep record that quotes it. The spec's VERIFIED tag is not reproduced here |
| probe | [3] 2026 interaction-probe caution | UNCHECKED | not checkable here; the spec dates its sweep 2026-11-12, the sweep record is dated 2026-11-11 (time zone difference likely, not established) |
| probe | [4] frame-label rule, PR #28 DIALOGUE.md E03 handling | VERIFIED as instruction | E03 exists on `main`; it is the user's self-description. The rule itself is in the owner's instruction, not a stated rule in that file |
| probe | [5] PR #28 ASSESSMENT.md denominators / model-version identifiers | VERIFIED | file exists on `main`; contents of the discipline not re-read for this filing |

## Dependencies declared by the specs (none met at filing)

```
EXP-002   needs  source-holder confirmation of S1-S4 frame labels      PENDING
                 a per-specimen C2 checklist                           not written
                 run records with memory/personalization setting       none
probe     needs  EXP-001 matched-content corpus, labels confirmed      does not exist
                 open-weight model + >=16 GB GPU or hosted compute     not available (phone environment)
                 re-read against then-current literature on unpark     not due
```

## Boundaries

- Nothing in this directory is a result. A future run gets its own dated record; it does not edit these files.
- Neither spec is imported by `assess.py`, the lab, or `run_checks.sh`.
- No culture, model family or source holder is characterized here; the specs' own "This does not" sections apply in full.
