# Card 08 — Bound and resolution leak

**Provenance:** worked out on 2026-11-15 in JinnZ2/explorative-math, `open_questions.md` Q12 (CC0, co-authored). The question and the code read (`toolkit/probes.py`, `compare/cross.py`) are at `main` `80b9ed0`. The bound tests are on `main` at `3b8e9ab` (merged 2026-11-15 from `claude/quasicrystal-projection-properties-448bx7`): `docs/resolution_leak.md` rows 2a–2c, `runs/symmetry_resolution_seed0.json`, `runs/mirror_sweep_seed0.json`. Status: a procedure taken from one case. It is not enforced by `assess.py`. It is routed by default for EMPIRICAL, REVIEW and SIMULATION (Card 00); run it on any claim whose evidence is an instrument reading. Co-authored.

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

Build B's `rotational_symmetry` returned the same list for both builds' φ unions on all 8 frames (`compare/runs/phi_scale_vs_phi_scale_rotate.jsonl`), although the unions differ: 16 against 8 distinct directions on cross-polytope frames 1–3. The suspected bounds were the order range and the tolerance. The bound tests at `3b8e9ab` tested both of those, plus the mirror probe's bounds:

| Bound | Value | Where | Tested at | State | Result (as logged) |
|---|---|---|---|---|---|
| order range | k in 2..`k_max` | `rotational_symmetry(k_max=12)` | 12 against 24 | `TESTED` | Known pair: a regular 8-gon and 16-gon both read `[2, 4, 8]` at 12, and `[2, 4, 8]` against `[2, 4, 8, 16]` at 24, so they separate. The unions: equal at both. |
| tolerance | relative to the set's radius | `rel_tol=1e-6` | 1e-6 against 1e-9 | `TESTED` | no output changed |
| centre | the centroid | `P.centroid` | — | `NOT_TESTED` | logged as not tested |
| plane | coordinates (0, 1) | `P.rotate(pts, 0, 1, ...)` | — | `CANNOT_MATTER` | the unions are 2D |
| direction count | rounding to 9 decimals | `compare/cross.py`, `round(x, 9)` | — | `NOT_TESTED` | sets the "16 against 8" count, not the probe's lists |
| mirror axes | grid of `n_axes` axes | `mirror_symmetry(n_axes=360)` | 360 against 720; tolerance 1e-6 against 1e-9; grid against no grid | `TESTED` | same readings at every setting |

Statuses as logged in `docs/resolution_leak.md`:
- **2a, known shapes: CONFIRMED (`k_max`); tolerance: no change.** Below the larger order, `k_max` made two different shapes read the same.
- **2b, the unions: not a leak at the bounds tested.** DERIVED there: a set of n points has no rotational order above n, and each union has 10 or 16 points, so `k_max` 24 covers every order they could have. The equal lists are not made by `k_max`.
- **2c, mirror on the unions: not a leak at the bounds tested.**
  - The mirror lists separate the unions on frame 0 only, for both shapes:
    - simplex frame 0: A has no axis; B has axes at 30, 90, 150°
    - cross-polytope frame 0: A has none; B has axes at 0, 45, 90, 135°
  - On the other 6 frames neither union shows a mirror.
  - Frame 0 is degenerate. Every rotation angle is zero there, so its points are the unrotated vertices.
  - A 360-frame sweep found a mirror on frame 0 only. That holds for the shape alone and for B's union; A's union showed a mirror on no frame.

Q12 itself stays PROPOSED as written: its test lists more shapes than the two that were run. Not tested, per the log: a coarser tolerance, a centre other than the centroid, other frames or shapes.

This is the card's point, in the run's own words: "The bound suspected is not always the bound that matters; test all logged bounds, not only the hypothesized one."

## 5. Limits

- One worked case; the procedure is not yet checked against a second instrument.
- Listing bounds from code finds the bounds the code names. A bound set by the data, such as the finite N in explorative-math Q7, has to be found by asking what the reading would do as N grows.
- The card does not say which bound leaked, only which ones are untested.
