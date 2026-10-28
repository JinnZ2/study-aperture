import sys, json, io, contextlib, math, random
sys.path.insert(0, sys.argv[1]); import finite_n_control as F
rows = []
for s in [20260815] + list(range(1, 21)):
    F.SEED = s
    with contextlib.redirect_stdout(io.StringIO()):
        g = [F.run(F.poisson, "p", 2.0), F.run(F.line, "l", 1.0), F.run(F.cantor_dust, "d", 1.26, 2.0), F.run(F.cantor_dust, "d", 1.26, 3.0)]
    b2 = F.dimension(F.cantor_dust(F.N_DENSE, random.Random(s)), 2.0)["d_f"]; b3 = F.dimension(F.cantor_dust(F.N_DENSE, random.Random(s)), 3.0)["d_f"]
    fn = max(abs(x) for x in g); lad = abs(b2 - b3); bud = fn + lad; res = 0.334 - bud
    rows.append(dict(seed=s, finite_n=round(fn,4), ladder=round(lad,4), budget=round(bud,4), residual=round(res,4), ratio=round(res/0.021,2)))
for r in rows: print(json.dumps(r))
R = rows[1:]
print("residual>0.021:", sum(r["residual"]>0.021 for r in R), "| ratio rounds to >=4 (>=3.5x):", sum(r["ratio"]>=3.5 for r in R), "| literal>=4x:", sum(r["ratio"]>=4 for r in R), "| budget<0.334:", sum(r["budget"]<0.334 for r in R), "| finite_n<=0.137:", sum(r["finite_n"]<=0.137 for r in R), "| ladder<=0.115:", sum(r["ladder"]<=0.115 for r in R))
fnmax = max(r["finite_n"] for r in rows); ladmax = max(r["ladder"] for r in rows)
print("pooled worst-case over 21 draws: finite_n", fnmax, "ladder", ladmax, "budget", round(fnmax+ladmax,4), "residual", round(0.334-fnmax-ladmax,4))
