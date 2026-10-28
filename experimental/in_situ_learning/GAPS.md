# Gap analysis: Jensen et al., in situ learning-based pulsed DNP

Status: gap analysis of one paper, 2026-10-28. Source read: the arXiv preprint (arXiv:2603.19448, HTML rendering, CC BY 4.0) through a fetch tool, including targeted questions (a)-(h) below. **Not read:** the published *Science Advances* version (it may differ), Supplementary Tables S1-S17 and Figures S1-S16, and the cited literature. Every "not found" below means not found in the text read, not absent from the work.

Source: Jensen, Carvalho, Wili, Holk Thomsen, Goodwin, Trottner, Strauch, Bodholt Nielsen, Nielsen, *In situ Learning-Based Spin Engineering of Pulsed Dynamic Nuclear Polarization*, https://arxiv.org/html/2603.19448

## What the study does

```
parameters x (pulse amplitudes, phases, repetitions)
      │
      ▼
home-built X-band DNP spectrometer ──► 1H solid-echo enhancement, averaged over electron offsets
      ▲                                         │
      │                                         ▼
 next x  ◄── expected-improvement-plus ◄── Gaussian process (ARD Matern 5/2)
      ▲
 optional prior: constrained random walk onto ZQ / DQ resonance conditions
```

- Trityl OX063, 80 K: 1000 evaluations per run, 51 h (about 3 min each). Best enhancement 10 for Bayesian vs about 7 for Monte Carlo. 15 for a 24-pulse constrained sequence. Offset-integrated (-60 to 60 MHz): cRW-OPT1 98, BayesOpt 96, PLATO 69, NOVEL 35. (Section 2.2, Fig. 2)
- 4-oxo-TEMPO, 80 K: Bayesian 13 vs Monte Carlo 9 (2000 sequences). (Section 2.4, Fig. 4)
- Simulation for comparison: a two-spin e-1H model, infinitely narrow EPR line, 4.5 A point dipole. The experiment was more broadband than the simulation; the authors attribute this mainly to finite line width. (Section 2.2, Fig. 2d)

## What holds in the text read

| | Basis |
|---|---|
| The in situ loop runs and improves on its own random-search baseline in both systems | Figs. 2, 4 |
| Constrained and unconstrained Bayesian runs had equal budgets (1000 each) | Fig. 2 caption |
| Learned sequences were tested on a second sample (glycerol-d5 → glycerol-d8) | Fig. 2 caption, Fig. 3f |
| Learned sequences were compared with published ones (NOVEL, PLATO) over an offset range | Section 2.2 |
| The authors flag their own weak points: deterministic noise model "may, in retrospect" be debatable; TEMPO efficiencies "not impressive"; constraint "may restrict the search space" | Sections 2.2, 2.4, 3 |

## Gaps

| # | Gap | Located | Why it matters | Toy measurement |
|---|---|---|---|---|
| G1 | **No replicate optimizations.** Every comparison (10 vs 7, 13 vs 9) is one run against one run. | (a) not found; SI 1.c `rng('shuffle')` only | Bayesian optimization and Monte Carlo are both stochastic. One run per arm is n = 1 within-run. | E4 |
| G2 | **Reported values are best observed during the search.** Fig. 4d plots the value "measured during the optimization". Re-measurement shown for trityl offsets, no error bars. | (d) partial | The maximum of many noisy measurements overstates the true value at that point. | E3 |
| G3 | **Instrument assumed stationary over 51 h.** Calibration per session, no drift monitoring within a run. | (b) not found; Methods 4.1 | The surrogate pools evaluations from hour 1 and hour 51 as one function. If the instrument drifts, early evaluations describe a different instrument. Card 02 frozen-average check: window and stationarity unstated. | design only (D1) |
| G4 | **Objective is a mean over offsets** (7 offsets for trityl; 1 for TEMPO). | Section 2.1 | A mean can be high with a hole at one offset. "Broadband" is read from the mean. | E5 |
| G5 | **Source of the in situ gain not separated.** Fig. 3c: the optimization "captures either spin-system or instrumental aspects". Transfer tested to a second sample, not to a second spectrometer or resonator. | (e); Section 2.3 | A gain from the sample transfers to other instruments; a gain from this resonator's quirks does not. The paper cannot yet tell which it found. | E2 |
| G6 | **TEMPO budgets not confirmed as matched.** Monte Carlo 2000; Bayesian count in Table S12 (not read). | (c) | "Bayesian 13 vs Monte Carlo 9" is only a method comparison at equal budget. | none |
| G7 | **70% gain has two baselines.** Results: vs a 31 MHz spin-lock. Discussion: vs NOVEL. | Sections 2.4, 3 | One figure, two denominators. | none |
| G8 | **Noise model** deterministic for Figs. 2a-c, noisy elsewhere. | Section 2.1 (authors' own flag) | A deterministic GP treats a lucky measurement as the truth there; this sharpens G2. | E3 (indirectly) |
| G9 | **Experimental code not released**; only the in silico MATLAB code. | (h); SI 1.c | In situ results reproduce only on an instrument; without the control code even an instrument owner cannot rerun the loop as run. | none |
| G10 | **Simulation baseline is an idealization**: two spins, infinitely narrow line. | Section 4.5 | This is the paper's reason for going in situ. It also means "in situ beats in silico" partly measures how idealized the simulation was; a simulation with a finite line width is the cheaper comparison. | E1 |
| G11 | **Physics prior only tested where it was derived.** Constrained random walk used for trityl only; TEMPO is not two-spin dominated. | Sections 2.4, 3 | A prior narrows the search to where the prior's physics holds. | design only (D2) |

## Discriminators (cheapest first)

| Gap | Cheapest observation that would close it |
|---|---|
| G1, G2 | Re-run the same loop 3-5 times; re-measure each recommended sequence 5-10 times outside the search. |
| G3 | Interleave one fixed reference sequence every k evaluations; plot it against time. |
| G4 | Report the per-offset profile and the worst offset beside the mean (partly in Fig. 3d). |
| G5 | Run the learned sequences on a second resonator or spectrometer; or re-run the in silico optimization with a finite EPR line width. If the line-width simulation reproduces the broadband gain, it is sample-side. |
| G10 | Same as the second half of G5. |
