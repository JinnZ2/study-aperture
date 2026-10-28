"""Recompute the arithmetic in Almudevar & Almudevar (2026), arXiv:2602.15697v1.

CC0. Python 3 stdlib only, no network. Every input below is transcribed from the
paper's HTML rendering (https://arxiv.org/html/2602.15697v1); the section or table
it came from is named beside it. Nothing here says whether the paper is right.

    python3 recompute.py            # print every check
    python3 recompute.py selftest   # exit 1 if any recorded result changes
"""

import math
import sys

URL = "https://arxiv.org/html/2602.15697v1"


# ---- the paper's model (Section 2.1, equations 2 and 3) -------------------

def ppv(pi, alpha, beta):
    """Eq. 2: Odds(PPV) = ((1 - beta) / alpha) * Odds(pi)."""
    if pi >= 1:
        return 1.0
    odds = (1 - beta) / alpha * (pi / (1 - pi))
    return odds / (1 + odds)


def ppv_obs(p, alpha_star, beta_star):
    """Eq. 3: PPV_obs ~ PPV (1 - beta*) + (1 - PPV) alpha*."""
    return p * (1 - beta_star) + (1 - p) * alpha_star


def pi_for_ppv(p, alpha, beta):
    """Invert eq. 2: the prevalence pi that gives a stated PPV."""
    odds_pi = (p / (1 - p)) * alpha / (1 - beta)
    return odds_pi / (1 + odds_pi)


def pi_for_obs(obs, alpha, beta, alpha_star, beta_star):
    """Invert eqs. 3 and 2: the prevalence that reproduces an observed rate."""
    p = (obs - alpha_star) / (1 - alpha_star - beta_star)   # eq. 4
    if p <= 0:
        return 0.0
    if p >= 1:
        return 1.0
    return pi_for_ppv(p, alpha, beta)


# ---- exact statistics, stdlib ---------------------------------------------

def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def clopper_pearson(k, n, conf=0.95):
    a = (1 - conf) / 2

    def solve(f):
        lo, hi = 0.0, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if f(mid):
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2

    lower = 0.0 if k == 0 else solve(lambda p: 1 - binom_cdf(k - 1, n, p) < a)
    upper = 1.0 if k == n else solve(lambda p: binom_cdf(k, n, p) > a)
    return lower, upper


def fisher_two_sided(a, b, c, d):
    """2x2 table [[a, b], [c, d]]; sums probabilities <= the observed one."""
    r1, c1, n = a + b, a + c, a + b + c + d

    def prob(x):
        return math.comb(c1, x) * math.comb(n - c1, r1 - x) / math.comb(n, r1)

    p_obs = prob(a)
    lo, hi = max(0, r1 - (n - c1)), min(r1, c1)
    return sum(prob(x) for x in range(lo, hi + 1) if prob(x) <= p_obs * (1 + 1e-9))


# ---- checks ----------------------------------------------------------------

ALPHA, BETA = 0.05, 0.1      # Table 1 caption: alpha* = alpha = 0.05, beta* = beta = 0.1

TABLE1 = [  # case, pi, printed PPV, printed PPV_obs  (Table 1)
    (1, 1.00, 1.000, 0.900),
    (2, 0.50, 0.947, 0.808),
    (3, 0.25, 0.857, 0.776),
    (4, 0.05, 0.486, 0.439),
]

TABLE4 = {  # effect type: (No, Yes)   (Table 4)
    "binomial test": (0, 1), "contrast": (1, 0), "correlation": (4, 2),
    "focused interaction contrast": (1, 0), "interaction": (29, 8),
    "main effect": (26, 23), "regression": (0, 1), "trend": (1, 0),
}


