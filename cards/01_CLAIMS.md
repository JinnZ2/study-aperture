# Card 01 — Claims, conditionals, and term drift

**Provenance:** three upstream tools from the Simulators repository (`@0655e8b`): `tools/conditional_claims.py` (executable, stdlib, selftest), `term-drift-citation/` (documented procedure), and `falsifier-audit/` (documented procedure, does not rank). Status: this card adapts all three to publication text.

## Purpose

Extract what the publication actually claims, keep the claims rigid when they are conditional, catch terms whose meaning moved between the measurement and the later use, and inventory the falsifiers. A claim without an evidence location is not yet a claim.

## 1. Claim extraction

For each claim, record:

- **id and verbatim text** (quote, don't paraphrase — paraphrase is where drift enters)
- **evidence location** — where in the publication the support lives (table, figure, page, derivation step). If you cannot find one, record `NO_EVIDENCE_LOCATION` and leave support `UNDETERMINED`. This is a value, not an error.
- **measurand** — what was measured, not what it is called (feeds Card 02)
- **conditional form** if the claim is an if-then

## 2. Conditional-claim rigidity (upstream executable: `conditional_claims.py`)

Conditional claims collapse in retelling: "IF [A] THEN [B]" quietly becomes "[B]", "[A] implies [B]" becomes "[B] implies [A]", or a biconditional flattens to a one-way implication. The upstream tool runs a truth table over bracketed atoms and names the collapse. It checks form, not truth.

```
python3 ../vendored/conditional_claims.py compare "IF [pose expanded] THEN [risk rises]" "[risk rises]"
# -> names the collapse: consequent extracted, antecedent dropped
```

Rules carried over unchanged:
- Atoms go in [brackets]; operators are IF..THEN, ->, <->, AND, OR, NOT.
- **Does-not-transfer is not refuted**; absence of a retest is not refutation (from `term-drift-citation/`).
- If the publication's restatement of its own claim (abstract vs. results vs. discussion) drops, flips, or flattens the operator, record it. That is a finding about the claim, not about the world.

## 3. Term drift (upstream: documented procedure)

For each load-bearing term, check whether the **referent held** between where the measurement happened and where the term is later used:

- Find the measurement that originally fixed the term (study, task, instrument).
- Find the later use (abstract, discussion, review, press coverage).
- Ask: would the original instrument, applied to the later use, return the same classification? If the later use would not have been scored the same way, the term drifted.
- Record: `REFERENT_HELD`, `REFERENT_DRIFTED`, or `CANNOT_TELL_WITH_MATERIAL_IN_HAND`.

## 4. Falsifier inventory (upstream: documented procedure)

List what would have to be observed for the claim to be wrong. For each falsifier record whether the publication reports testing it. The inventory is not ranked and not scored. A publication whose central claim has no stated falsifier gets that recorded as a fact about the claim's state, not as a verdict on truth.

## Limits

- Paraphrase during extraction reintroduces the drift this card is supposed to catch; quote.
- The conditional tool checks form only; a faithfully preserved conditional can still be false.
- Term-drift calls are limited by the material in hand; `CANNOT_TELL` is a valid, expected outcome.
