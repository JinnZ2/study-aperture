#!/usr/bin/env bash
# Rebuild assessment.json and report.md for this specimen from the CLI. CC0, co-authored.
# Every value below is CARRIED: Grok's assessment of arXiv 2611.16833 (Grok chose the
# paper), relayed by Claude on 2026-11-15. Nothing here was read by the builder of this
# record. Run from the repository root:
#     bash examples/arxiv-2611.16833-grok-specimen/build.sh
set -eu
D=examples/arxiv-2611.16833-grok-specimen
F=$D/assessment.json
U=https://arxiv.org/abs/2611.16833
A="python3 assess.py"
rm -f "$F"

$A init --file $F --title "Chen, He, Zhou, Bu (PKU, submitted 2026-11-12): resistance to AI-assisted writing among first authors (arXiv 2611.16833)" \
  --type EMPIRICAL \
  --citation "arXiv:2611.16833, submitted 2026-11-12, $U" \
  --materials "CARRIED: Grok's assessment, relayed by Claude 2026-11-15. Grok's stated reads: the paper's abstract, introduction and methods; a CASRAI writeup (2026-11-15); an alphaXiv summary. Results and limitations sections: read depth not stated. Data as relayed: OpenAlex snapshot 2026-09-23; 71,133 first authors; 565,602 publications, 2023 to Sep 2026." \
  --context "Specimen for the section-level read ceiling (Card 07 4b): results claims carried from a press writeup and a snippet, beside a methods claim read in full. Not an assessment for a decision."

# ---- sources (depths as Grok declared them)
$A source --file $F --id S1 --location "$U" --depth FULL_TEXT \
  --detail "abstract, introduction, methods (as declared in Grok's assessment)" \
  --sections "abstract,introduction,methods" \
  --section-depth results=UNDECLARED --section-depth limitations=UNDECLARED \
  --basis "Grok's assessment, relayed 2026-11-15 (CARRIED)"
$A source --file $F --id S2 --location "CASRAI writeup of arXiv 2611.16833, 2026-11-15 (URL not relayed)" \
  --depth PRESS_RELEASE --basis "Grok's assessment, relayed 2026-11-15 (CARRIED)"
$A source --file $F --id S3 --location "alphaXiv summary of arXiv 2611.16833 (URL not relayed)" \
  --depth SNIPPET --basis "Grok's assessment, relayed 2026-11-15 (CARRIED)"

# ---- ordinary design checks (only what the relay carries)
$A design --file $F --check measurement_validity --state CHECKED --source "$U" --error-type E4_UNCHECKED_OBSERVER \
  --finding "AI use is measured by an alpha classifier trained on GPT-3.5 rewrites; reading its output as AI use is a construct leap (relayed premise)."
for k in confounding selection uncertainty multiplicity missing_data preregistration; do
  $A design --file $F --check $k --state NOT_CHECKED --finding "not in the relayed assessment"
done

# ---- claims (paraphrased in the relay, not verbatim)
$A claim --file $F --id C1 --label DERIVED --support UNTESTED \
  --text "Resistance = predicted minus observed share of a first author's abstracts with alpha >= 0.1." \
  --evidence "Methods (as relayed)" \
  --measurand "resistance to AI-assisted writing, per first author" \
  --instrument "alpha classifier (GPT-3.5 rewrites); threshold 0.1" \
  --rests-on S1:methods
$A claim --file $F --id C2 --label OBSERVED --support UNTESTED --grade MEASURED_PRESENT \
  --text "Early resistance predicts later resistance; the positive-resistance share falls from 52.9% to 37.2%." \
  --evidence "Results (carried through S2/S3)" --rests-on S2 --rests-on S3
$A claim --file $F --id C3 --label OBSERVED --support UNTESTED --grade MEASURED_PRESENT \
  --text "Environment predicts resistance better than individual traits; overall predictive power is low." \
  --evidence "Results (carried through S2/S3)" --rests-on S2 --rests-on S3
$A claim --file $F --id C4 --label OBSERVED --support UNTESTED --grade MEASURED_PRESENT \
  --text "A non-positive collaborator is followed by lower later resistance." \
  --evidence "Results (carried through S2/S3)" --rests-on S2 --rests-on S3
$A claim --file $F --id C5 --label OBSERVED --support UNTESTED --grade MEASURED_PRESENT \
  --text "The positive-resistance group cites older work and fewer subfields; their reuse gap widens from 3.24 to 7.95 percentage points, visible before 2023." \
  --evidence "Results (carried through S2/S3)" --rests-on S2 --rests-on S3

# ---- independence (Card 03), as relayed
$A tool --file $F --id T1 --card 03 --state RUN --source "$U" --error-type E3_DEFAULTED_SLOT \
  --output "Threshold alpha >= 0.1 comes from the same group's earlier work (not an independent calibration). The robustness check with Qwen is a same-family model, not an independent detector. Relayed premises; not checked here."

$A check --file $F
$A report --file $F > $D/report.md
