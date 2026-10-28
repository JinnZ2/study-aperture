# In situ learning (experimental)

Status: experimental, 2026-10-28. Implemented: a gap analysis of one paper (`GAPS.md`), a stdlib toy of the learning loop with five measured experiments (`loop.py`, pinned by `test_loop.py`), and a proposed learning program for AI (`THEORY.md`). **Not established:** anything about spin systems or real instruments (the toy is constructed), and anything about AI systems (the program has not been run). Independent of `assess.py` and of `scope_audit_lab`; nothing here enters an assessment record.

Source paper: Jensen et al., *In situ Learning-Based Spin Engineering of Pulsed Dynamic Nuclear Polarization*, arXiv:2603.19448 (published in *Science Advances*; the arXiv preprint was read, not the journal version).

## Files

| File | Contents |
|---|---|
| `GAPS.md` | what the study does, what holds, gaps G1-G11 with locations, cheapest discriminators |
| `THEORY.md` | mapping to an AI learning program, propositions T1-T6, protocol L1-L8, and T7 (the owner's proposal: human systems as the spin system, with a field-change removal test); all PROPOSED |
| `loop.py` | stdlib Gaussian process + expected improvement on constructed functions; experiments E1-E5 |
| `test_loop.py` | selftest + sample regeneration check |
| `samples/run.txt` | the pinned output of `python3 loop.py` |

## Toy results (samples/run.txt)

```
truth on instrument k:  g + m + h_k        simulation: g
                        m = physics the simulation omits (shared)
                        h_k = term belonging to instrument k only
```

| | Question | Result |
|---|---|---|
| E1 | When does in situ beat in silico? | Only when the simulation omits a large term: 0/8 seeds at no omission, 8/8 at a large one, 6/8 with high noise. |
| E2 | Does what was learned on instrument A hold on B? | Fully, while the instrument term is small. When it dominates, the learned procedure is worse on B than the in silico one (retained -2.3). |
| E3 | Does the best observed value overstate? | Yes, growing with noise: mean overstatement 0.004, 0.2, 0.51 at noise 0.05, 0.15, 0.3. |
| E4 | Does one run per method order two methods? | Bayesian median 1.006 vs random 0.79, but 17 of 64 single-run pairs reverse the order. |
| E5 | What does a mean over offsets hide? | Mean-optimal worst offset 0.518 vs 0.584 for the worst-case optimum, at a mean cost of 0.024. |

Every number is a property of the constructed functions, seeds 0-7, budget 30.

## Run

```sh
python3 loop.py selftest          # fast checks
python3 loop.py                   # E1-E5, about 10 s
python3 -m unittest test_loop.py  # selftest + output matches samples/run.txt
```