def run():
    r = {}

    # R1 Table 1: PPV column and PPV_obs column under the stated parameters
    rows = []
    for case, pi, p_print, obs_print in TABLE1:
        p = ppv(pi, ALPHA, BETA)
        obs_010 = ppv_obs(p, ALPHA, 0.10)
        obs_015 = ppv_obs(p, ALPHA, 0.15)
        rows.append((case, round(p, 3), p_print, round(obs_010, 3), round(obs_015, 3), obs_print))
    r["table1"] = rows

    # R2 Table 4 totals
    no = sum(v[0] for v in TABLE4.values())
    yes = sum(v[1] for v in TABLE4.values())
    other = {k: v for k, v in TABLE4.items() if k not in ("main effect", "interaction")}
    r["table4"] = {
        "total": no + yes, "yes": yes,
        "other_rows_total": sum(sum(v) for v in other.values()),
        "other_rows_yes": sum(v[1] for v in other.values()),
    }

    # R3 Fisher exact: main effect 23/49 vs interaction 8/37 (Section 3.5: P = 0.023)
    r["fisher_main_vs_interaction"] = round(fisher_two_sided(23, 26, 8, 29), 4)

    # R4 Clopper-Pearson intervals the paper reports
    r["cp_osc_35_97"] = tuple(round(x, 3) for x in clopper_pearson(35, 97))   # Intro: (26.6%, 46.2%)
    r["cp_camerer_11_18"] = tuple(round(x, 3) for x in clopper_pearson(11, 18))  # 3.6: (0.357, 0.827)

    # R5 Section 3.5 / 3.6 predictions from eq. 3
    r["pred_main"] = round(ppv_obs(ppv(0.25, ALPHA, BETA), ALPHA, 0.468), 3)       # paper 0.463
    r["pred_interaction"] = round(ppv_obs(ppv(0.05, ALPHA, BETA), ALPHA, 0.468), 3)  # paper 0.284
    r["pred_camerer"] = round(ppv_obs(ppv(0.25, ALPHA, BETA), ALPHA, 0.441), 3)    # paper 0.486

    # R6 Identification: which prevalence reproduces the OSC rate, with and without
    #     the paper's corrected type II error? (35/97 point; CP interval endpoints)
    lo, hi = clopper_pearson(35, 97)
    ident = {}
    for label, bstar in (("beta*=0.08 (OSC reported)", 0.08), ("beta*=0.468 (paper)", 0.468)):
        ident[label] = tuple(round(pi_for_obs(x, ALPHA, BETA, ALPHA, bstar), 3) for x in (lo, 35 / 97, hi))
    r["pi_that_fits_osc"] = ident

    # R8 Camerer 11/18 under the paper's pi = 0.25 with OSC's reported beta* instead
    r["camerer_no_bias"] = round(ppv_obs(ppv(0.25, ALPHA, BETA), ALPHA, 0.08), 3)

    # R7 ML-RP: the prevalence implied if 11/13 is read as PPV (as Section 3.6 does)
    r["pi_from_mlrp"] = round(pi_for_ppv(11 / 13, ALPHA, BETA), 3)

    return r


EXPECTED = {
    "table1": [(1, 1.0, 1.0, 0.9, 0.85, 0.9), (2, 0.947, 0.947, 0.855, 0.808, 0.808),
               (3, 0.857, 0.857, 0.779, 0.736, 0.776), (4, 0.486, 0.486, 0.464, 0.439, 0.439)],
    "table4": {"total": 97, "yes": 35, "other_rows_total": 11, "other_rows_yes": 4},
    "fisher_main_vs_interaction": 0.0228,
    "cp_osc_35_97": (0.266, 0.465),
    "cp_camerer_11_18": (0.357, 0.827),
    "pred_main": 0.463, "pred_interaction": 0.284, "pred_camerer": 0.486,
    "pi_that_fits_osc": {"beta*=0.08 (OSC reported)": (0.018, 0.03, 0.048),
                         "beta*=0.468 (paper)": (0.043, 0.092, 0.255)},
    "pi_from_mlrp": 0.234,
    "camerer_no_bias": 0.796,
}


