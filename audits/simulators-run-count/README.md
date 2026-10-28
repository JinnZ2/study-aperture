# Audit: single-draw claims in JinnZ2/Simulators (ADDENDUM item C2)

Status: completed bounded audit, run 2026-10-28 against Simulators commit `0655e8be2d090030f8e568a8b68b36afdc98fbec`, which was read-only throughout (all runs in scratch copies). It measures one thing: whether stated results rest on a single random draw, and whether they survive re-drawing. It does **not** establish whether any claim is true, does not test replication across independent studies, and does not cover the 173 folders outside the candidate set (138 with no random draws, 14 with no code, 19 whose random code all carries multi-run machinery, plus `play-sims` and `tests` excluded below).

## The question

```
within-run n     how many random draws a stated number rests on      ← this audit
replication n    how many independent studies agree                  ← not this audit
                 (every new study starts at 1; that is a state, not a defect)
```

A result resting on one seed can change when the seed changes. Simulations can raise this n cheaply, so it is worth knowing where it is 1.

## Funnel

```
216 folders (legacy/ and archive/ excluded)
 ├─ 138  no random draws at all                         seed count does not apply
 ├─  14  no code
 ├─  19  every random file carries multi-run machinery
 └─  45  candidates ─┬─ 2 excluded: play-sims (self-declared sketches, "audit convention does not apply"), tests (harness)
                     └─ 43 audited, claim by claim

1,054 claims in the 43 audited folders
   852  not random (fixtures, arithmetic, deterministic integration, document checks)   81%
    32  out of scope (ILLUSTRATIVE, sketches)
    79  already multi-run (2 to 20,000 draws)
     4  unresolved (generating code not shipped)
    87  rest on a single draw   (16 flagged by the repo itself, 71 not)
          │
          │  re-run at the original seed, then at 20 other seeds (10 for the slowest audit)
          ▼
    32  HOLDS at every seed
    35  DIRECTION HOLDS, stated magnitude moves with the seed
    12  FAIL AT SOME SEEDS (verified, below)
     4  not random once scoped correctly (the claim is about one fixed world or fixture)
     3  already flagged by a neighbouring row or revision
     1  NOT REPRODUCED at its own original seed
```

Totals regenerate from the data with `python3 consolidate.py`.

## Verified: claims that fail at some seeds (12)

Every row below was re-run by a second, independent pass that checked the randomness varied was within the claim's scope and the pass/fail test matched the sentence.

| Folder · claim | Says | Satisfied | What moves |
|---|---|---|---|
| fragility-cascade · CGT-4 v2 (repo-flagged single seed) | accuracy slope "robustly negative" | **6/20** independent seeds (14/20 on overlapping seeds) | slope −0.0061 … +0.0089 |
| anchor-interval · ANC_003 | "FP ≥ TP at every threshold" | **6–7/20** | the weaker "no discrimination" holds 20/20 |
| sim-span · RESULTS.md:36 | mono floor ≥ 10 h | **10/20** | floors 9.79–10.25 straddle the sentence's own "below 10" |
| aperiodic-order-sim-stack · AOS_003 | residual ≈ 4× the 0.021 baseline | **13/20** | residual 0.004–0.116; the original seed itself is 3.91× |
| fragility-cascade · CGT-1 (repo-flagged) | decoupled accuracy < 0.5, coupled gap < 0.2 | 16–18/20 | original accuracy 0.493 sits next to the 0.5 line |
| instrument-bias-sims · IBS_011 | content correlation "under 0.2 at every mix" | 16/20 | peaks 0.200–0.229 |
| proxy-investigation-lab · README.md:49 | gaming "inflates top-decile variance" | 17/20 | gamed vs ungamed median 0.092 vs 0.083 (see corrections) |
| sim-span · RESULTS.md:91 | lowest vertex at mixture p 0.5–0.75 | 17/20 | |
| transmission-cascade · TC_005 | type coefficient under the 0.10 floor on the null world | 17/20 | crosses it ~13% of the time (1746/2000) |
| instrument-bias-sims · IBS_001 | > 95% null + product ordering | 19/20 | the failing draw has zero ESCALATE events (untestable, not reversed) |
| battery-offgas-prearm · BOP_010 | a 30 s step does not fire | 19/20 | fires on ~2.7% of noise draws (973/1000 pass) |
| sim-span · SPAN_003 | flat produces fewer U's than frag_driven | 19/20 | the original count of 4 is the lowest of 21 draws |

## Not reproduced at its own seed (1)

**climate-modeling · `audits/cascade_speed.py:5`**, the flagship audit's docstring: the smooth model *"consistently underestimates how fast collapse arrives."* The committed `samples/audit_report.json` shows `collapse_time_true_h` 240.0 = `collapse_time_audited_h` 240.0, which is the window end, so neither model crosses the collapse marker. The "true" system's biomass ends at **754,402** against 480 for the audited one: it runs away upward. The FAIL verdict fires on `rmse 307017.87 > 15`, i.e. on that divergence, not on collapse timing. *(Checked directly from the committed sample.)*

