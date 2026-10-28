import sys, json
sys.path.insert(0, sys.argv[1])
import coupling_gap_test as C
def one(seed):
    C.SEED = seed
    cp = C.run(C.Proposer(32, True), seed=seed); dc = C.run(C.Proposer(32, False), seed=seed)
    gens, mem = [], None
    for g in range(12):
        p = C.Proposer(32, False); tr = C.run(p, seed=seed+g, seed_mem=mem)
        gens.append((C.m(tr["coh"]), C.m(tr["acc"]))); mem = list(p.mem)
    a = C.linreg_slope([x for _,x in gens]); c = C.linreg_slope([x for x,_ in gens])
    r = dict(seed=seed, dc_coh=C.m(dc["coh"]), dc_acc=C.m(dc["acc"]), cp_coh=C.m(cp["coh"]), cp_acc=C.m(cp["acc"]))
    r["cp_gap"] = round(abs(r["cp_coh"]-r["cp_acc"]),3)
    r["c1"] = r["dc_coh"]>0.8 and r["dc_acc"]<0.5 and r["cp_gap"]<0.2
    r["acc_slope"]=round(a,5); r["coh_slope"]=round(c,5); r["c4v2"]= a<0 and abs(c)<0.01
    return r
for s in sys.argv[2:]:
    print(json.dumps(one(int(s))))
