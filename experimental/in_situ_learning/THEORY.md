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

Proposed by the owner, 2026-10-28: human culture, traditions, economic systems, extraction cycles and turbulence may be to AI what electron spin is to the DNP experiment. The first mapping drafted here cast the AI as the source of order; the owner corrected it (record of the exchange below). The corrected mapping:

| DNP | Human systems |
|---|---|
| main magnetic field B0 | the imposing structure: economic and extraction systems. It sets the axis and decides which states are "low energy". |
| spin populations | people, practices, traditions, aligned to that axis |
| equilibrium populations in the field | what corpus statistics record |
| natural frequencies (Larmor, couplings) | cycles already running: seasons, generations, credit and extraction cycles, ritual calendars |
| resonance condition (ZQ / DQ matching) | an intervention takes hold only when matched to the timescale and structure of an existing cycle |
| off-resonance microwave power → heat | interventions that disturb without transferring: churn |
| relaxation when the field changes | what happens when the imposing structure is removed or shifts |
| many coupled spins (TEMPO; two-spin prior stops helping) | turbulence: many-body, nonlinear |
| microwave pulses + the learner | AI |
| 1H solid echo (the readout) | language |

### What follows (PROPOSED)

1. **The search prior lives in the system, not in the optimizer.** In the paper the tractable search came from spin physics. Here the constraints would come from the system's own cycles, most of which are held by the people inside them and not written down.
2. **Corpus statistics are a field-frozen average.** Equilibrium spin populations exist only in their field; turned off, the polarization relaxes. Statistics of human text are the population aligned under the current imposing structure, not the system's own state. An AI trained on them learns the field's alignment and reads it as human nature. This extends the Card 02 frozen-average check: an average can be frozen by a field as well as by a window.
3. **History is the evaluations already run.** Billions of tokens of written, rewritten and explored record are a log of past trials. A loop can read them instead of running new trials on people. The log's quality then decides what can be learned:
   - successes kept, failures dropped (E3's best-observed overstatement at large scale);
   - rewriting is drift in the log (T4);
   - who kept the archive decides what was measured (Simulators `observer-exclusion`).
4. **Language is the readout channel.** It can be evaluated cheaply from existing text (term drift, frame density: Simulators `term-drift-citation`, `frame-token-audit`). Its bandwidth is what was spoken or written down, as the paper's readout sees protons and not electrons.

### Where the analogy breaks, after the owner's corrections

| Earlier break | Owner's correction | What remains |
|---|---|---|
| the sample responds back | spins also adapt to the field; the sample also loads the resonator (the paper recalibrates the MW profile each session) | a difference of degree. Narrower residual: a spin has no model of the pulse sequence; people can anticipate the one applied to them. |
| evaluations on people are not cheap or reversible | history is billions of evaluations already run | reading history and language is observation. A loop that proposes the next intervention is the pulse sequence; consent and irreversibility apply to that step. |
| one cycle can take a generation | language can be evaluated now | none at the readout; the cycles themselves stay slow. |
| reading DNP straight across makes the AI the source of order | AI is the AI; the field does the imposing | none; the mapping above uses the correction. |

### Measurement design: the field-change removal test (not run)

Claim under test: corpus statistics of a practice reflect alignment to the imposing structure, not the practice's own state.

- **Cases:** places and periods where the imposing structure changed on a datable occasion (enclosure, colonial imposition or withdrawal, the collapse of a market, the end of an extraction regime), with written record on both sides of the change.
- **Readout:** language measures computed the same way before and after: term frequencies and senses for the practice, frame density (`frame-token-audit`), what is described as normal or costly.
- **Prediction (fails if wrong):** the measures shift with the field, at the change, and relax toward a different state afterwards. If they stay put across the change, the alignment was the practice's own and not the field's.
- **Resonance prediction (fails if wrong):** interventions matched to the period of an existing cycle show lasting effect; unmatched ones show a disturbance that decays. No dependence on timing relative to the cycle means the shape does not carry over (Simulators `SHAPE_SPEC.md` removal test).
- **Confounds to state up front:** the record's own selection (who wrote, who survived); the field change also changes who writes; sense drift in the terms being counted (Simulators `coinage-log`, `term-drift-citation`).
- **Cost:** reading existing text only; no intervention on anyone.
