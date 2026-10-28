# Addendum: work to be done

Status: open work list, 2026-10-28. Nothing here is implemented unless its state says so. Items are recorded as gaps on purpose; none of them is resolved by being written down.

States used below: **OPEN** (needs work), **OWNER** (needs the owner's decision before any work), **UNDETERMINED** (not inspected yet; no finding either way), **MEASURED** (inspected; the finding is linked, and follow-ups are separate items).

## A. Translation layer: oral reasoning → English → code

```
oral reasoning ──────────► English ──────────► code
relational, held in        linear; context      closed sets; anything not
context, checked by        moves into           named in advance is invalid
practice over time         footnotes            or dropped

loss 1: who, when, how it was checked    loss 2: early commitment to categories
```

Working rules already in use: leave gaps instead of coining words; keep the shape (relations) when labels aren't ready; mark things as not interpretable at the moment rather than forcing a reading.

| # | Item | State |
|---|---|---|
| A1 | **A third missing-value state.** `UNDECLARED` = no one recorded a value. `UNDETERMINED` = evidence in hand can't decide. Neither covers: *the meaning is held, but can't be carried into this language yet.* Open questions: should records represent this at all, and if so, how, without coining a word for it? Deliberately left unnamed here. | OWNER |
| A2 | **Record translation losses instead of patching them.** Some bugs will turn out to be places where English or code cannot hold what the original reasoning holds. These need a place to be recorded as translation losses (what was lost, at which step), so they stay visible instead of being smoothed over. Where that record lives is undecided. | OPEN |
| A3 | **Closed vocabularies force early commitment.** Every value set in `assess.py` must be fixed in advance. The sentinels (`UNDECLARED`, `UNDETERMINED`, `NODATA`) are a partial workaround. Not yet assessed: which sets push assessors into a premature choice. | UNDETERMINED |
| A4 | **Shape as a carrier.** Relations can be kept without labels (diagrams, graphs, the provenance graph tools). Not yet worked out: how a record holds shape-only content that `check` and `report` can carry without forcing it into words. | OPEN |

## B. Toolkit

| # | Item | State |
|---|---|---|
| B1 | **Other lab outputs have no import path.** `labref` covers integrity-checker reports only. Criterion-to-conclusion mappings and review results have no structured way into a record. | OPEN |
| B2 | **Free-text guard.** Lab status words typed into `tool --output` are not blocked; CLAUDE.md says to use `labref` instead. Blocking it in code would also reject legitimate notes that mention a lab result. | OWNER |
| B3 | **Review history is protected by convention only.** `reviews/<run>/` and `attempt-NN-*` directories are "preserve unchanged" in CLAUDE.md, but nothing checks it. A hash manifest test (like `vendored/SHA256SUMS`) would enforce it. | OPEN |
| B4 | **Methods referenced but not run:** `presignal_ledger`, `rank_detector`, `grounding-layers` (needs NumPy), `frame_probe`, `observer_position_control`. Their cards describe upstream procedures; none is verified by this toolbox. | OPEN |

## C. Independence and testing

| # | Item | State |
|---|---|---|
| C1 | **No independent run yet.** All five upstream repositories share one author, so by Card 03 the toolkit's own methods are `SHARED_UPSTREAM`: agreement between them is not independent confirmation (and not evidence against). The cheapest route to an independent test: someone else runs `AI_ENTRY_PROMPT.md` on a paper they chose themselves, and the result is recorded with its independence route. | OPEN |
| C2 | **Within-run n in Simulators.** A claim that rests on a single simulation run or seed would be `UNDERPOWERED`, and simulations can raise n cheaply (more seeds, parameter sweeps). This is distinct from replication count: every new study starts at one, which is a state, not a defect. Measured 2026-10-28 ([audits/simulators-run-count](audits/simulators-run-count/README.md)): 81% of claims in the 43 candidate folders involve no random draw; 87 rest on one draw; re-drawn at 20 other seeds, 32 hold, 35 keep their direction with a moving magnitude, 12 fail at some seeds (verified), 1 doesn't reproduce at its own seed. | MEASURED |
| C2a | **Returning the C2 findings to Simulators.** Its `READ_ME_THIS_WAY.md` asks for dated notes beside originals, not overwrites; this session cannot write to Simulators. Includes one new red by its own `KNOWN_RED.md` protocol (`cooperative-substrate-proof/selftest.py`). | OWNER |
| C2b | **The 67 HOLDS / DIRECTION-HOLDS verdicts in C2 were not independently re-verified.** Verification overturned 13 of 25 first-pass failures, all toward false failure; the same scope errors could widen reported magnitude ranges. | OPEN |
| C3 | **Popularity is not a usable signal here.** Stars and citations measure human attention; this toolkit is read mostly by AIs, which leave no such trace. Usage evidence would need a different channel. Whether and how to collect it is undecided. | OWNER |

## D. Repository housekeeping

| # | Item | State |
|---|---|---|
| D1 | **CI runs twice per pull-request commit** (push + pull_request triggers). Limiting `push` to `main` in `.github/workflows/checks.yml` is a one-line change. | OPEN |
| D2 | **Merged branches remain on GitHub** (`add-claude-md`, `repo-integrity-ci`, `lab-ref`). Delete them from the Branches page, or enable "Automatically delete head branches" in repository settings. | OWNER |
| D3 | **Discoverability.** AIs don't find repositories on their own yet; a human still points a model at the cards. The README's opening is where adoption starts. | OPEN |
