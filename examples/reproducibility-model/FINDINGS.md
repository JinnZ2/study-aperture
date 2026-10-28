# Findings: Almudevar & Almudevar (2026), "Reproducibility and Statistical Methodology"

Status: a bounded run of study-aperture on one paper, 2026-10-28. Recorded: the record (`assessment.json`, built by `build.sh`), the generated `report.md`, and a stdlib recomputation of the paper's arithmetic (`recompute.py`, pinned by `python3 recompute.py selftest`). **Not established:** whether the paper's conclusion is right, the type II error figure (inputs not in hand), and anything in the cited studies, none of which were read. The assessor chose the paper, so this is not the independent run ADDENDUM C1 asks for.

Source: arXiv:2602.15697v1, HTML rendering at https://arxiv.org/html/2602.15697v1, read through a fetch tool. The PDF could not be downloaded here (shell egress 403). Section, table and equation numbers below refer to that rendering.

## The paper's argument, as a shape

```
OSC 2015: 97 significant originals ──► 35 significant replications (36%)
                                         ▲
paper:  original effect sizes are inflated by selection on significance (3.3-3.4)
        ──► replications powered on them are underpowered
        ──► mean type II error 0.468, not OSC's 0.08          (3.5, C2)
        + prevalence pi = 0.25 main effects, 0.05 interactions (3.5, C4: "Suppose", "conjecture")
        ──► predicted 0.463 / 0.284  vs observed 0.469 / 0.216 (3.5)
```

## What recomputes (recompute.py)

| # | Check | Result |
|---|---|---|
| R1 | Table 1 from its caption (alpha* = alpha = 0.05, beta* = beta = 0.1) | PPV column reproduces. PPV_obs: row 1 matches, row 3 within 0.003, rows 2 and 4 match beta* = 0.15 instead. Table 1 is not an input to the 3.5 fit. |
| R2 | Table 4 totals | 35/97, matches. The 11 studies outside the main-effect and interaction rows (4/11) are not discussed. |
| R3 | Fisher exact, 23/49 vs 8/37 | p = 0.0228 (paper: 0.023) |
| R4 | Clopper-Pearson 35/97, 11/18 | (0.266, 0.465) and (0.357, 0.827), both as stated in 3.5 and 3.6 |
| R5 | Predictions from eq. 3 | 0.463, 0.284, 0.486: all exactly as stated |
| R6 | Which pi reproduces 35/97 | with the paper's beta* 0.468: pi 0.043-0.255 (point 0.092); with OSC's reported beta* 0.08: pi 0.018-0.048 (point 0.030) |
| R7 | pi implied by ML-RP 11/13 read as PPV | 0.234; Table 1 labels pi = 0.25 "consistent with ML-RP" |
| R8 | Camerer 11/18 under no bias (beta* 0.08, pi 0.25) | predicted 0.796; also inside (0.357, 0.827) |

The paper's own arithmetic holds. Where it is off (R1) the table is illustrative and nothing downstream rests on it.

## What the record keeps open

**1. The fit rests on an imposed prevalence (C1, C4; Card 02).** pi is introduced with "Suppose" and "conjecture" (3.5) and is not measured. R6 shows the observed 35/97 is reproduced:
- by the paper's reading (bias, beta* 0.468) with pi anywhere from 0.043 to 0.255;
- by a no-bias reading (OSC's beta* 0.08) with pi from 0.018 to 0.048.

So the observed rate does not by itself choose between "the protocol depressed the rate" and "few of the original hypotheses were true". The paper shows the bias is *sufficient* under its pi. The abstract's "able by itself to explain" is that sufficiency claim. The record does not read it as shown that the bias *is* the explanation.

In the terms of Card 02's frozen-average check: pi stands for a distribution over fields, eras and designs, under a selection process that keeps acting. It enters the model as one constant, with no population, window or stationarity stated. When one value did not fit the interactions, a second was introduced (0.05), which is the distribution reappearing as a second free value.

The record carries these as input averages (`assess.py average`), so they print in the report's incompleteness block: A1 (pi 0.25: estimated from ML-RP, used for OSC, fitted to ML-RP), A2 (pi 0.05: split from A1), A3 (mean type II error 0.468: estimated over all 93 replications pooled, used for each subset separately). None states a window or stationarity.

**2. One confirmation is the calibration (C5; Card 03).** pi = 0.25 is chosen as "consistent with ML-RP" (Table 1). Section 3.6 then reports ML-RP's 84.6% as very close to the predicted 0.857. That closeness was set when pi was chosen (R7), so it is not a separate test. Route: SHARED_UPSTREAM.

**3. The independent check does not discriminate (C6; Cards 03, 04).** Camerer et al. are independent data. At n = 18 their rate (11/18) is compatible with the bias prediction (0.486) and with the no-bias prediction (0.796) (R8). The claim "compatible" holds; the comparison separates nothing. Graded UNDERPOWERED.

**4. Two prevalences for two subsets (design: multiplicity).** Main effects get pi 0.25, interactions 0.05. With one free value per observed rate, the close fit in 3.5 is expected whatever the mechanism.

**5. The central input was not recomputed (C2).** The mean type II error 0.468 comes from re-estimating each original effect from its p-value (N = 93 of 97; some p-values reported as 0, a limitation the paper states). The per-study inputs were not in hand, so C2 stays UNDETERMINED.

## Open branches (Card 04)

```
OSC 35/97
 ├─ (a) protocol bias: inflated originals → underpowered replications     paper's reading
 ├─ (b) low prevalence: pi ≈ 0.03, OSC's power roughly right               fits equally (R6)
 ├─ (c) mixture of (a) and (b)
 └─ (d) other replication moderators (Gilbert et al. 2016, cited, not modelled)

cheapest discriminator: re-replicate a sample of the same OSC items, powered on
bias-corrected effect sizes.  (a) → success rises toward PPV.  (b) → stays low.
Not run in the paper.
```

What holds whatever the value of pi: powering a replication on an effect estimate that was selected for significance overestimates power (3.3-3.4). Decision D3 records that point separately.

## What this run says about the toolkit

This was also a test of study-aperture itself. Places where it fit badly, recorded as they happened:

| # | Where | What happened | Bears on |
|---|---|---|---|
| K1 | Card 00 types | No type for a re-analysis of other studies' published data. Used THEORETICAL plus overrides for Cards 02 and 03. | A3 |
| K2 | Measurement grades | No grade for "computed by the paper, not recomputed here" (C2). Used UNDECLARED, which says less than is known. | A3 |
| K3 | Card 03 routes | No route for "a calibration reused as a confirmation" (C5). SHARED_UPSTREAM fits loosely. | A3 |
| K4 | `report` incompleteness block | Lists UNDETERMINED claims and open decisions. It does not list IMPOSED grades (C1, C4, C5) or UNTESTED claims (C4, C8), although the central claim rests on an IMPOSED input. A reader of the first block alone misses the main open point. Partly closed by the input-average check (ADDENDUM B6): the imposed pi now prints in the block as A1/A2. IMPOSED claim grades in general still do not (ADDENDUM B5). | ADDENDUM B5, B6 |
| K5 | Material | The publisher's PDF was blocked; the HTML rendering was enough for this paper because the tables are HTML. A paper with image-only tables would have stopped at the abstract. | none |

K4 is the one that matters most: the incompleteness block is the report's headline by design, and here it under-reports.

## Reproduce

```sh
python3 examples/reproducibility-model/recompute.py            # R1-R8
python3 examples/reproducibility-model/recompute.py selftest   # pinned values
bash examples/reproducibility-model/build.sh                   # rebuild assessment.json + report.md
```
