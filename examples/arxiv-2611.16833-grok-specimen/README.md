# Specimen: arXiv 2611.16833 from Grok's assessment

Status: test specimen for the section-level read ceiling (Card 07 4b). Every
value is CARRIED from Grok's assessment of the paper (Grok chose the paper),
relayed by Claude on 2026-11-15. Nothing here was read by whoever built the
record, and nothing here is an assessment of the paper.

Rebuild: `bash examples/arxiv-2611.16833-grok-specimen/build.sh`.

Sources, as Grok declared them:
- S1 the paper (Chen, He, Zhou, Bu; PKU; submitted 2026-11-12): FULL_TEXT for
  abstract, introduction and methods; results and limitations UNDECLARED.
- S2 CASRAI writeup, 2026-11-15: PRESS_RELEASE.
- S3 alphaXiv summary: SNIPPET.

Expected, and observed: `check` prints VALID — FLAGGED (4).
- C1 (the resistance measure) rests on S1:methods, a section read in full; no flag.
- C2–C5 (results) carry MEASURED_PRESENT and rest on S2 and S3 only; each exceeds
  the ceiling of both, so each is flagged.
- Had C2–C5 also rested on S1:results, the section ceiling would give
  UNDECLARED for that rest and flag it as well.

Choices made when building (not in the relay):
- C2–C5 support UNTESTED: the relay gives their grades, not their support.
- C1 carries no measurement grade: it states a definition.
- Claim texts are the relay's paraphrases, not quotes from the paper.
- Design checks other than measurement validity are NOT_CHECKED (not in the relay).
- No claim is marked central.
