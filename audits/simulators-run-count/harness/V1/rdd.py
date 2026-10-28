import sys, json
sys.path.insert(0, sys.argv[1])
import residual as R
orig = R._noise
for off in map(int, sys.argv[2:]):
    R._noise = lambda n, amp, seed, off=off: orig(n, amp, seed + off)
    f = R.fixture("F4"); r = R.analyse(f, 0.5, "stipulated")
    k = R.fixture("F4"); k.correction_status = R.UNADJUSTED; rk = R.analyse(k, 0.5, "stipulated")
    # recompute s2 for the unknown series for precondition
    s2 = R.conditional_lean(f)
    sym = not s2["any_lean"]
    print(json.dumps(dict(f4_seed=44+off, symmetric_by_instrument=sym, lean_rows=[x["row"]+":"+x["against"] for x in s2["ranked"] if x.get("lean")]+(["pooled"] if s2["pooled"].get("lean") else []),
        verdict_unknown=r["verdict"], verdict_known=rk["verdict"],
        literal_selftest=(r["verdict"]=="UNINTERPRETABLE" and rk["verdict"] in (R.NO_ACTION,R.CHECK_S2A)),
        not_clean_unknown= r["verdict"] not in (R.NO_ACTION,R.CHECK_S2A),
        conditional_ok=(not sym) or (r["verdict"]=="UNINTERPRETABLE" and rk["verdict"] in (R.NO_ACTION,R.CHECK_S2A)))))
