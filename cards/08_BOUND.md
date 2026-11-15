# Card 08 — Bound and resolution leak

**Provenance:** worked out on 2026-11-15 in JinnZ2/explorative-math, `open_questions.md` Q12 (commit `80b9ed0`, CC0, co-authored). The code read is `toolkit/probes.py` and `compare/cross.py`. Status: a procedure taken from one case. It is not enforced by `assess.py` and not in the routing table; run it on any claim whose evidence is an instrument reading. Co-authored.

## 1. What the card is for

An instrument can only report values inside its own bounds: a range it searches, a tolerance, a step size, a rounding, an origin, a sample size. A reading taken at a bound can be the bound speaking rather than the object. This is a **resolution leak**: the result records the instrument, and is read as a property of what was measured.

The usual mistake is to check the one bound you already suspect and stop there. A leak can come through any of them.

## 2. Procedure

1. **List every bound of the instrument**, from its code or methods, not from memory. For each one, record:
   - the parameter
   - its value
   - where it is set (file and line, or methods section)
2. **For each bound, ask whether the reading could change if the bound moved.** Mark it one of:
   - `TESTED`: the reading was re-taken at another value. Record both values.
   - `NOT_TESTED`
   - `CANNOT_MATTER`: give the reason.
3. **Test every bound marked `NOT_TESTED` that the claim depends on**, not only the suspected one. The cheapest test is a known-answer input: an object whose true value lies outside the bound, or between two steps of it.
4. **State the reading inside its bounds.** "k = [2]" is incomplete. "k = [2] for k in 2..12 at tolerance 1e-6 about the centroid" is complete.

## 3. Outputs

- A bound list, one row per parameter, each with its test state.
- The reading restated with its bounds.
- For a claim resting on the reading:
  - while a bound it depends on is `NOT_TESTED`, the claim cannot carry `SUPPORTED`, `CONTRADICTED` or `MEASURED_ABSENT` on the strength of that reading;
  - record it as `UNDETERMINED`, or as the bounded statement.
  - A missed bound is an `E4_UNCHECKED_OBSERVER` miss (Card 06 section 4): the instrument's calibration went unchecked.

## 4. Worked case: explorative-math Q12

Build B's `rotational_symmetry` returned the same list for both builds' φ unions on all 8 frames (`compare/runs/phi_scale_vs_phi_scale_rotate.jsonl`), although the unions differ: 16 against 8 distinct directions on cross-polytope frames 1–3. The suspected bound was the order range. Listing all of them:

| Bound | Value | Where | Could it hide the difference? | State |
|---|---|---|---|---|
| order range | k in 2..12 | `toolkit/probes.py`, `rotational_symmetry(k_max=12)` | yes: a 16-fold set reads only as its divisors ≤ 12 | `NOT_TESTED` |
| tolerance | 1e-6 × the set's radius | `rel_tol=1e-6`, `_scale_of` | yes: two orders that differ within the tolerance read the same | `NOT_TESTED` |
| centre | the centroid | `rotational_symmetry`, `P.centroid` | yes, for a set not symmetric about its centroid | `NOT_TESTED` |
| plane | coordinates (0, 1) only | `P.rotate(pts, 0, 1, ...)` | not for 2D unions; would for higher dimensions | `CANNOT_MATTER` here: the unions are 2D |
| direction count | rounding to 9 decimals | `compare/cross.py`, `round(x, 9)` | yes: it sets the "16 vs 8" itself | `NOT_TESTED` |
| mirror resolution | 360 axes (0.5° steps over 180°) | `mirror_symmetry(n_axes=360)` | not used in the k comparison | `CANNOT_MATTER` for Q12 |

Reading inside its bounds: "both unions are k-fold for the same k in 2..12, at tolerance 1e-6 about the centroid." That reading does not separate "the orders are equal" from "the probe cannot see the difference". Q12 stays PROPOSED until its known-answer run (regular k-gons for k = 5, 8, 13, 16, 24) tests the order range and the tolerance together.

## 5. Limits

- One worked case; the procedure is not yet checked against a second instrument.
- Listing bounds from code finds the bounds the code names. A bound set by the data, such as the finite N in explorative-math Q7, has to be found by asking what the reading would do as N grows.
- The card does not say which bound leaked, only which ones are untested.
