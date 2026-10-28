# run from sim-span copy. three_column(seed=) three_column.py:93 ; nightly(seed=) three_column.py:118 ; one_run(seed) sim_span.py:253
import sys, json, sim_span as S, three_column as T
seeds=[int(x) for x in sys.argv[1:]]
for s in seeds:
    tcs=4242 if s==0 else s; ns=99 if s==0 else s; os_=1000 if s==0 else s
    rows=[T.three_column(p,seed=tcs) for p in (0.0,0.25,0.5,0.75,1.0)]
    err=max(abs(r["slope"]-r["p"]) for r in rows)
    att={p:(T.nightly(p,1,seed=ns)["recovered"],T.nightly(p,7,seed=ns)["recovered"]) for p in (0.25,0.5,0.75,1.0)}
    m=S.one_run(20000,"mono",1.0,os_)["reported"]
    print(json.dumps({"seed":s,"r2p":rows[-1]["r2_product"],"r2a":rows[-1]["r2_additive"],"maxerr":err,
      "maxabs_intercept":max(abs(r["intercept"]) for r in rows),"att":att,"mono_a":m["a"],"mono_vertex":m["vertex"],"mono_is_u":m["is_u"],"mono_hi":m["hi"]}),flush=True)
