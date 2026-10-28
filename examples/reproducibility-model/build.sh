#!/usr/bin/env bash
# Rebuild assessment.json and report.md for this example from the CLI. CC0.
# Every value below came from https://arxiv.org/html/2602.15697v1 (read 2026-10-28)
# or from recompute.py in this folder (R1..R8). Run from the repository root:
#     bash examples/reproducibility-model/build.sh
set -eu
D=examples/reproducibility-model
F=$D/assessment.json
U=https://arxiv.org/html/2602.15697v1
A="python3 assess.py"
rm -f "$F"

$A init --file $F --title "Almudevar & Almudevar (2026): Reproducibility and Statistical Methodology" \
  --type THEORETICAL \
  --citation "arXiv:2602.15697v1 [stat.AP], submitted 2026-02-17, $U" \
  --materials "arXiv HTML rendering read through a fetch tool: abstract, section list, Tables 1 and 4, and quoted passages of Sections 2.1-2.2, 3.5, 3.6, 5. PDF not downloadable here (shell egress 403). Per-study OSC p-values and replication sample sizes behind the type II error figure not in hand. Cited sources (Nosek 2015, Klein 2014, Camerer 2016) not read." \
  --context "Whether to read the Open Science Collaboration's 36% replication rate (Nosek et al. 2015) as an estimate of how many published psychology findings are true, or as largely an artifact of how the replications were powered. Assessor-chosen paper; no decision owner named."

# ---- ordinary design checks (THEORETICAL record; run anyway because the paper re-analyses data)
$A design --file $F --check selection --state CHECKED --source "$U" \
  --finding "The prevalence used for OSC (pi = 0.25) is labelled 'consistent with ML-RP' (Table 1); Klein et al. 2014 studied a hand-picked set of effects. Selection of that set is not discussed as a reason it may differ from OSC's sample."
$A design --file $F --check measurement_validity --state CHECKED --source "$U" \
  --finding "The model treats 'replicated' as a significant same-direction replication (35/97). OSC also reported CI containment (47%) and subjective success (39%) (Introduction); the model addresses only the significance criterion."
$A design --file $F --check uncertainty --state CHECKED --source "$U" \
  --finding "Intervals are given for observed rates (35/97; 11/18, recomputed R4). No interval is given for the mean type II error 0.468 or for pi; the predicted rates in Section 3.5 are point values."
$A design --file $F --check multiplicity --state CHECKED --source "$U" \
  --finding "Two subsets (main effects, interactions) are fitted with two separately chosen prevalences (0.25, 0.05; Section 3.5). One free parameter per observed rate."
$A design --file $F --check missing_data --state CHECKED --source "$U" \
  --finding "Type II error computed on N = 93 of 97 after bounding effect estimates below by 0 (Section 3.5); 'a number of P-values were given as 0' (Section 3.5, stated limitation). 11 studies outside the main-effect and interaction rows (4/11 replicated, R2) are not discussed."
$A design --file $F --check confounding --state CHECKED --source "$U" \
  --finding "The main-effect vs interaction split (23/49 vs 8/37, Fisher p 0.0228, R3) is attributed to prevalence. Whether effect type covaries with sub-field or original sample size is not examined in the passages read."
$A design --file $F --check preregistration --state NOT_APPLICABLE --source "$U" \
  --finding "Model and re-analysis paper; no preregistration stated or expected."

# ---- claims
$A claim --file $F --id C1 --label DERIVED --support PARTIALLY_SUPPORTED --grade IMPOSED \
  --text "We show that the OSC methodology induces a bias that is able by itself to explain the discrepancy between the OSC estimates of reproducibility and other more optimistic estimates made by similar studies." \
  --evidence "Abstract; mechanism Sections 3.3-3.5; fit Table 4 and Section 3.5" \
  --measurand "observed replication rate PPV_obs, predicted from prevalence pi and replication type II error beta*" \
  --instrument "eq. 3 with pi = 0.25 (main) and 0.05 (interactions) and mean beta* 0.468" \
  --range "OSC-RP 97 studies; ML-RP 13; Camerer 18" \
  --falsifiers "An independent estimate of pi for the OSC originals inside 0.018-0.048 (fits OSC with OSC's reported beta* 0.08, R6) and outside 0.043-0.255 (the range the corrected beta* needs). A high-power re-replication of the same OSC items whose success rate stays near 0.36. Neither run in the paper." \
  --source "$U"
$A claim --file $F --id C2 --label DERIVED --support UNDETERMINED --grade UNDECLARED \
  --text "the mean type II error is now 0.468, considerably higher than the average 0.08 reported by the OSC-RP" \
  --evidence "Section 3.5" \
  --measurand "mean conditional type II error of the OSC replications, with effect size re-estimated by MLE from each original p-value" \
  --instrument "beta_c(eta, t, alpha, beta), t = z_alpha/2, eta replaced by its MLE bounded below by 0; N = 93 of 97" \
  --falsifiers "Recomputing from OSC's per-study p-values and replication sample sizes gives a mean near 0.08. Not recomputed here: inputs not in hand." \
  --source "$U"
