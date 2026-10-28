# reseed harness for alignment-under-coupling; run from the folder copy
import sys, os, json, statistics as st
sys.path.insert(0, os.getcwd())
import check_run_1 as K, sim_b_entropy_depletion as B, sim_c_loop_threshold as C, sim_d_temperature_null as D
which = sys.argv[1]; seeds = [int(x) for x in sys.argv[2].split(",")]
out = {}
for sd in seeds:
    if which == "simc":   # RESULTS:91 / TFM_003, iters=150 as run_all
        res = [(s,) + C.run(s, 5, 150, seed=sd)[:2] for s in (0.0,0.1,0.2,0.3,0.4,0.5,0.7,0.9,1.2,1.6)]
        out[sd] = {"all_alive40": all(r[2]==40 for r in res), "min_alive": min(r[2] for r in res)}
    elif which == "cond":  # TFM_004 table
        out[sd] = {str(s): round(K.conductance_range(s, seed=sd)["floor_below_min_by"],2) for s in (0.0,0.4,1.6)}
    elif which == "split":  # TFM_005
        _, tp = K.final_distribution(0.0, gens=0); base = K.split_entropy(tp)
        r = {}
        for a in (0.0,0.05,0.40):
            p,_ = K.final_distribution(a, seed=sd); s = K.split_entropy(p)
            r[str(a)] = (round(s["H_head"]-base["H_head"],3), round(s["H_tail"]-base["H_tail"],3))
        out[sd] = r
    elif which == "simb":  # RESULTS:57-64
        rows=[]
        for a in (0.0,0.01,0.02,0.05,0.10,0.20,0.40):
            rr = B.run(a, 12, 3000, seed=sd, verbose=False)
            d = rr[0][1]-rr[-1][1]
            rows.append((a, round(rr[-1][1],3), "COLLAPSE" if d>1.0 else "eroding" if d>0.4 else "held"))
        out[sd] = rows
    elif which == "simd":  # RESULTS:13-14
        r={}
        for name,stg in (("UNQ",0.0),("Q",1.5)):
            rows = D.sweep(stg, 3000, rng_seed=sd)
            r[name] = [D.verdict(rows,c) for c in (1,2,3)]
        out[sd]=r
print(json.dumps(out))
