# usage: anc.py SIMDIR MODE seeds...   MODE=all (vary seed everywhere) | noise (substrate+initial corpus fixed at SEED; vary only injection rng seed+2)
import sys, json
sys.path.insert(0, sys.argv[1])
import corpus_loop as CL
mode=sys.argv[2]
if mode=="noise":
    o_sub, o_init = CL.substrate, CL.initial_corpus
    CL.substrate = lambda n, s: o_sub(n, CL.SEED)
    CL.initial_corpus = lambda t, s, bias=CL.INITIAL_BIAS: o_init(t, CL.SEED+1, bias)
for sd in map(int, sys.argv[3:]):
    sig,null=[],[]
    for lam in (0.02,0.04,0.08,0.12,0.20,0.30,0.45):
        sig += [r["corpus_shift"] for r in CL.run("degrade",lam,seed=sd)]
        null += [r["corpus_shift"] for r in CL.run("improve",lam,seed=sd)]
    lo,hi=min(sig+null),max(sig+null); fpge=True; best=None; zero_thr=[]
    for k in range(21):
        thr=lo+(hi-lo)*k/20.0; tp=sum(x>thr for x in sig)/len(sig); fp=sum(x>thr for x in null)/len(null)
        fpge = fpge and fp>=tp
        if best is None or tp-fp>best[0]: best=(round(tp-fp,4),k,round(tp,3),round(fp,3))
    print(json.dumps(dict(seed=sd, fp_ge_tp=fpge, best_tp_minus_fp=best)))