def render(r):
    out = [f"Recompute: Almudevar & Almudevar 2026, {URL}", ""]
    out.append("R1  Table 1 (alpha* = alpha = 0.05, beta = 0.1 as captioned)")
    out.append("    case  PPV calc  PPV print  obs@beta*=0.10  obs@beta*=0.15  obs print")
    for case, p, pp, o10, o15, op in r["table1"]:
        out.append(f"    {case:>4}  {p:>8.3f}  {pp:>9.3f}  {o10:>14.3f}  {o15:>14.3f}  {op:>9.3f}")
    out.append("    PPV column reproduces. PPV_obs: row 1 matches beta* = 0.10 (caption), row 3")
    out.append("    is within 0.003 of it; rows 2 and 4 match beta* = 0.15, not the caption.")
    out.append("    Table 1 is illustrative;")
    out.append("    the Section 3.5 fit does not use its PPV_obs column.")
    t = r["table4"]
    out += ["", f"R2  Table 4: {t['yes']}/{t['total']} replicated (matches 35/97); rows other than main",
            f"    effect / interaction: {t['other_rows_yes']}/{t['other_rows_total']} (not discussed in the text)."]
    out += ["", f"R3  Fisher exact, main 23/49 vs interaction 8/37: p = {r['fisher_main_vs_interaction']}"
            " (paper: 0.023)"]
    out += ["", f"R4  Clopper-Pearson 35/97: {r['cp_osc_35_97']} (Section 3.5: 0.266-0.465; the Intro's quoted",
            "    OSC interval 26.6%-46.2% is not Clopper-Pearson; 0.003 apart at the top)",
            f"    Clopper-Pearson 11/18: {r['cp_camerer_11_18']} (paper: 0.357, 0.827)"]
    out += ["", "R5  Predictions from eq. 3:",
            f"    main effects, pi 0.25, beta* 0.468:  {r['pred_main']}  (paper 0.463, observed 0.469)",
            f"    interactions, pi 0.05, beta* 0.468:  {r['pred_interaction']}  (paper 0.284, observed 0.216)",
            f"    Camerer, pi 0.25, beta* 0.441:       {r['pred_camerer']}  (paper 0.486, observed 0.611)"]
    out += ["", "R6  Prevalence pi that reproduces OSC 35/97 (CP lower, point, CP upper):"]
    for k, v in r["pi_that_fits_osc"].items():
        out.append(f"    {k:<28} pi = {v[0]:.3f}  {v[1]:.3f}  {v[2]:.3f}")
    out.append("    Both the paper's corrected beta* and OSC's reported beta* reproduce 35/97;")
    out.append("    they need different pi. pi is not measured in the paper, so the observed rate")
    out.append("    does not by itself pick between 'protocol bias' and 'low prevalence'.")
    out += ["", f"R7  Reading ML-RP 11/13 as PPV (Section 3.6) implies pi = {r['pi_from_mlrp']};",
            "    pi = 0.25 was labelled 'consistent with ML-RP' (Table 1), so the 0.846 vs 0.857",
            "    agreement in Section 3.6 is the calibration, not a separate test."]
    lo, hi = r["cp_camerer_11_18"]
    out += ["", f"R8  Camerer 11/18 with pi 0.25 and OSC's beta* 0.08 (no bias): {r['camerer_no_bias']}",
            f"    with the paper's beta* 0.441: {r['pred_camerer']}. Both lie inside ({lo}, {hi});",
            "    at n = 18 the Camerer rate does not separate the two readings."]
    return "\n".join(out)


def selftest():
    got = run()
    bad = [k for k in EXPECTED if got[k] != EXPECTED[k]]
    for k in bad:
        print(f"CHANGED {k}: expected {EXPECTED[k]!r}, got {got[k]!r}")
    # known answers for the helpers
    assert abs(ppv(0.5, 0.05, 0.1) - 18 / 19) < 1e-12
    assert abs(pi_for_ppv(ppv(0.3, 0.05, 0.1), 0.05, 0.1) - 0.3) < 1e-12
    assert abs(fisher_two_sided(1, 0, 0, 1) - 1.0) < 1e-12
    print(f"checks: {len(EXPECTED) + 3}   failed: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.exit(selftest())
    print(render(run()))
