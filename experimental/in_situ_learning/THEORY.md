# Theory: an in situ learning program for AI, modelled on the DNP loop

Status: PROPOSED throughout. Nothing here has been run on an AI system. The toy in `loop.py` tests properties of the loop shape on constructed functions; it does not test the mapping below. Owner's question that started this: can the learning methods in Jensen et al. (arXiv:2603.19448) be turned into a learning program for AI?

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
- **Open:** whether the AI's procedure space has anything like resonance conditions, i.e. a physics-like prior that makes the search tractable. In the DNP case the prior came from spin theory; for AI procedures no equivalent theory is named here.
