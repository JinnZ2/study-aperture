#!/usr/bin/env bash
# Rebuild assessment.json and report.md for this example from the CLI. CC0.
# Material read 2026-10-28: Scientific Frontline coverage (U), a Phys.org
# screenshot supplied by the user, Oceanographic coverage, and Spira et al. 2026
# (V, open-access PDF, related study). The paper (doi:10.1038/s41558-026-02758-y)
# and the University of Melbourne release were not reachable (client errors).
#     bash examples/aaiw-reversal-2026/build.sh
set -eu
D=examples/aaiw-reversal-2026
F=$D/assessment.json
U=https://www.sflorg.com/2026/10/oce10282601.html
V=https://eprints.soton.ac.uk/511866/1/s41558-026-02601-4.pdf
E=https://github.com/JinnZ2/earth-systems-physics/blob/aaiw-reversal-2026/aaiw_reversal_2026.py
A="python3 assess.py"
rm -f "$F"

$A init --file $F --title "Mishra, Gayen & Naveira Garabato (2026): Reversal of Antarctic Intermediate Water trends triggered by sea ice decline" \
  --type EMPIRICAL \
  --citation "Nature Climate Change 2026, doi:10.1038/s41558-026-02758-y; coverage $U" \
  --materials "Press coverage only (Scientific Frontline, Oceanographic, Phys.org screenshot). Paper, figures, salinity/density magnitudes, depths and methods NOT read. Related: Spira et al. 2026 (Nature Climate Change, doi:10.1038/s41558-026-02601-4), open-access PDF read through a fetch tool. Unit conversions computed in earth-systems-physics aaiw_reversal_2026.py." \
  --context "User-chosen study, routed to Thwaites and Earth-system modelling: whether a Southern Ocean freshwater budget built around ice-shelf melt (the CDW-AABW loop in earth-systems-physics, the Thwaites audit in CEED) needs the sea-ice meltwater term, and whether AAIW has changed state. No decision owner named."

$A design --file $F --check selection --state CHECKED --source "$U" \
  --finding "One water mass, 1995-2024, reversal window 2016-2024 (9 years). The coverage calls it the first direct observational evidence. Argo near-global coverage is a 2000s development, so the early part of the 1995-2015 baseline rests on sparser data (VERIFY in the paper)."
$A design --file $F --check measurement_validity --state CHECKED --source "$U" --error-type E1_DROPPED_VARIABLE \
  --finding "The meltwater comparison (about 3x then 2x the Amazon's annual flow) is a melt volume. Sea ice that forms and melts in place delivers no net freshwater over a year; whether the figure is gross seasonal melt or net delivery to the AAIW source region is not stated in the material read."
$A design --file $F --check confounding --state CHECKED --source "$V" --error-type E1_DROPPED_VARIABLE \
  --finding "The coverage names sea-ice decline as the trigger and does not mention ice-shelf (glacial) meltwater, which other work in the same period reports rising. Spira et al. 2026 attribute the 2015-16 sea-ice drop itself to wind-driven mixing over thinned Winter Water, so the 'trigger' is one link in a chain."
$A design --file $F --check uncertainty --state NOT_CHECKED --source "$U" \
  --finding "No uncertainties, magnitudes or depths in the material read."
$A design --file $F --check preregistration --state NOT_APPLICABLE --source "$U" \
  --finding "Observational analysis of a natural record."

$A claim --file $F --id C1 --label OBSERVED --support PARTIALLY_SUPPORTED --grade MEASURED_PRESENT \
  --text "has rapidly reversed its long-term trends in salinity and density" \
  --evidence "Coverage only; magnitudes and figures not read" \
  --measurand "AAIW salinity and density trends, 1995-2015 vs 2016-2024" \
  --instrument "Argo floats (~4,000), satellite and atmospheric datasets" \
  --range "1995-2024; post-reversal 9 years" \
  --falsifiers "The post-2016 trend lies within the spread of earlier 9-year windows of the same record; or the reversal is confined to the depth/region range where Argo coverage changed." \
  --source "$U"
$A claim --file $F --id C2 --label DERIVED --support UNDETERMINED --grade UNDECLARED \
  --text "Reversal of Antarctic Intermediate Water trends triggered by sea ice decline" \
  --evidence "Paper title; coverage: summer melt about 3x Amazon flow before 2016, about 2x after" \
  --measurand "attribution of the AAIW change to reduced sea-ice meltwater" \
  --instrument "not described in the material read" \
  --falsifiers "A freshwater budget for the AAIW source region that includes ice-shelf meltwater and net (not gross) sea-ice melt does not show a decrease of the needed size." \
  --source "$U"
