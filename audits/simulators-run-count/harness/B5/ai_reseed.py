# reseed harness for anchor-interval; run from the folder copy. Mirrors corpus_loop.check_* and moving_reference.check_rank with seed passed in.
import sys, os, json, math, random, io, contextlib
sys.path.insert(0, os.getcwd())
import corpus_loop as CL, moving_reference as MR
seeds=[int(x) for x in sys.argv[1].split(",")]
out={}
for sd in seeds:
    r={}
    h=CL.run("degrade",0.12,seed=sd); f=CL.run("degrade",0.0,seed=sd)
    r["drift_012"]=h[-1]["coupling_err"]-h[0]["coupling_err"]; r["drift_0"]=f[-1]["coupling_err"]-f[0]["coupling_err"]
    r["sep"]= h[-1]["coupling_err"]>h[0]["coupling_err"] and h[-1]["coherence_err"]<h[0]["coherence_err"] and h[-1]["corpus_shift"]<h[0]["corpus_shift"]
    r["d1_mono"]=all(b["coherence_err"]<=a["coherence_err"]+1e-12 for a,b in zip(h,h[1:]))
    sig,null=[],[]; worse=better=0
    for lam in (0.02,0.04,0.08,0.12,0.20,0.30,0.45):
        d=CL.run("degrade",lam,seed=sd); i=CL.run("improve",lam,seed=sd)
        sig+= [x["corpus_shift"] for x in d]; null+=[x["corpus_shift"] for x in i]
        worse+= d[-1]["coupling_err"]>d[0]["coupling_err"]; better+= i[-1]["coupling_err"]<i[0]["coupling_err"]
    lo,hi=min(sig+null),max(sig+null); fpge=True; best=-9
    for k in range(21):
        thr=lo+(hi-lo)*k/20.0; tp=sum(x>thr for x in sig)/len(sig); fp=sum(x>thr for x in null)/len(null)
        fpge = fpge and fp>=tp; best=max(best,tp-fp)
    r.update(fp_ge_tp=fpge, best_tp_fp=best, worse=worse, better=better)
    r["final_noanchor"]=h[-1]["coupling_err"]
    r["triggered_fires"]=sum(1 for x in h if x["coherence_err"]>h[0]["coherence_err"])
    sched=[CL.run("degrade",0.12,seed=sd,anchor_every=e,anchor_frac=1.0)[-1]["coupling_err"] for e in (12,8,6,4,3,2)]
    r["sched"]=sched; r["sched_mono"]=all(sched[j]>sched[j+1] for j in range(5)) and sched[0]<r["final_noanchor"]
    MR.SEED=sd
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf): MR.check_rank()
    ne={}
    for line in buf.getvalue().splitlines():
        p=line.split()
        if len(p)>=3 and p[0] in ("0.00","0.95"):
            try: ne[p[0]]=float(p[1])
            except: pass
    r["neff_0"]=ne.get("0.00"); r["neff_095"]=ne.get("0.95")
    out[sd]=r
print(json.dumps(out))
