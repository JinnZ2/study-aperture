# Theory: an in situ learning program for AI, modelled on the DNP loop

Status: PROPOSED throughout. Nothing here has been run on an AI system, and T7's measurement design has not been run on any corpus. The toy in `loop.py` tests properties of the loop shape on constructed functions; it does not test the mapping below. Owner's question that started this: can the learning methods in Jensen et al. (arXiv:2603.19448) be turned into a learning program for AI?

## The shape

```
                 in silico                                  in situ
   ┌──────────────────────────────┐          ┌───────────────────────────────────┐
   │ model of the system          │          │ the system itself                 │
   │ cheap, noiseless, unlimited  │          │ expensive, noisy, budgeted        │
   │ omits terms by construction  │          │ contains every term, including    │
   │ (two spins, zero line width) │          │ ones that belong to this instrument│
   └──────────────────────────────┘          └───────────────────────────────────┘
          finds the model's optimum                 finds this instrument's optimum
```

In situ learning does not remove the model's error. It swaps it: the omitted terms of the model are replaced by the specific terms of the instrument. What the loop learns is "the best procedure on this instrument, this sample, these weeks."

## Mapping

| DNP study | AI learning program |
|---|---|
| pulse sequence x | a procedure: order of checks, which tools run, prompt structure, thresholds |
| spectrometer | an environment that returns a measured outcome the learner does not author: a known-answer set, a test suite, a physical result, a person's correction |
| enhancement | outcome scored against that external key |
| two-spin simulation | the AI's self-model, or grading by a model of the same kind |
| constrained random walk onto resonances | method priors (cards, physics constraints) narrowing the search |
| electron offsets | the population of tasks; "broadband" = works across it |
| effective-field reading of the winners | extracting a rule from what worked, labelled DERIVED or PROPOSED |

## Six propositions (PROPOSED)

| # | Proposition | Toy evidence | Repo cross-link |
|---|---|---|---|
| T1 | In situ learning gains exactly the terms the model omits, and inherits the terms that belong to the instrument. Learning against one evaluator learns that evaluator. | E2: with a strong instrument-specific term, the learned procedure gains on A and is worse than the in silico optimum on B (retained -2.3). Below a threshold, the gain transfers fully. | Simulators `null-harness`, Goodhart in `proxy-investigation-lab` |
| T2 | Self-evaluation is in silico. A model grading its own procedure cannot see the terms its own construction omits. | E1: when the model omits a large term, in situ wins 8/8 seeds; when it omits nothing, in situ only adds noise (0/8). | `criterion-symmetry`, `frame-location-benchmark` FLB_010 |
| T3 | The learner chooses its own data. The record must keep every evaluation, not only the best; the best observed value overstates the truth, and the overstatement grows with noise. | E3: mean overstatement 0.004 → 0.2 → 0.51 as noise goes 0.05 → 0.15 → 0.3. | "failures are results" (Simulators `AGENTS.md`) |
| T4 | An evaluator that drifts invalidates what the surrogate has accumulated. A fixed reference probe, re-measured during the run, is the only way to see it. | not run (D1) | `criteria-drift`, `tools/known_answer.py` |
| T5 | A mean over tasks is a frozen average of a distribution of tasks; report the profile and the worst case. | E5: mean-optimal procedure has worst offset 0.518; worst-case-optimal 0.584 at a mean cost of 0.024. | Card 02 frozen-average check |
| T6 | A learning claim is a comparison at a stated budget against a null (random search) over several seeds. One run per arm does not order two methods. | E4: Bayesian beats random by median 1.006 vs 0.79, yet 17 of 64 single-run pairs reverse that order. | ADDENDUM C2 audit |

## A protocol that follows from T1-T6 (PROPOSED)

| # | Requirement | Answers |
|---|---|---|
| L1 | State the parameterisation and the budget before the run. | T6 |
| L2 | The objective comes from an environment the learner does not author; name it and its source. | T2 |
| L3 | Log every evaluation with time, not only the winner. | T3 |
| L4 | Interleave a fixed reference procedure every k evaluations. | T4 |
| L5 | Re-measure the recommendation n times outside the search before reporting it. | T3 |
| L6 | Report the per-task profile and the worst task beside the mean. | T5 |
| L7 | Evaluate the recommendation on a second environment (second evaluator, second instrument) before claiming it as a method rather than a fit. | T1 |
| L8 | Run at least 3 seeds per arm, with a random-search arm at equal budget. | T6 |

