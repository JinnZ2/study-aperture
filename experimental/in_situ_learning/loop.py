"""In-situ learning loop: a constructed toy for measuring what such loops can and cannot show.

CC0. Python 3 stdlib only, no network. Nothing here models a spin system or any real
instrument. Every function, constant and noise level is CONSTRUCTED so that the ground
truth is known; the toy exists to make the method questions in GAPS.md measurable.

The shape borrowed from Jensen et al. (arXiv:2603.19448): a parameterised procedure x
is run on the real instrument, one noisy evaluation at a time; a Gaussian-process
surrogate with an expected-improvement acquisition proposes the next x; a simulation
of the system exists but omits terms.

    truth on instrument k:   f_k(x) = g(x) + m(x) + h_k(x)          (noise sigma per evaluation)
    simulation (in silico):  g(x)                                  (omits m and h_k)

    g    physics the simulation contains
    m    physics the simulation omits, shared by every instrument (sample-side; e.g. line width)
    h_k  a term belonging to instrument k only (resonator, transients, MW inhomogeneity)

    python3 loop.py              # run experiments E1-E5 and print the results
    python3 loop.py selftest     # small, fast known-answer checks
"""

import math
import random
import sys

DIM = 2


def bump(x, c, w):
    return math.exp(-sum((a - b) ** 2 for a, b in zip(x, c)) / (2 * w * w))


# ---- constructed truth -------------------------------------------------------

G = [(1.0, (0.30, 0.70), 0.12), (0.8, (0.75, 0.30), 0.10)]
M_CENTER, M_WIDTH = (0.55, 0.55), 0.15
H_CENTER = {"A": (0.82, 0.82), "B": (0.18, 0.18)}
H_WIDTH = 0.08


def g(x):
    return sum(a * bump(x, c, w) for a, c, w in G)


def truth(x, model_error, inst_amp, inst="A"):
    return (g(x) + model_error * bump(x, M_CENTER, M_WIDTH)
            + inst_amp * bump(x, H_CENTER[inst], H_WIDTH))


GRID = [(i / 60, j / 60) for i in range(61) for j in range(61)]


def grid_argmax(f):
    return max(GRID, key=f)


# ---- Gaussian process + expected improvement (stdlib) -------------------------

def _kern(a, b, ls):
    return math.exp(-sum((p - q) ** 2 for p, q in zip(a, b)) / (2 * ls * ls))


def _cholesky(K):
    n = len(K)
    L = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1):
            s = K[i][j] - sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                L[i][j] = math.sqrt(max(s, 1e-12))
            else:
                L[i][j] = s / L[j][j]
    return L


def _solve_lower(L, b):
    y = []
    for i in range(len(L)):
        y.append((b[i] - sum(L[i][k] * y[k] for k in range(i))) / L[i][i])
    return y


def _solve_upper_t(L, y):
    n = len(L)
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (y[i] - sum(L[k][i] * x[k] for k in range(i + 1, n))) / L[i][i]
    return x


class GP:
    def __init__(self, X, y, ls=0.12, noise=0.05):
        self.X, self.ls = X, ls
        self.mu, sd = sum(y) / len(y), (max(y) - min(y)) or 1.0
        self.sd = sd
        ys = [(v - self.mu) / sd for v in y]
        nv = (noise / sd) ** 2 + 1e-6
        K = [[_kern(a, b, ls) + (nv if i == j else 0.0) for j, b in enumerate(X)]
             for i, a in enumerate(X)]
        self.L = _cholesky(K)
        self.alpha = _solve_upper_t(self.L, _solve_lower(self.L, ys))

    def predict(self, x):
        k = [_kern(x, a, self.ls) for a in self.X]
        mean = sum(p * q for p, q in zip(k, self.alpha))
        v = _solve_lower(self.L, k)
        var = max(1.0 - sum(t * t for t in v), 1e-12)
        return self.mu + self.sd * mean, self.sd * math.sqrt(var)


