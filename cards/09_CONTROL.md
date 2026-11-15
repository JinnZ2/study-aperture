# Card 09 — Control: a run that should fail

**Provenance:** worked out on 2026-11-15 from JinnZ2/explorative-math runs at commit `80b9ed0` (CC0, co-authored): `experiments/fibonacci_chain.py`, `experiments/simplex_4d.py`, `experiments/golden_angle.py`, and `open_questions.md` Q12. Status: a procedure. Its rule maps onto the existing support vocabulary, but `assess.py` does not check for a control. It is not in the routing table; run it on any claim that a method found, detected or matched something. Co-authored.

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
| both φ unions have the same symmetry order (Q12) | shapes of known, different orders | the probe returns different orders | not run | `CONTROL_ABSENT` → the equality is `UNTESTED`. Q12 is the control's specification. |

## 5. Limits

- A control that fails as expected shows that the method can say no on that input. It does not show that the method is right on other input.
- Choosing the control is a judgement. Record who chose it and before or after seeing the main result.
- One repository's runs; all of these controls were built by the same hand as the method.