$A claim --file $F --id C3 --label OBSERVED --support SUPPORTED --grade MEASURED_PRESENT \
  --text "For main effects and interactions respectively, the values of PPV_obs were 23/49 = 46.9% and 8/37 = 21.6% (P = 0.023, Fisher's exact test)" \
  --evidence "Section 3.5; Table 4" \
  --measurand "count of significant same-direction replications by original effect type" \
  --instrument "OSC-RP data as tabulated in Table 4" \
  --falsifiers "Table 4 counts differ from the OSC data file (not checked: OSC file not read). Arithmetic recomputed: totals 35/97 and Fisher p 0.0228 (R2, R3)." \
  --source "$U"
$A claim --file $F --id C4 --label PROPOSED --support UNTESTED --grade IMPOSED \
  --text "Suppose, in fact, pi=0.25 (Case 3 of Table 1) [...] Suppose we next conjecture an effect prevalence of pi = 0.05 (Case 4 of Table 1)." \
  --evidence "Section 3.5" \
  --measurand "effect prevalence pi among the original OSC hypotheses" \
  --instrument "none: stated as a supposition; pi = 0.25 borrowed from the ML-RP calibration, pi = 0.05 from 'secondary or exploratory analyses'" \
  --falsifiers "Any measured prevalence for the OSC original hypotheses. None exists in the paper." \
  --source "$U"
$A claim --file $F --id C5 --label DERIVED --support PARTIALLY_SUPPORTED --grade IMPOSED \
  --text "for the ML-RP the reported value PPV_obs = 11/13 = 84.6% is essentially a direct estimate of PPV, which is very close to the predicted value PPV = 0.857 given an effect prevalence of pi = 0.25." \
  --evidence "Section 3.6; Table 1 Case 3" \
  --measurand "ML-RP replication rate read as PPV" \
  --instrument "treats ML-RP replication error rates as about zero" \
  --falsifiers "ML-RP's own replication error rates are not near zero. The closeness is shared with the calibration: Table 1 labels pi = 0.25 'consistent with ML-RP' (R7)." \
  --source "$U"
$A claim --file $F --id C6 --label DERIVED --support SUPPORTED --grade UNDERPOWERED \
  --text "For a prevalence of pi=0.25 with PPV=0.857 (Case 3 of Table 1), the predicted observed reproducibility rate is PPV_obs=0.486, and therefore is compatible with the observed rate." \
  --evidence "Section 3.6 (Camerer et al., 11/18; 95% Clopper-Pearson 0.357-0.827)" \
  --measurand "economics replication rate 11/18" \
  --instrument "eq. 3 with beta* 0.441" \
  --falsifiers "Observed rate outside 0.357-0.827. Holds (R4). The same interval also contains 0.796, the no-bias prediction (R8), so the comparison does not separate the readings." \
  --source "$U"
$A claim --file $F --id C7 --label DERIVED --support PARTIALLY_SUPPORTED --grade UNDECLARED \
  --text "Table 1 [...] a replication protocol with errors alpha* = alpha = 0.05 and beta* = beta = 0.1" \
  --evidence "Section 2.2, Table 1" \
  --measurand "illustrative PPV and PPV_obs for four prevalences" \
  --instrument "eqs. 2 and 3" \
  --falsifiers "Recomputation from the caption: PPV column reproduces; PPV_obs reproduces for row 1, within 0.003 for row 3, and rows 2 and 4 match beta* = 0.15 instead (R1). Table 1 is not an input to the Section 3.5 fit." \
  --source "$U"
$A claim --file $F --id C8 --label PROPOSED --support UNTESTED --grade UNDECLARED \
  --text "We argue, for both scientific and ethical reasons, that a considered balance of false positive and false negative rates is preferable to a single-minded concentration on false positive rates alone." \
  --evidence "Abstract; Sections 4.2-4.4" \
  --measurand "none: a normative position" \
  --falsifiers "Not an empirical claim; carried as an argument." \
  --source "$U"

# ---- input averages (Card 02 frozen-state check)
$A average --file $F --id A1 --text "effect prevalence pi, main effects" --value 0.25 \
  --population "hypotheses tested by the OSC-RP main-effect originals" \
  --window UNDECLARED --stationarity UNDECLARED \
  --estimated-from "ML-RP effects (Klein et al. 2014): Table 1 labels pi = 0.25 'consistent with ML-RP'" \
  --fitted-to "ML-RP 11/13 read as PPV (implies pi 0.234, recompute R7)" \
  --claim C1 --claim C4 --claim C5 --source "$U"
