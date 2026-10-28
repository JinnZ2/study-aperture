#!/usr/bin/env bash
# Rebuild assessment.json and report.md for this example from the CLI. CC0.
# Material actually read (2026-10-28): the Nagoya University press release (U) and the
# arXiv abstract page of an independent CALET study of the same storm (V). The paper
# itself (DOI 10.1029/2026GL125879) was not reachable: the Wiley page and phys.org both
# returned client errors through the fetch tool. Run from the repository root:
#     bash examples/arase-may2024/build.sh
set -eu
D=examples/arase-may2024
F=$D/assessment.json
U=https://en.nagoya-u.ac.jp/news/articles/pr-2024-solar-storm-triggered-ultra-relativistic-electrons-inside-earths-impenetrable-barrier/
V=https://arxiv.org/abs/2602.03990
A="python3 assess.py"
rm -f "$F"

$A init --file $F --title "Miyoshi et al. (2026): Local Acceleration of Multi-MeV Electrons Inside Earth's Impenetrable Barrier During the May 2024 Superstorm" \
  --type EMPIRICAL \
  --citation "Geophysical Research Letters 2026, doi:10.1029/2026GL125879; press release dated 2026-10-28, $U" \
  --materials "Press release only (read through a fetch tool). Paper, figures, methods and supplement NOT read: Wiley and phys.org pages returned client errors. Independent check: arXiv:2602.03990 abstract page (CALET on the ISS, same storm), read through a fetch tool. Baker et al. 2014 (origin of the barrier) not read." \
  --context "User-chosen study. Two decisions it could feed: whether spacecraft radiation planning can treat the region inside about 3 Earth radii as protected from multi-MeV electrons, and whether radiation-belt forecast models need a local acceleration source at low L. No decision owner named."

# ---- design checks (at press-release depth; most are not inspectable)
$A design --file $F --check selection --state CHECKED --source "$U" \
  --finding "One storm (May 2024), described as a superstorm. The release reports no other event and no generalization. n = 1 event: the result is an existence observation, not a rate."
$A design --file $F --check measurement_validity --state NOT_CHECKED --source "$U" \
  --finding "Phase space density (PSD) against radial distance requires adiabatic coordinates computed from a magnetic field model. Which model, and whether the peak survives a second model during an extreme storm, is not in the material read."
$A design --file $F --check confounding --state CHECKED --source "$U" --error-type E1_DROPPED_VARIABLE \
  --finding "The release links the peak to chorus waves through co-occurrence (intense chorus; plasmasphere eroded, recovery about 4.3-4.7 days vs about 2 typical). The same erosion changes plasmaspheric hiss, which the release itself names as a shaper of the barrier through scattering loss. Loss is not carried into the 'local gain' inference in the text read."
$A design --file $F --check uncertainty --state NOT_CHECKED --source "$U" \
  --finding "No uncertainties on PSD, peak height, or peak growth in the material read."
$A design --file $F --check preregistration --state NOT_APPLICABLE --source "$U" \
  --finding "Event study of a natural storm; preregistration not expected."

# ---- claims
$A claim --file $F --id C1 --label OBSERVED --support SUPPORTED --grade MEASURED_PRESENT \
  --text "in 2024, Japan's Arase space probe detected these electrons well inside the barrier" \
  --evidence "Press release; paper figures not read. Independently: CALET reports relativistic electrons down to L = 2.2, below the nominal L = 2.8 barrier, persisting months ($V)" \
  --measurand "presence of multi-MeV (some above 3 MeV) electrons inside about 3 Earth radii" \
  --instrument "Arase particle instruments (paper); CALET on the ISS (independent, integral count rates)" \
  --range "May 2024 storm and after" \
  --falsifiers "Arase and CALET both report presence from different orbits and detectors. A shared contamination (for example penetrating protons counted as electrons) would have to affect both." \
  --source "$U"
$A claim --file $F --id C2 --label DERIVED --support UNDETERMINED --grade UNDECLARED \
  --text "the electrons were accelerated locally rather than infiltrating from outer radiation belts" \
  --evidence "Press release: a distinct local PSD peak near the barrier boundary that strengthened over time. Method not read." \
  --measurand "radial PSD profile at fixed adiabatic invariants; growth of a local maximum" \
  --instrument "Arase electron data over several orbits, converted to PSD with a magnetic field model (model not stated in material read)" \
  --range "one storm" \
  --falsifiers "The peak disappears or moves when PSD is recomputed with a second field model; or a transport model with fast inward injection and L-dependent loss reproduces a growing peak at the same place; or the peak is absent at other first invariants where chorus acceleration predicts it." \
  --source "$U"