def _ei(mean, sd, best, xi=0.01):
    z = (mean - best - xi) / sd
    cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    pdf = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return (mean - best - xi) * cdf + sd * pdf


def run_loop(f_true, sigma, budget, rng, method="bayes", n_init=4, n_cand=120):
    """One optimisation run on noisy evaluations of f_true. Returns the evaluated
    points, observed values, and the recommendation (best OBSERVED value, as reported
    in the source paper)."""
    measure = lambda x: f_true(x) + rng.gauss(0, sigma)
    X, Y = [], []
    for _ in range(n_init if method == "bayes" else budget):
        x = (rng.random(), rng.random())
        X.append(x); Y.append(measure(x))
    while method == "bayes" and len(X) < budget:
        gp = GP(X, Y, noise=max(sigma, 1e-3))
        best_i = max(range(len(Y)), key=Y.__getitem__)
        cands = [(rng.random(), rng.random()) for _ in range(n_cand)]
        cands += [tuple(min(1, max(0, X[best_i][d] + rng.gauss(0, 0.05))) for d in range(DIM))
                  for _ in range(n_cand // 4)]
        best_obs = Y[best_i]
        x = max(cands, key=lambda c: _ei(*gp.predict(c), best_obs))
        X.append(x); Y.append(measure(x))
    i = max(range(len(Y)), key=Y.__getitem__)
    return {"X": X, "Y": Y, "x_rec": X[i], "y_rec_observed": Y[i]}


# ---- experiments ---------------------------------------------------------------

def e1_in_situ_vs_in_silico(seeds, budget, conds):
    """Regret on instrument A of the in-silico optimum vs the in-situ recommendation."""
    x_sil = grid_argmax(g)
    rows = []
    for model_error, sigma in conds:
        f = lambda x: truth(x, model_error, 0.6, "A")
        best = f(grid_argmax(f))
        reg_sil = best - f(x_sil)
        reg_is = [best - f(run_loop(f, sigma, budget, random.Random(s))["x_rec"]) for s in seeds]
        rows.append({"model_error": model_error, "sigma": sigma,
                     "regret_in_silico": round(reg_sil, 3),
                     "regret_in_situ_median": round(sorted(reg_is)[len(reg_is) // 2], 3),
                     "in_situ_beats_in_silico": sum(r < reg_sil for r in reg_is)})
    return {"x_in_silico": x_sil, "n_seeds": len(seeds), "rows": rows}


def e2_transfer(seeds, budget, sigma, inst_amps, model_error=1.2):
    """Learn on instrument A, measure on instrument B. Of the gain over the in-silico
    optimum on A, how much is still there on B?"""
    x_sil = grid_argmax(g)
    rows = []
    for b in inst_amps:
        fA = lambda x: truth(x, model_error, b, "A")
        fB = lambda x: truth(x, model_error, b, "B")
        gainA, gainB = [], []
        for s in seeds:
            x = run_loop(fA, sigma, budget, random.Random(s))["x_rec"]
            gainA.append(fA(x) - fA(x_sil)); gainB.append(fB(x) - fB(x_sil))
        mA, mB = sum(gainA) / len(seeds), sum(gainB) / len(seeds)
        rows.append({"instrument_term": b, "gain_on_A": round(mA, 3), "gain_on_B": round(mB, 3),
                     "retained_on_B": None if mA <= 0 else round(mB / mA, 2)})
    return {"model_error": model_error, "sigma": sigma, "rows": rows}


def e3_winners_curse(seeds, budget, sigmas, model_error=0.6):
    """Best OBSERVED value minus the true value at that point."""
    rows = []
    for sigma in sigmas:
        f = lambda x: truth(x, model_error, 0.6, "A")
        over = []
        for s in seeds:
            r = run_loop(f, sigma, budget, random.Random(s))
            over.append(r["y_rec_observed"] - f(r["x_rec"]))
        rows.append({"sigma": sigma, "mean_overstatement": round(sum(over) / len(over), 3),
                     "runs_overstated": sum(o > 0 for o in over), "n": len(over)})
    return rows


def e4_single_run_comparison(seeds, budget, sigma, model_error=0.6):
    """Bayesian vs random search, one run each: how often does a single pair reverse
    the ordering of the medians?"""
    f = lambda x: truth(x, model_error, 0.6, "A")
    bo = [f(run_loop(f, sigma, budget, random.Random(s))["x_rec"]) for s in seeds]
    rs = [f(run_loop(f, sigma, budget, random.Random(1000 + s), method="random")["x_rec"])
          for s in seeds]
    med = lambda v: sorted(v)[len(v) // 2]
    bo_better = med(bo) >= med(rs)
    pairs = [(a, b) for a in bo for b in rs]
    reversed_ = sum((a < b) if bo_better else (a > b) for a, b in pairs)
    return {"budget": budget, "sigma": sigma, "median_true_bayes": round(med(bo), 3),
            "median_true_random": round(med(rs), 3), "range_bayes": (round(min(bo), 3), round(max(bo), 3)),
            "range_random": (round(min(rs), 3), round(max(rs), 3)),
            "single_pairs_reversing_median_order": f"{reversed_}/{len(pairs)}"}


def e5_mean_over_offsets():
    """The paper's objective is a mean over offsets. Compare the mean-optimal and the
    worst-case-optimal procedure: what does the mean hide?  Offsets shift g along x0."""
    offsets = [-0.12, -0.06, 0.0, 0.06, 0.12]
    def per_offset(x):
        return [g((min(1, max(0, x[0] + o)), x[1])) - 0.9 * bump(x, (0.33 + 2 * o, 0.7), 0.03)
                for o in offsets]
    mean_f = lambda x: sum(per_offset(x)) / len(offsets)
    min_f = lambda x: min(per_offset(x))
    xm, xw = grid_argmax(mean_f), grid_argmax(min_f)
    r2 = lambda x: tuple(round(v, 3) for v in x)
    return {"offsets": offsets,
            "mean_optimal": {"x": r2(xm), "mean": round(mean_f(xm), 3), "worst_offset": round(min_f(xm), 3)},
            "worst_case_optimal": {"x": r2(xw), "mean": round(mean_f(xw), 3), "worst_offset": round(min_f(xw), 3)}}


# ---- render / selftest ---------------------------------------------------------

def run_all(seeds=range(8), budget=30):
    return {
        "E1": e1_in_situ_vs_in_silico(seeds, budget, [(0.0, 0.05), (0.6, 0.05), (1.2, 0.05),
                                                      (1.2, 0.3)]),
        "E2": e2_transfer(seeds, budget, 0.05, [0.0, 0.8, 1.6]),
        "E3": e3_winners_curse(seeds, budget, [0.05, 0.15, 0.3]),
        "E4": e4_single_run_comparison(seeds, budget, 0.15),
        "E5": e5_mean_over_offsets(),
    }


def render(r):
    out = ["In-situ learning toy (CONSTRUCTED; not a model of any instrument)", ""]
    e1 = r["E1"]
    out.append(f"E1 in situ vs in silico on instrument A ({e1['n_seeds']} seeds, in-silico optimum {e1['x_in_silico']})")
    out.append("   model_error  sigma  regret_in_silico  regret_in_situ(median)  in_situ_beats_in_silico")
    for row in e1["rows"]:
        out.append(f"   {row['model_error']:>11}  {row['sigma']:>5}  {row['regret_in_silico']:>16}  "
                   f"{row['regret_in_situ_median']:>22}  {row['in_situ_beats_in_silico']:>13}/{e1['n_seeds']}")
    e2 = r["E2"]
    out += ["", f"E2 learned on instrument A, measured on B (model_error {e2['model_error']}, sigma {e2['sigma']})",
            "   instrument_term  gain_on_A  gain_on_B  retained_on_B"]
    for row in e2["rows"]:
        out.append(f"   {row['instrument_term']:>15}  {row['gain_on_A']:>9}  {row['gain_on_B']:>9}  {str(row['retained_on_B']):>13}")
    out += ["", "E3 best observed value minus true value at the recommended point",
            "   sigma  mean_overstatement  runs_overstated"]
    for row in r["E3"]:
        out.append(f"   {row['sigma']:>5}  {row['mean_overstatement']:>18}  {row['runs_overstated']:>10}/{row['n']}")
    e4 = r["E4"]
    out += ["", f"E4 one run each, Bayesian vs random (budget {e4['budget']}, sigma {e4['sigma']})",
            f"   median true value: bayes {e4['median_true_bayes']} range {e4['range_bayes']}; "
            f"random {e4['median_true_random']} range {e4['range_random']}",
            f"   single pairs reversing the median ordering: {e4['single_pairs_reversing_median_order']}"]
    e5 = r["E5"]
    out += ["", f"E5 mean over offsets {e5['offsets']} vs worst offset",
            f"   mean-optimal:       x {e5['mean_optimal']['x']}  mean {e5['mean_optimal']['mean']}  worst offset {e5['mean_optimal']['worst_offset']}",
            f"   worst-case-optimal: x {e5['worst_case_optimal']['x']}  mean {e5['worst_case_optimal']['mean']}  worst offset {e5['worst_case_optimal']['worst_offset']}"]
    return "\n".join(out)


def selftest():
    checks, bad = 0, []

    def ok(cond, name):
        nonlocal checks
        checks += 1
        if not cond:
            bad.append(name)

    # GP interpolates a noiseless point and reverts toward the mean far away
    gp = GP([(0.2, 0.2), (0.8, 0.8)], [1.0, 0.0], ls=0.1, noise=1e-3)
    m, s = gp.predict((0.2, 0.2))
    ok(abs(m - 1.0) < 1e-2 and s < 0.05, "gp interpolates")
    m, s = gp.predict((0.5, 0.0))
    ok(s > 0.9 * gp.sd, "gp uncertain far from data")
    ok(abs(_ei(1.0, 1e-9, 0.0, 0.0) - 1.0) < 1e-6, "ei of a certain improvement")
    # truth decomposition
    ok(abs(truth((0.3, 0.7), 0, 0) - g((0.3, 0.7))) < 1e-12, "truth reduces to g")
    ok(truth(H_CENTER["A"], 0, 1, "A") > truth(H_CENTER["A"], 0, 1, "B"), "instrument term is local")
    # the loop finds the optimum of a noiseless single bump better than its start
    f = lambda x: bump(x, (0.6, 0.4), 0.1)
    r = run_loop(f, 0.0, 20, random.Random(1))
    ok(f(r["x_rec"]) > 0.9, "bayes loop finds a single bump")
    ok(len(r["X"]) == 20, "budget respected")
    # with zero noise, the observed best equals the true value (no winner's curse)
    ok(abs(r["y_rec_observed"] - f(r["x_rec"])) < 1e-12, "no overstatement at sigma 0")
    # E5: the worst-case optimum is not worse at its worst offset than the mean optimum
    e5 = e5_mean_over_offsets()
    ok(e5["worst_case_optimal"]["worst_offset"] >= e5["mean_optimal"]["worst_offset"], "maximin dominates on worst offset")
    ok(e5["mean_optimal"]["mean"] >= e5["worst_case_optimal"]["mean"], "mean optimum dominates on mean")
    print(f"checks: {checks}   failed: {len(bad)}")
    for b in bad:
        print(f"FAILED {b}")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["selftest"]:
        sys.exit(selftest())
    print(render(run_all()))
