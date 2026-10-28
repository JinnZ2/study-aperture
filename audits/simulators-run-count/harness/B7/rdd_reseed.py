# run from residual-direction copy. Reseeds fixture noise: residual._noise(n,amp,seed) -> seed + OFF (residual.py:465)
import random, statistics as st, residual as R
orig=R._noise
res={k:[] for k in "fp s2a s2c rdd1 rdd4 rdd5_F1 rdd5_F2 rdd5_F3 rdd5 rdd6".split()}
offs=[0]+[1000*k for k in range(1,21)]
for off in offs:
    R._noise=lambda n,amp,seed,off=off: orig(n,amp,seed+off)
    r1=R.analyse(R.fixture("F1"),0.8,"s"); r2=R.analyse(R.fixture("F2"),0.01,"s"); r3=R.analyse(R.fixture("F3"),0.7,"s"); r4=R.analyse(R.fixture("F4"),0.5,"s")
    k=R.fixture("F4"); k.correction_status=R.UNADJUSTED; rk=R.analyse(k,0.5,"s")
    s2a=[r for r in r1["s2"]["rows"] if r["row"]=="S2a"][0]; s2c=[r for r in r1["s2"]["rows"] if r["row"]=="S2c"][0]
    res["fp"].append(r1["s2"]["pooled"]["fraction_positive"]); res["s2a"].append(s2a["standardized"]); res["s2c"].append(s2c["standardized"])
    res["rdd1"].append((not r1["s2"]["pooled"]["lean"]) and s2a["lean"])
    res["rdd4"].append(r2["verdict"]==R.LOG_AND_LEAVE and r2["s2"]["candidate"] is None)
    res["rdd5_F1"].append(r1["s4"]["state"]); res["rdd5_F2"].append(r2["s4"]["state"]); res["rdd5_F3"].append(r3["s4"]["state"])
    res["rdd5"].append(r1["s4"]["state"]==R.STABLE and r2["s4"]["state"]==R.STABLE and r3["s4"]["state"]==R.GROWING)
    res["rdd6"].append(r4["verdict"]==R.UNINTERPRETABLE and rk["verdict"] in (R.NO_ACTION,R.CHECK_S2A))
for k,v in res.items():
    o,r=v[0],v[1:]
    if isinstance(o,bool): print(k,"orig",o,"sat",sum(r),"/",len(r))
    elif isinstance(o,str): print(k,"orig",o,"reseeds",{x:r.count(x) for x in set(r)})
    else: print(k,"orig %.4f min %.4f med %.4f max %.4f"%(o,min(r),st.median(r),max(r)))
