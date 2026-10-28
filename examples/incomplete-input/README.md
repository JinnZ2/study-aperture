# Failure-mode example: incomplete input

An abstract-only assessment of an unknown preprint. The record is **VALID** (missing
values are values, not errors) but the report is visibly INCOMPLETE: no publication
type declared, so no cards route; the one extracted claim has `NO_EVIDENCE_LOCATION`
and support `UNDETERMINED`; the premise and independence cards are `BLOCKED` on
materials. Nothing was converted into a negative finding or a completion.

This is the intended behavior: an incomplete assessment that says so is worth more
than a complete-looking one that doesn't.

Reproduce:
```sh
python3 ../../assess.py check --file assessment.json
python3 ../../assess.py report --file assessment.json
```
