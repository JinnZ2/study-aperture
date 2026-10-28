import sys, json
sys.path.insert(0, sys.argv[1])
import s1_encounter_denominator as m
mode = sys.argv[2]; seeds = list(map(int, sys.argv[3:]))
def row(f, tseed, oseed):
    tl = m.timeline(40, 400, f, tseed)
    a = m.observe_continuous(tl); b = m.observe_event(tl, 0.0, seed=oseed)
    bm = m.observe_event(tl, 0.0, mortality_weighted=True, seed=oseed)
    return dict(true_null=a["composition"]["NULL"], B_null=b["composition"]["NULL"],
        true_escl=a["composition"]["ESCALATE"], B_escl=b["composition"]["ESCALATE"],
        B_mort_escl=(bm["composition"] or {}).get("ESCALATE"), n_escl_ticks=a["counts"]["ESCALATE"])
for s in seeds:
    ts, os_ = (s, s) if mode == "joint" else (11, s)
    lo = row(0.001, ts, os_); hi = row(0.02, ts, os_)
    null_ok = lo["true_null"] > 0.95 and lo["B_null"] == 0.0
    prod_ok = hi["B_mort_escl"] is not None and hi["B_mort_escl"] > hi["B_escl"] > hi["true_escl"]
    print(json.dumps(dict(mode=mode, tl_seed=ts, obs_seed=os_, f001=lo, f002=hi, null_ok=null_ok, product_ok=prod_ok)))
