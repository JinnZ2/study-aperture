# Card 09 — Control: a run that should fail

**Provenance:** worked out on 2026-11-15 from JinnZ2/explorative-math (CC0, co-authored). The runs `experiments/fibonacci_chain.py`, `experiments/simplex_4d.py` and `experiments/golden_angle.py` are at `main` `80b9ed0`. The Q12 control run is on `main` at `3b8e9ab`, merged 2026-11-15 from `claude/quasicrystal-projection-properties-448bx7` (`runs/symmetry_resolution_seed0.json`, `docs/resolution_leak.md` row 2a). Status: a procedure. Its rule maps onto the existing support vocabulary, but `assess.py` does not check for a control. Routed by default for EMPIRICAL, REVIEW and SIMULATION (Card 00); run it on any claim that a method found, detected or matched something. Co-authored.

## 1. What the card is for

A method that reports a finding has to be run on input where the finding should not appear. That input is a **wrong-rule control** (the same procedure under a rule that should not produce the effect) or a **random control** (the same procedure on unstructured input). If the control also "finds" it, the method was reporting itself.

If no control was run, the result was never put at risk. It is `UNTESTED`, however clean it looks.

## 2. Procedure

1. **Name the finding** and the method that produced it.
2. **Name the control that should fail**: what input, under what rule. Then say what failing looks like, as a value or a range, before reading the control's output.
3. **Look for the control in the material.** Record one of:
   - `CONTROL_RUN_FAILED_AS_EXPECTED`: the control did not show the finding.
   - `CONTROL_RUN_ALSO_FOUND`: the control showed the finding too. The method does not separate signal from no signal here.
   - `CONTROL_ABSENT`: no control was run.
4. **Set the claim's support from that state:**
   - `CONTROL_ABSENT` → the claim's support is at most `UNTESTED`, whatever the main run shows.
   - `CONTROL_RUN_ALSO_FOUND` → `UNSUPPORTED`, for the claim that the method detects the effect.
   - `CONTROL_RUN_FAILED_AS_EXPECTED` → the claim may be graded on the main run.
5. **A control has to differ from the main run in only the one thing it tests.** If it differs in two, name both; the result separates neither.

## 3. Outputs

- For each finding: its control, the predicted failure, the control's state, and the support that state allows.
- A finding with `CONTROL_ABSENT` is listed as incompleteness, with the control that would test it.

## 4. Worked cases: explorative-math

| Finding | Control | Predicted failure | Observed | State |
|---|---|---|---|---|
| Z² cut at slope 1/φ gives a chain with no short period (`fibonacci_chain`) | rational slope 1/2, same cut | a fixed small period | golden prefix periods 5, 13, 21, 34, 89, 233 (lengths 10 to 320); control period 3 at every length | `CONTROL_RUN_FAILED_AS_EXPECTED` |
| the golden angle packs most evenly (`golden_angle`) | rational turns 2/5 (144°) and 3/8 (135°) | spokes, uneven gaps | worst two by `nn_cv`: 0.399 and 0.407, against 0.018 for golden | `CONTROL_RUN_FAILED_AS_EXPECTED` |
| the Petrie projection of the 5-cell is reached (`simplex_4d`) | 2000 random rotations | random search does not land on it | best random score 23.45, median 152.83; Petrie 2.2e-14 | `CONTROL_RUN_FAILED_AS_EXPECTED`. The reading in the run is that the view was found by construction, not by search. |
| both φ unions have the same symmetry order (Q12), probe at `k_max` 12 | a regular 8-gon and 16-gon, known orders 8 and 16 | the probe returns different lists | `[2, 4, 8]` for both: the control also reads "equal" | `CONTROL_RUN_ALSO_FOUND` → at `k_max` 12 an "equal" reading carries no information about the unions |
| the same, probe at `k_max` 24 | the same pair | different lists | `[2, 4, 8]` against `[2, 4, 8, 16]` | `CONTROL_RUN_FAILED_AS_EXPECTED` → the unions' equal lists at `k_max` 24 can be read. Logged as "not a leak at the bounds tested"; Q12 stays PROPOSED because only two of its listed shapes were run |

## 5. Limits

- A control that fails as expected shows that the method can say no on that input. It does not show that the method is right on other input.
- Choosing the control is a judgement. Record who chose it and before or after seeing the main result.
- One repository's runs; all of these controls were built by the same hand as the method.
- The Q12 rows show the state can depend on a setting of the method: the same control is `ALSO_FOUND` at one `k_max` and `FAILED_AS_EXPECTED` at another. Record the setting beside the state.