$A claim --file $F --id C3 --label PROPOSED --support UNTESTED --grade UNDECLARED \
  --text "we may have underestimated the extent of deep-ocean warming and rising sea levels" \
  --evidence "Coverage: 'A weakened AAIW layer could push more excess heat deeper.' No figure given." \
  --measurand "deep-ocean heat uptake and sea-level contribution" \
  --falsifiers "A model run with the observed AAIW change shows no material change in deep heat uptake." \
  --source "$U"
$A claim --file $F --id C4 --label DERIVED --support PARTIALLY_SUPPORTED --grade UNDECLARED \
  --text "That transition took thousands of years, not two decades." \
  --evidence "Coverage quote (Gayen); the ~130 kyr ago transition" \
  --measurand "rate comparison: past AAIW state change vs present reversal" \
  --falsifiers "None stated. The two are different objects: a 9-year trend statistic and a completed state change." \
  --source "$U"

$A average --file $F --id A1 --text "summer sea-ice meltwater before 2016" --value "about 3x Amazon annual flow (about 19,800 km3/yr)" \
  --population "Antarctic summer sea-ice melt" --window "1995-2015" --stationarity UNASSESSED \
  --claim C2 --source "$U"
$A average --file $F --id A2 --text "Amazon annual flow (unit of comparison)" --value "about 6,600 km3/yr" \
  --population UNDECLARED --window UNDECLARED --stationarity UNDECLARED \
  --claim C2 --source "$U"

$A tool --file $F --id T1 --card 00 --state RUN --source "$U" \
  --output "Type EMPIRICAL (observational trend analysis plus attribution). Material is press coverage; method-level checks are NOT_CHECKED rather than passed."
$A tool --file $F --id T2 --card 01 --state RUN --source "$U" \
  --output "4 claims. Conditional form of C2: IF the meltwater figures are net freshwater delivered to the AAIW source region AND no other freshwater term moved enough to cancel, THEN reduced sea-ice melt explains the reversal."
$A tool --file $F --id T3 --card 02 --state RUN --source "$E" --error-type E1_DROPPED_VARIABLE \
  --output "Unit conversion (earth-systems-physics aaiw_reversal_2026.py): drop 6,600 km3/yr = 0.209 Sv, a third of the pre-2016 figure. That is about 63x the CDW-attributable ice-shelf basal melt (104.8 Gt/yr) the repo's CDW-AABW loop runs on. Each budget carries one of two freshwater terms that moved in opposite directions over the same years."
$A tool --file $F --id T4 --card 03 --state RUN --source "$V" \
  --output "Related, not independent of the trigger: Spira et al. 2026 (same journal) study the same 2015-16 sea-ice drop and attribute it to wind-driven mixing. The two papers agree on the event and sit at different links of one chain: wind -> mixing -> sea ice -> meltwater -> AAIW."
$A tool --file $F --id T5 --card 04 --state RUN --source "$U" \
  --output "Open branches for the AAIW reversal: (a) reduced sea-ice meltwater (paper); (b) wind and Ekman-transport changes acting directly on AAIW formation; (c) multi-year internal variability over a 9-year window; (d) change in data coverage. Cheapest discriminator: compare the post-2016 trend with all earlier 9-year windows of the same record."
$A tool --file $F --id T6 --card 05 --state RUN --source "$U" --error-type E2_STALE_CONDITIONS \
  --output "Term frame: 'healthy' AAIW is defined by the 1995-2015 state (A1). A baseline taken from one window is a reading of that window; 'reversal' is measured against it. The past-transition comparison sets a 9-year trend beside a completed state change (C4)."
$A tool --file $F --id T7 --card 06 --state RUN --source "$U" \
  --output "Target: has AAIW changed state, and why? Rendering: 'reversed', 'triggered by sea ice decline', 'may have underestimated'. Observed: a trend change over 9 years. Attribution and the sea-level implication are not checkable at press depth."

$A decide --file $F --id D1 --state DETECTED \
  --text "Add the sea-ice meltwater term beside ice-shelf melt in Southern Ocean freshwater budgets (earth-systems-physics CDW-AABW loop, CEED Thwaites audit). Does not depend on C2's attribution, only on the term being large and moving."
$A decide --file $F --id D2 --state UNRESOLVED \
  --text "Treat AAIW as having changed state (tipping) rather than as a multi-year excursion? Depends on C1 against earlier windows and on internal variability, not in the material read."

$A check --file $F
$A report --file $F > $D/report.md