The DNP paper meets L1 and L2 in full, L6 in part (Fig. 3d), L7 in part (second sample, same instrument), and L3-L5, L8 not in the text read (GAPS.md).

## Where this could be measured here

- **Cheap, in this repository:** a loop that adjusts an assessment procedure (which cards, in what order) and scores it against records with planted, known defects, on `assess.py check` plus a known-answer set. A second instrument for L7: a different known-answer set written by someone else. Not built.
- **Open, partly answered by T7 below:** whether the AI's procedure space has anything like resonance conditions, i.e. a physics-like prior that makes the search tractable. In the DNP case the prior came from spin theory.

## T7: the system the AI acts on as the spin system (PROPOSED)

Proposed by the owner, 2026-10-28: human culture, traditions, economic systems, extraction cycles and turbulence may be to AI what electron spin is to the DNP experiment. Revised the same day for precision ("junk in gets junk out"): every physics statement carries a source or a computation, every human-side term has an operational definition or is marked UNDEFINED, and each row states its status.

Status words used in this section: **SOURCED** (stated in a cited source, read at the depth given), **COMPUTED** (`physics_side.py`, pinned), **STATED** (stated by the owner as their tradition's practice, 2026-10-28; recorded in their words where possible, not generalised to other people), **PROPOSED** (the analogy; not tested), **UNDEFINED** (no measurable definition yet; a gap, not a finding).

### Physics side (what the analogy borrows)

| # | Statement | Status | Source |
|---|---|---|---|
| P1 | The main field B0 splits each spin's energy levels; at thermal equilibrium the populations follow P = tanh(h nu / 2kT). | SOURCED (textbook) + COMPUTED | `physics_side.py` |
| P2 | In the paper's setup (proton Larmor about 14.8 MHz, 80 K): B0 = 0.3476 T, electron Larmor 9.742 GHz, thermal electron polarization 2.92e-3, proton 4.44e-6. | COMPUTED from Jensen et al. Sections 4.1-4.2 + CODATA | `physics_side.py` |
| P3 | Microwave pulses do not create the polarization. They transfer the electrons' thermal polarization, created by B0, to the protons. The ceiling on enhancement is P_e / P_H = 658 (the gyromagnetic ratio); the paper reports values "approaching 180". | COMPUTED; paper value SOURCED (Section 2.2) | `physics_side.py`; arXiv:2603.19448 |
| P4 | Transfer happens only when the drive's effective field meets a resonance condition (ZQ or DQ matching with the proton Larmor frequency). The paper's constrained search restricted sequences to these conditions. | SOURCED | Jensen et al. Sections 2.1-2.2, SI Fig. S4 |
| P5 | When the drive stops, the transferred proton polarization relaxes back toward its thermal value. The paper's build-up times (2 s to 64 s depending on sample) are the timescale on which enhancement is built and lost. | SOURCED (build-up times, Section 2) | Jensen et al. Figs. 2-4 captions |
| P6 | Spins can come to anticipate a periodic drive. In quantum dots under a periodic pulse train, the nuclear spin bath reshapes ("the initial normal distributed Overhauser field evolves towards a comb like structure") so that electron precession completes whole periods between pulses, and "a revival of this polarization emerges just before the arrival of the subsequent pulse." | SOURCED | Greilich et al., *Science* (2007) 1896-1899, doi:10.1126/science.1146850 (record read, full text not); quotes from arXiv:2004.02623 |
| P7 | The paper's two-spin constraint was applied to trityl only. For 4-oxo-TEMPO (an electron coupled to 14N and many protons) the unconstrained search reached 13 vs 9 for Monte Carlo, and the authors call the efficiencies "not impressive". | SOURCED | Jensen et al. Sections 2.4, 3 |

### Order is defined only relative to a field

Polarization means nothing until its axis is stated (P1). "Order" is the same: without its field it is an incomplete quantity. Two fields act on human systems:

```
B_physics   the ground: energy, mass balance, regeneration; nobody can switch it off
B_imposed   the structure: law, prices, debt, tenure; set by people, changeable by people
```

| Definition | Field | Status |
|---|---|---|
| The common meaning ("social order", "law and order"): alignment of practices with the imposing structure, usually without naming it. | B_imposed | PROPOSED reading of common usage |
| The owner's tradition: "alignment with physics as best as we are able to calibrate to what is known today, with our minds open to updating constantly as conditions change." | B_physics | STATED |

The tradition's definition carries two practices as part of it, not as additions (STATED): awareness of one's own scope, and a constant search for more understanding; and internal audits run constantly, so as to stay calibrated to the environment. Corrected by the owner the same day: the tradition of calibration is stated as not common; whether constant internal audit is uncommon is not known. Either difference may be partly one of words, other traditions doing the same under other names (open; not checked).

Read against this folder (PROPOSED): this is the in situ loop with physics as the instrument. Constant internal audit is L4 (re-measure a fixed reference during the run) and T4 (an uncalibrated evaluator drifts). Awareness of scope is a declared range of validity (Card 02 `range`; the frozen-average check's population and window). Updating as conditions change is refusing to freeze the average.

Precision note: physics is also known through instruments, so B_physics here is physics as currently calibrated. The stated definition already carries this ("as best as we are able to calibrate").

### Mapping

| DNP (physics row) | Human systems | Operational definition on the human side | Status |
|---|---|---|---|
| main field B0 (P1) | the imposing structure: economic and extraction systems | rules backed by enforcement that set the cost of each available practice (law, prices, debt terms, land tenure). Measurable as cost per practice, by date. | PROPOSED; definition partial |
| spin populations aligned to B0 (P1) | people, practices, traditions aligned to that structure | share of a population carrying out each practice, by date | PROPOSED |
| thermal equilibrium populations (P1, P2) | what corpus statistics record | frequency and sense of practice terms in text from a stated corpus and window | PROPOSED |
| natural frequencies (P4) | cycles already running: seasons, generations, credit and extraction cycles, ritual calendars | a recurring practice with a measurable period and phase | PROPOSED |
| resonance condition (P4) | an intervention takes hold only when matched to an existing cycle | intervention period and phase relative to the cycle's | PROPOSED |
| order transferred, ceiling set by the field (P3), relative to B_imposed | order an AI can move relative to the imposing structure; ceiling set by the structure | alignment of practices with what the structure makes cheap: cost per practice by date against how often the practice occurs | PROPOSED; measurable |
| the same, relative to B_physics | order relative to physics; ceiling set by physics | alignment with energy and mass balance and regeneration, recalibrated as conditions change: dissipation of a practice against the regeneration rate of the substrate it draws on (Simulators `extraction-blindness-sim`, `fragility-cascade` aim at this) | PROPOSED; partly measurable |
| relaxation after the drive stops (P5) | effects of an intervention fade back to the structure's equilibrium unless the structure changes | decay time of an intervention's effect after it ends | PROPOSED |
| anticipation of a periodic drive (P6) | anticipation by people of the drive applied to them | graded, see the breaks table | PROPOSED |
| many coupled spins, the two-spin constraint not applied (P7) | turbulence: many-body, nonlinear | UNDEFINED | PROPOSED |
| microwave pulses + the learner | AI | the procedure the AI applies and the loop choosing it | PROPOSED |
| 1H solid echo, the readout | language | measures computed from text (term frequency, sense, frame density) | PROPOSED |

### What follows (PROPOSED)

1. **The search constraints live in the system, not in the optimizer** (from P4, P7). In the paper the tractable search came from spin physics, and where the physics was many-body the constraint was not available. Here the constraints would come from the system's own cycles, most of them held by the people inside the cycles and not written down.
2. **Corpus statistics are a field-frozen average** (from P1, P5). Equilibrium populations exist only in their field. Text statistics are the population aligned under the current imposing structure, not the system's own state. An AI trained on them learns the structure's alignment and can read it as human nature. This extends the Card 02 frozen-average check: an average can be frozen by a field as well as by a window.
3. **The drive moves order; it does not create it, and the field sets the ceiling** (from P3). Read across, with the field named: order relative to B_imposed was created by the structure and is capped there; order relative to B_physics is capped by physics. The two can point in different directions. An AI trained on corpus statistics sees mainly the first (point 2).
4. **What is moved relaxes back** (from P5). Without a change in the field, an intervention's effect decays toward the field's equilibrium. The decay time is the measurable quantity.
5. **History is the evaluations already run.** Billions of tokens of written, rewritten and explored record are a log of past trials. A loop can read them instead of running new trials on people. The log's quality decides what can be learned: successes kept and failures dropped (E3's overstatement at large scale), rewriting as drift in the log (T4), and who kept the archive deciding what was measured (Simulators `observer-exclusion`).
6. **Language is the readout channel.** It can be evaluated cheaply from existing text (Simulators `term-drift-citation`, `frame-token-audit`). Its bandwidth is what was spoken or written down, as the paper's readout sees protons and not electrons.

### Where the analogy breaks, after the owner's corrections

| Earlier break | Correction | What remains |
|---|---|---|
| "the sample responds back; spins don't" | Spins respond to the field (P1, P5); the sample also loads the resonator (the paper recalibrates the microwave profile each session, Methods 4.1). | A difference of degree, not kind. |
| "a spin has no model of the pulse sequence; people can anticipate the one applied to them" | Withdrawn. Spins can come to anticipate a periodic drive (P6). Not all people can: anticipating a drive requires seeing it, and the rule may be opaque, the information unavailable, or the period longer than a lifetime. | Anticipation is a graded variable in both: (memory of the drive) x (visibility of the drive). The earlier wording made it a category and put humans on the special side. Corollary (PROPOSED): an imposing structure that hides its own drive lowers the anticipation of the people under it. |
| "evaluations on people are not cheap or reversible" | History is billions of evaluations already run. | Reading history and language is observation. A loop that proposes the next intervention is the pulse sequence; consent and irreversibility apply to that step. |
| "one cycle can take a generation" | Language can be evaluated now. | None at the readout; the cycles themselves stay slow. |
| "the AI is the source of order" | AI is the AI; the field does the imposing. | None; the mapping uses the correction, and P3 supports it on the physics side. |

### Measurement design: field-change removal test (not run)

Claim under test (from What follows 2 and 4): measures of a practice in text track the imposing structure, not the practice's own state. The same test tells which field a practice is aligned to: alignment with B_imposed should relax when the structure changes (P5); alignment with B_physics should hold, because that field is not switched off by a regime change. Practices tuned to seasons, soil and water are predicted to hold across the change; practices that exist because a rule made them cheap are predicted to move with the rule.

- **Cases.** Datable changes in an imposing structure (enclosure, colonial imposition or withdrawal, a market collapse, the end of an extraction regime), with text on both sides of the change. Cases, corpora, change dates and measures are fixed and recorded before any text is read.
- **Readout.** The same measures before and after: term frequency and sense for the practice, frame density (`frame-token-audit`), what is described as normal or costly.
- **Prediction (P1, P5 read across).** (a) A step in the measures at the change date larger than their pre-change variation; (b) afterwards, an approach to a new level with a measurable time constant.
- **Null.** No step beyond pre-change variation, or a step that reverses to the pre-change level: the alignment was the practice's own, not the structure's.
- **Resonance prediction (P4 read across).** Interventions matched in period and phase to an existing cycle show an effect that outlasts the intervention; unmatched ones show a disturbance that decays (P5). Null: no dependence on timing relative to the cycle. This is the Simulators `SHAPE_SPEC.md` removal test: if the constraint set is shared, timing matters; if not, the shape does not carry over.
- **Confounds, stated before running.** The record's selection (who wrote, whose text survived); a change in the structure also changes who writes; sense drift in the counted terms (Simulators `coinage-log`, `term-drift-citation`); the change date may be contested.
- **Cost.** Existing text only; no intervention on anyone.