$A average --file $F --id A2 --text "effect prevalence pi, interactions" --value 0.05 \
  --population "hypotheses tested by the OSC-RP interaction originals" \
  --window UNDECLARED --stationarity UNDECLARED --split-of A1 \
  --claim C1 --claim C4 --source "$U"
$A average --file $F --id A3 --text "mean type II error of the OSC-RP replications" --value 0.468 \
  --population "OSC-RP main-effect and interaction subsets, each predicted separately (Section 3.5)" \
  --window UNDECLARED --stationarity UNDECLARED \
  --estimated-from "93 of 97 OSC-RP replications, all effect types pooled" \
  --claim C1 --claim C2 --source "$U"

# ---- card runs
$A tool --file $F --id T1 --card 00 --state RUN --source "$U" \
  --output "Type THEORETICAL (model, derivation, review). Defaults 00/01/04/06. Overrides: 02, because the fit rests on an imposed quantity (pi); 03, because the 'more optimistic' studies are used as agreement. Toolkit fit: no type covers a re-analysis of other studies' published data; THEORETICAL plus overrides used."
$A tool --file $F --id T2 --card 01 --state RUN --source "$U" \
  --output "8 claims, verbatim. C1 in conditional form: IF pi for the OSC originals is about 0.25 (0.05 for interactions) AND mean beta* is about 0.468, THEN 35/97 is the expected rate. Both antecedents carry the result; neither is observed."
$A tool --file $F --id T3 --card 02 --state RUN --source "$U" \
  --output "pi graded IMPOSED: 'Suppose' and 'conjecture' (Section 3.5), with a reason given for each value but no measurement. beta* 0.468 is derived from inputs not in hand (per-study p-values, replication n), so UNDECLARED here rather than checked. Toolkit fit: the measurement grades have no value for 'computed, not recomputed'; UNDECLARED was the nearest."
$A tool --file $F --id T4 --card 03 --state RUN --source "$U" \
  --output "ML-RP vs model: SHARED_UPSTREAM. pi = 0.25 is set from ML-RP (Table 1 label; 11/13 implies pi 0.234, R7), then ML-RP's closeness to 0.857 is reported in Section 3.6. Camerer vs model: independent data, but at n = 18 compatible with both the bias reading (0.486) and the no-bias reading (0.796), R8. Toolkit fit: 'calibration reused as confirmation' has no route of its own; SHARED_UPSTREAM fits loosely."
$A tool --file $F --id T5 --card 04 --state RUN --source "$U" \
  --output "Open branches for OSC's 35/97: (a) protocol bias, inflated original effects leading to underpowered replications (paper); (b) low prevalence, pi about 0.03 with OSC's reported beta*, no bias needed (R6); (c) a mixture of (a) and (b); (d) other moderators of replication (Gilbert et al. 2016 is cited, not modelled). The observed rate alone does not separate (a) from (b). Cheapest discriminator: re-replicate a sample of the same OSC items powered on bias-corrected effect sizes. Under (a) success rises toward PPV; under (b) it stays low. Not run in the paper."
$A tool --file $F --id T6 --card 05 --state RUN --source "$U" \
  --output "Term frame: 'reproducibility' in OSC carries several indicators (significance 36%, CI containment 47%, subjective 39%; Introduction). The paper's model is about significance only. 'Explain the discrepancy' applies to that one indicator. Observer-position and lower-layer checks: NOT_APPLICABLE to this material."
$A tool --file $F --id T7 --card 06 --state RUN --source "$U" \
  --output "Target: is OSC's low rate mostly an artifact of the replication protocol? Rendering: 'able by itself to explain'. That shows sufficiency under an imposed pi, not that the artifact is the explanation. Arithmetic recomputed (recompute.py R1-R8): the predictions in Sections 3.5 and 3.6 reproduce exactly."

# ---- decisions
$A decide --file $F --id D1 --state UNRESOLVED \
  --text "Read OSC's 36% as an estimate of the share of published psychology findings that would replicate under adequate power? If pi is near 0.25, this paper says no (the protocol depresses the rate). If pi is near 0.03, the rate stands without any bias. pi is not measured."
$A decide --file $F --id D2 --state UNRESOLVED \
  --text "Treat this paper as having shown that the OSC rate is a methodological artifact? It shows that the artifact is sufficient under assumed prevalences, and that the same arithmetic reproduces OSC and Camerer. It does not separate that from a low-prevalence reading (R6, R8)."
$A decide --file $F --id D3 --state DETECTED \
  --text "Adopt the power-analysis point (do not power replications on original effect estimates, which overestimate effects after selection on significance; Sections 3.3-3.4) when planning replications. This does not depend on the value of pi."

$A check --file $F
$A report --file $F > $D/report.md
