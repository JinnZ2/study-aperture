# Design note, 2026-11-16

Status: PROPOSED. Co-authored. CC0. A note for the slot/tag design, filed beside
the explain-then-do protocol. Nothing here is implemented in `assess.py`.
Lojban items are from memory and marked VERIFY * by the author; they are not
verified here. The DISCARD section is kept as a record of what was discarded.

Pasted verbatim as delivered.

```text
FROM THE DESIGN NOTE (usable)
1 DEGRADED state = real gap in branch 4
  now: required slot empty → VOID on the whole claim
  note: keep filled slots, list missing ones, let unaffected
        processing continue, block downstream from treating it as established
  → same shape as MIXED in 2b: partial information, typed and carried
2 self-reference: better as a slot FILL than an exemption
  "I feel warm" → x1 = speaker, evidential = internal experience
  exempting it drops a record; filling it keeps the chain
3 the 4 classes need different slot shapes:
  judgment     better/good → good FOR whom, BY what standard
  comparative  more/efficient → x1 vs x2, IN what property, BY how much
  emotive      warm/hostile → physical vs social reading is itself a slot
  fear-based   threat → to whom, from what evidence, within what time

DISCARD: the commentary's causal story
  "Langevin" came from the voice transcription of your "Lojban"
  (this morning's voice log shows it; I then asked about the drift equation)
  FDIP-NET is a separate record from 11-15 (attention-sensor refs),
  not a pivot caused by the word
  → a narrative built after the fact, no evidence behind it
  its praise ("masterstroke", "brilliant") carries no checks → no weight
  its one useful line: FDIP protocol, reproduce ≠ generalize

LOJBAN GAPS IN OUR BLOCK   (from memory, VERIFY *)
  se'o = I know by internal experience → this is the self-reference slot,
        already in the language
  ja'o = I conclude → DERIVED (missing from our map)
  ka'u = cultural knowledge → NOT auto-PROPOSED
        → route through the oral-record discriminator
          (shared, multi-generation, checkable, teller not central)
          the same filter-bias problem from this morning, at the tag level
  zmadu: x1 exceeds x2 in property x3 by amount x4   (comparative)
  xamgu: x1 is good for x2 by standard x3            (judgment)




THE FOUR CHECKS (from the 07:xx discriminator, navigation case)
  shared        held by a community, not one person
  multi_gen     stable across generations
  checkable     makes claims about the world that can be tested
  not_central   the teller isn't the subject of the claim

CARRIED → OBSERVED
  the navigation record already set the convention:
  "SOURCE: oral tradition, holder relayed; status OBSERVED"
  → ka'u passing all 4 = OBSERVED, with the transmission in provenance
    (oral · multi-generation · holder relayed)
  → this keeps the tag scale at three values; the "carried" information
    lives in provenance instead of a fourth tag
  any check n → PROPOSED (unchanged)

REST HOLDS
  se'o scoped to the speaker; external → DEGRADED, nothing waived ✓
  VOID > FAIL > DEGRADED > UNDECIDED, with missing items still listed ✓
  truncation → VOID ✓
```

Note on scope: "CARRIED" in this note is the epistemic-tag sense. In this repo
`CARRIED` is also a read depth (Card 07), a different set; the note does not
change Card 07.

Observer slots: human_reader = null, ai_reader = null.
