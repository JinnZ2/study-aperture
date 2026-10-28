# reseed the observer-exclusion Monte Carlo functions (imports from the copy; no file edits)
import sys, statistics as st; sys.path.insert(0, sys.argv[1])
import archival_bias as ab, v2_check as v2
S = range(1, 21)
def rng(v): return (round(min(v),3), round(st.median(v),3), round(max(v),3))
a10 = [ab.attenuation(10, seed=s) for s in S]
print("att10 mean", rng([x["observed_mean"] for x in a10]), "P>0", rng([x["frac_positive"] for x in a10]), "neg mean", sum(x["observed_mean"]<0 for x in a10), "P<0.5", sum(x["frac_positive"]<0.5 for x in a10))
a20 = [ab.attenuation(20, seed=s) for s in S]
print("att20 mean", rng([x["observed_mean"] for x in a20]), "P>0", rng([x["frac_positive"] for x in a20]))
f0 = [ab.f4_bias(0, seed=s) for s in S]
print("f4 gap0 field_first", rng([x["field_first"] for x in f0]))
def gap_needed(seed):
    for g in range(80):
        if ab.f4_bias(g, trials=4000, seed=seed)["excluded_first"] >= 0.5: return g
print("gap_needed", [gap_needed(s) for s in S])
cs = [v2.correction_sign(seed=s) for s in S]
print("corr median_delta", rng([x["median_delta"] for x in cs]), "spec_minus", rng([x["spec_minus"] for x in cs]), "plus", rng([x["plus"] for x in cs]), "spec worse than raw", sum(abs(x["spec_minus"]-20)>abs(x["L_raw"]-20) for x in cs))
fm = [v2.f4_term_mismatch(seed=s) for s in S]
print("f4mm delta_gap", rng([x["delta_gap"] for x in fm]), "field_first", rng([x["field_first_rate"] for x in fm]), "first_ex", rng([x["first_ex_median"] for x in fm]), "first_fi", rng([x["first_fi_median"] for x in fm]))
