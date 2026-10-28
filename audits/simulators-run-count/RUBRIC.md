# C2 rubric: which claims in JinnZ2/Simulators rest on a single stochastic run?

## The question
"Within-run n": does a stated result (a claim-table row, or a numeric finding in a README/RESULTS file)
rest on ONE draw of a random process (one seed, one run, one permutation draw), such that a different
seed could change it? This is NOT about replication count (every new study starts at 1 — not a defect).
It is also NOT about whether the claim is true. Only: is the stated number a single draw, and does it hold
when re-drawn?

## Ground rules (from the repo's own READ_ME_THIS_WAY.md, AGENTS.md, READING_PROTOCOL.md)
- NEVER modify /home/claude/jinnz2/simulators. Copy what you need into YOUR work dir first:
  `cp -r /home/claude/jinnz2/simulators/<folder> <workdir>/` (also copy sibling folders/tools/ if imports need them;
  simplest is `cp -r /home/claude/jinnz2/simulators <workdir>/sim` once, ~62 MB, then work only inside it).
- Do not fix anything. A failing self-test or a claim that breaks is a RESULT; record it verbatim.
- Keep apart: FOUND, OUT_OF_SCOPE, UNRESOLVED. A scope limit a file states is its scope, not a missing result.
- `ILLUSTRATIVE` = made-up numbers to show a method → OUT_OF_SCOPE. `PLACEHOLDER` constants → out of scope ONLY
  if the claim is about the placeholder value itself; a claim about behaviour under randomness is still in scope.
  `CONSTRUCTED` (synthetic data) is IN scope if the synthetic data is random: a claim about how an instrument
  behaves on random constructed data can still be seed-dependent.
- KNOWN_RED.md at repo root lists expected failures (incl. 2 pinned-red calibration anchors). Check it before
  calling a failure new.
- numpy 2.x and scipy are installed. If something needs another package, mark NOT_RUNNABLE(reason); don't install.
- Keep each single run under ~2 minutes; if a sim is slow, use fewer reseeds (min 10) and say so.

## Per claim, classify into exactly one
| category | meaning |
|---|---|
| NOT_STOCHASTIC | the stated number comes from deterministic code, a fixture, arithmetic, a selftest, a document audit, or randomness that cannot affect it (e.g. hash-seeded embeddings used only as labels) |
| OUT_OF_SCOPE_DECLARED | ILLUSTRATIVE / sketch / explicitly declared not a result |
| MULTI_RUN | the claim already aggregates ≥2 seeds/draws (record K and how: "30 seeds", "1000 null draws", "40 runs") |
| SINGLE_RUN_SELF_FLAGGED | rests on one draw AND the repo says so near the claim (quote it) |
| SINGLE_RUN_UNFLAGGED | rests on one draw and nothing near it says so |
| UNRESOLVED | can't tell what produced the number (say what's missing) |

Only list NOT_STOCHASTIC / OUT_OF_SCOPE claims as COUNTS per folder, not row by row. List every MULTI_RUN,
SINGLE_RUN_* and UNRESOLVED row individually.

## For every SINGLE_RUN_* claim: run it
1. Reproduce the stated number at the original seed (REPRODUCED / NOT_REPRODUCED(got X) / NOT_RUNNABLE(reason)).
2. Re-run at K=20 other seeds (10 if slow). Changing the seed may mean a CLI flag, an env var, or editing the
   seed constant IN YOUR COPY ONLY (say which line).
3. Report: values across seeds (min / median / max), and how many of K satisfy the claim as worded.
4. Verdict: HOLDS (K/K satisfy) · DIRECTION_HOLDS_MAGNITUDE_VARIES (claim's direction/sign/ordering holds K/K but a
   stated magnitude doesn't) · FAILS_IN_SOME (k/K, k<K) · NOT_RUNNABLE(reason).
Record the exact commands so a second person can rerun.

## Output
Write JSON Lines to the output path you're given, one object per listed claim:
{"folder","claim_id","claim_short"(<=200 chars, quote key words),"evidence":"file:line","category",
 "k_runs"(for MULTI_RUN),"self_flag_quote","reproduced","reseeds":K,"satisfied":k,"values":{"min","median","max","orig"},
 "verdict","commands":[...],"notes"}
plus one object per folder: {"folder","summary":true,"claims_total","not_stochastic","out_of_scope","multi_run",
 "single_self_flagged","single_unflagged","unresolved","notes"}.
Folders without a claim table: treat numeric findings stated in README / RESULTS / FINDINGS files as claims
(claim_id = "file:line").

Then reply with a SHORT summary (<=250 words): per folder counts, and every SINGLE_RUN_* row with its verdict.
Do not editorialize about the repo's quality; report measurements.
