# Routing example: a non-empirical publication

The assessed publication is the README of the `chain-position-detectability`
research note (WO-1) — a commentary, not a study. The router sends only cards 00,
01, and 06; the quantitative cards (02, 03, 04, 05) return `NOT_APPLICABLE` — a
legal output, not a failure. Card 01's finding: the note already labels its own
claims OBSERVED / DERIVED / PROPOSED, which is exactly the labeling Card 06 asks
assessors to apply.

Reproduce:
```sh
python3 ../../assess.py check --file assessment.json
python3 ../../assess.py report --file assessment.json
```