$A claim --file $F --id C3 --label PROPOSED --support UNTESTED --grade UNDECLARED \
  --text "chorus waves ... potentially providing favorable conditions" \
  --evidence "Press release: intense rising/falling-tone chorus seen by Arase; plasmasphere slow to recover (about 4.3-4.7 days vs about 2 typical)" \
  --measurand "energy transfer from chorus to multi-MeV electrons at about 3 Earth radii" \
  --instrument "Arase wave measurements; link to acceleration by timing" \
  --falsifiers "A quasi-linear or test-particle calculation with the observed chorus amplitude and density gives acceleration far too slow to build the observed peak in the observed time. Not reported in the material read." \
  --source "$U"
$A claim --file $F --id C4 --label DERIVED --support PARTIALLY_SUPPORTED --grade UNDECLARED \
  --text "The so-called impenetrable barrier seemed to have been broken." \
  --evidence "Press release; C1" \
  --measurand "whether multi-MeV electrons can exist inside the empirical inner boundary first reported in 2014" \
  --instrument "comparison of the May 2024 observation against the boundary location" \
  --falsifiers "The 2014 boundary was characterized over storms of a range that did not include a superstorm; if so, 'broken' and 'outside the conditions it was measured in' predict the same observation." \
  --source "$U"

# ---- input averages (Card 02 frozen-state check)
$A average --file $F --id A1 --text "location of the impenetrable barrier (inner edge of multi-MeV electrons)" --value "about 3 Earth radii (L about 2.8)" \
  --population UNDECLARED --window UNDECLARED --stationarity UNDECLARED \
  --estimated-from "storms observed before the 2014 discovery (Baker et al. 2014, not read); L = 2.8 is CALET's 'nominal' value" \
  --claim C4 --source "$U"
$A average --file $F --id A2 --text "typical plasmasphere recovery time" --value "about 2 days" \
  --population UNDECLARED --window UNDECLARED --stationarity UNDECLARED \
  --claim C3 --source "$U"

# ---- card runs
$A tool --file $F --id T1 --card 00 --state RUN --source "$U" \
  --output "Type EMPIRICAL (single-event spacecraft observation plus interpretation). Material is a press release, so cards run on what the release states; method-level checks are NOT_CHECKED rather than passed."
$A tool --file $F --id T2 --card 01 --state RUN --source "$U" \
  --output "4 claims. Conditional form of C2: IF the PSD peak is real in adiabatic coordinates (field-model independent) AND transport plus loss cannot build a growing peak there, THEN the electrons were accelerated locally. Neither antecedent is checkable from the release."
$A tool --file $F --id T3 --card 02 --state RUN --source "$U" \
  --output "C1 graded MEASURED_PRESENT (direct detection, corroborated). C2 and C3 UNDECLARED: PSD depends on a field model not named in the material, and the chorus link is by timing. Two input averages, both FROZEN as stated: the barrier location (A1) and the typical recovery time (A2)."
$A tool --file $F --id T4 --card 03 --state RUN --source "$V" \
  --output "Independent route for C1: CALET on the ISS (different orbit, detector, team) sees relativistic electrons at L 2.2-3.2 for months after the storm. Supports presence, not mechanism: CALET reports count rates, not PSD. CALET's own wording ('pushed down' from the outer belt, per its plain language summary as read) is a transport reading of the same event. So: agreement on presence, the two routes differ on mechanism wording."
$A tool --file $F --id T5 --card 04 --state RUN --source "$U" \
  --output "Open branches for the growing PSD peak: (a) local acceleration by chorus (paper); (b) fast inward transport plus L-dependent loss (hiss inside the eroded plasmasphere) leaving an apparent peak; (c) the peak is produced by the field model used to compute adiabatic coordinates during an extreme storm; (d) a mixture. Cheapest discriminator: recompute PSD with a second field model, and check the peak across several first invariants. Whether the paper ran either is not in the material read."
$A tool --file $F --id T6 --card 05 --state RUN --source "$U" --error-type E2_STALE_CONDITIONS \
  --output "Term frame: 'impenetrable barrier' names an empirical boundary from observations up to 2014 and is used in the release as if it were a property of the system ('broken'). The May 2024 storm is outside the storm range that boundary was characterized on (window and population undeclared, A1). The boundary is a reading taken under earlier conditions applied under new ones."
$A tool --file $F --id T7 --card 06 --state RUN --source "$U" \
  --output "Target: where do multi-MeV electrons inside about 3 Earth radii come from? Rendering: 'accelerated locally rather than infiltrating'. Presence is observed twice independently (C1); mechanism is an inference from one PSD profile in one storm, not checkable at press-release depth (C2)."

# ---- decisions
$A decide --file $F --id D1 --state DETECTED \
  --text "Stop treating the region inside about 3 Earth radii as protected from multi-MeV electrons in spacecraft radiation planning for superstorm conditions. Depends only on C1 (presence, two instruments), not on the mechanism."
$A decide --file $F --id D2 --state UNRESOLVED \
  --text "Add a local acceleration source at low L to radiation-belt forecast models? Depends on C2, which is UNDETERMINED here: needs the paper's PSD method and the field-model check (T5)."

$A check --file $F
$A report --file $F > $D/report.md
