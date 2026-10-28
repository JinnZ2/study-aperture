"""Reseed stochastic instrument-bias-sims claims. Run with cwd = sim/instrument-bias-sims.
Usage: python3 ibs_reseed.py <s1|s4|s9i|s9r> seed [seed...]
Seed injection is by keyword argument / wrapper; equivalent to editing the default seed
literal at the line named per claim."""
import sys, json, time
sys.path.insert(0, '.')
which = sys.argv[1]; seeds = list(map(int, sys.argv[2:]))
if which == 's1':
    import s1_encounter_denominator as m   # default seed=11 at s1_encounter_denominator.py:103
    for s in seeds:
        lo = m.sweep([0.001, 0.1], seed=s)
        hi = m.sweep([0.02], seed=s)[0]
        a = lo[0]['true_null_share'] > 0.95 and lo[0]['B_null_share'] == 0.0
        b = hi['B_mortality_escalate_share'] > hi['B_escalate_share'] > hi['true_escalate_share']
        print(json.dumps({"seed": s, "true_null_f0.001": lo[0]['true_null_share'], "B_null_f0.001": lo[0]['B_null_share'],
              "f0.02_true_escl": hi['true_escalate_share'], "f0.02_B_escl": hi['B_escalate_share'],
              "f0.02_B_mort_escl": hi['B_mortality_escalate_share'], "null_part": a, "product_part": b, "ok": a and b}))
elif which == 's4':
    import s4_antler_calibration as m      # default seed=3 at s4_antler_calibration.py:186
    orig = m.engagement_series
    for s in seeds:
        m.engagement_series = lambda arm, floor=0.0, n=400, seed=None, _s=s: orig(arm, floor=floor, n=n, seed=_s)
        ac = m.arm_comparison()
        r = ac['trend_ratio']; sp = ac['arms']['arm_pat']['A_spread']
        print(json.dumps({"seed": s, "trend_ratio": r, "trend_ratio_1dp": round(r, 1), "arm_pat_spread": sp,
              "magnitude_ok": round(r, 1) == 9.3, "direction_ok": r > 5.0 and sp < 0.15}))
elif which == 's9i':
    import s9_corpus_position_filter as m  # population seed=17 at s9_corpus_position_filter.py:220; corpus seed=23 at :176
    origc = m.corpus
    for s in seeds:
        m.corpus = (lambda pop, seed=None, _s=s: origc(pop, seed=_s + 6)) if s != 17 else origc
        rows = m.interaction_check(seed=s)
        ex = [round(r['excess'], 4) for r in rows]
        print(json.dumps({"seed": s, "corpus_seed": 23 if s == 17 else s + 6, "excess_by_coupling": dict(zip(["0.0","0.3","0.5","0.7","0.9"], ex)),
              "max_excess": max(ex), "magnitude_ok": round(max(ex), 2) == 1.85, "direction_ok": ex[-1] > 1.0 and ex[-1] > ex[0]}))
elif which == 's9r':
    import s9_corpus_position_filter as m  # default seed=31 at s9_corpus_position_filter.py:287
    orig = m.relevance_test
    for s in seeds:
        m.relevance_test = lambda w, n=3000, coupling=0.7, seed=None, _s=s: orig(w, n=n, coupling=coupling, seed=_s)
        rc = m.relevance_crossover()
        pk = rc['peak_content_correlation']
        print(json.dumps({"seed": s, "peak_content_corr": pk, "content_overtakes_at": rc['content_overtakes_at'], "ok": pk < 0.2}))
