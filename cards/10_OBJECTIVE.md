# Card 10 — Objective: "best" names its measure

**Provenance:** worked out on 2026-11-15 from JinnZ2/explorative-math `runs/golden_angle_seed0.json` (commit `80b9ed0`, CC0, co-authored). Status: a procedure. It is not enforced by `assess.py` and not in the routing table; run it on any claim that something is best, optimal, most efficient or most even. Co-authored.

## 1. What the card is for

"Best" has no value until a measure is named. A measure comes with three parts: what is measured, which direction counts as better, and over which population, window or range. An optimum is relative to all three. Change the measure and the optimum, or the ranking under it, can change.

The case that set this card: a packing can be judged by **volume** (how much room each point gets, read as nearest-neighbour distance) or by **gap fill** (how evenly the gaps are filled, read as the spread of those distances). These are different objectives over the same points.

## 2. Procedure

1. **Find the measure behind the word.** For each "best / optimal / most …" in the claim, name:
   - the quantity
   - the direction (higher or lower is better)
   - the range it was taken over
   If the material names none, record the measure as `UNDECLARED`.
2. **List the other measures the same data supports.** Use the ones a reader could reasonably mean, not every possible one.
3. **Rank under each measure the data allows.** Report whether these agree:
   - the optimum (first place)
   - the order of the rest
4. **State the claim with its measure.** "Golden is most even by `nn_cv` over 400 points" is complete. "Golden is best" is not.

## 3. Outputs

- The named measure, or `UNDECLARED`.
- A ranking table, one column per measure.
- Agreement of the optimum and of the order, stated separately.
- A claim of "best" with an `UNDECLARED` measure stays `UNDETERMINED`.
- A claim whose ranking flips under a measure the material also supports is graded only under its own measure, and the flip is recorded.

## 4. Worked case: explorative-math golden angle

`runs/golden_angle_seed0.json` ranks nine divergence angles by `nn_cv` (coefficient of variation of nearest-neighbour distances, lower is more even: gap fill). The same run also records `min_nn` (smallest nearest-neighbour distance, higher means more room per point: volume) and `mean_nn`. Ranked under each (DERIVED here from the run file's own rows):

| Rank | `nn_cv` (gap fill, low first) | `min_nn` (volume, high first) | `mean_nn` (high first) |
|---|---|---|---|
| 1 | golden | golden | golden |
| 2 | golden-0.1 | golden-0.1 | golden-0.1 |
| 3 | 137.0 | 138.0 | 138.0 |
| 4 | golden-0.5 | golden+0.5 | golden+0.5 |
| 5 | 138.0 | 137.0 | golden+0.1 |
| 6 | golden+0.5 | golden-0.5 | 137.0 |
| 7 | golden+0.1 | golden+0.1 | golden-0.5 |
| 8 | rational_3/8_turn | rational_3/8_turn | rational_3/8_turn |
| 9 | rational_2/5_turn | rational_2/5_turn | rational_2/5_turn |

- **The optimum agrees.** Golden is first under all three, and the two rational turns are last.
- **The order of the rest does not agree.** 137.0 is third by gap fill and fifth by volume. Among the ±0.5° perturbations and the whole-degree angles, the angles under golden (137.0, golden-0.5) do better on gap fill, and the angles over golden (138.0, golden+0.5) do better on volume. The ±0.1° pair keeps its places under all three.
- **Consequence for open question Q7 in the same repository.** Q7's own observation, that golden+0.1 ranks below golden+0.5, holds under all three measures. Which side of golden does better at ±0.5° does not: it flips between gap fill and volume. So any reading of an asymmetry about the golden angle has to name its measure. Q7's finite-N sweep should record all three.

## 5. Limits

- The worked case has one optimum that survives every measure. A case where the optimum itself moves would test the card harder.
- "Measures a reader could reasonably mean" is a judgement; record who chose them.
- The card does not choose a measure. It only refuses an unnamed one.