## Corrections made during verification

The first pass reported 25 claims failing at some seeds. **13 of those 25 did not survive verification.** The errors fall into recurring classes, and they are a result in their own right: a reseeding audit can generate false failures as easily as it finds real ones.

| Error class | Rows | Example |
|---|---|---|
| Varied randomness the claim doesn't quantify over | M1a, CDC_006, RCL_008, RDD_006, TC_006, floor-resilience:106 | M1a is about "this dataset"; re-drawing the dataset made hilbert win 1/20. Re-drawing only the observers (the claim's actual scope): **hilbert wins 20/20** |
| Criterion didn't match the wording | proxy:49, RC_013, RCL_008, RESULTS.md:26, RESULTS.md:91 | "inflates" was tested as ratio > 1; the claim needs gamed vs ungamed, which gives 17/20 |
| Already addressed in a nearby row | D1, CGT-3 v1, RC_002 | D1 cites seed-3 numbers; D1″ two rows down: *"Neither direction survives the seed sweep."* |
| Seeds not independent | CGT-4 v2 (kept as a fail, rate corrected) | consecutive base seeds share 11 of 12 generation seeds (`SEED+g`); independent seeds give 6/20, not 14/20 |

The 67 HOLDS / DIRECTION-HOLDS rows were **not** independently re-verified. The error classes found all push toward *false failures*, so those verdicts are less exposed, but where the first pass re-drew out-of-scope randomness their magnitude ranges may be wider than the claim's true spread.

## Other findings

Checked directly:
- **fragility-cascade `collapse_predictor.py:66`**: `random.seed(123)` inside `phi_spiral_transition`, called on every predict. Claims C12, C13, C14 and C16, described as 50-trial sweeps, rest on 1–2 distinct draws. Verdicts don't change across 20 reseeds.
- **aperiodic-order-sim-stack `finite_n_control.py:254-256`**: prints *"still well above the 0.021 matched-N baseline"* whenever budget < gap, without comparing the residual to the baseline. At seed 16 the residual is 0.004 and the sentence still prints.
- **cooperative-substrate-proof `selftest.py:40`** crashes: `AttributeError: module 'scope' has no attribute 'code_case'` (`scope.py` defines `code`). `KNOWN_RED.md:940` records this selftest at 82/0, so by the repo's protocol this is a **new red**.

Reported by the audit passes (rerun commands in `data/`):
- **relational**: the figures' Cartesian-vs-Relational gap is attributed to seed variance in `notes.md:708`, but the shipped demo gives 0.36 / 0.52 at all 20 seeds and 3 unseeded runs. The scripts that drew the figures aren't shipped (UNRESOLVED).
- **model-ecology AC row**: mixes two runs. N_eff 2.48 is seed 3 alone; 6.29× is the 12-seed mean (seed 3 alone gives 6.05×). The 12-seed sweep script isn't shipped.
- **residual-direction RDD_005**: the claim holds, but a false GROWING reading on a STABLE fixture occurs on 385/2000 draws (19%).
- **anchor-interval `corpus_loop.py:309`** prints "on this run"; no claim-table row carries that qualifier.
- **sim-span**: the headline grid (4/124/63 of 360) is one run per combination at seed 1000; the "40 seeds" in the RESULTS.md header applies to the U-rate figures, not the grid.
- **emergence-stability-simulator**: the sample claim table holds 22 claims; its README says 19.

## Files

| Path | Contents |
|---|---|
| `triage.py`, `data/triage.json` | static scan of all 216 folders (reads text only) |
| `RUBRIC.md` | the classification and rerun protocol every pass followed |
| `data/first_pass.jsonl` | 7 parallel passes: 169 listed claims + 43 folder summaries, each with evidence `file:line` and rerun commands |
| `data/verification.jsonl` | 21 failing rows re-checked by two independent passes |
| `data/lead_verification.jsonl` | 4 rows checked directly (M1a, D1, proxy:49, cascade_speed) |
| `consolidate.py` → `data/final.json` | final verdict per single-draw claim; revised verdicts mapped in a visible table |
| `harness/` | rerun scripts per pass (`B1`–`B7` first pass, `V1`/`V2` verification, `lead`) |

## Reproduce

```sh
python3 consolidate.py              # totals
python3 consolidate.py --markdown   # per-claim table (87 rows)
```

Rerunning a measurement: clone Simulators at the commit above into a scratch folder, then run the command recorded in that row's `commands` field (harness scripts take a seed or monkeypatch one; no Simulators file is edited). Stdlib plus numpy/scipy, as the Simulators folders themselves require.

## Upstream

Simulators' `READ_ME_THIS_WAY.md` asks for dated notes beside the original rather than overwrites, and `AGENTS.md` asks that failures be reported verbatim. Whether and how these findings go back into Simulators is the owner's call (ADDENDUM C2a).
