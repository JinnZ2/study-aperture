# usage: span.py SIMDIR LEG seeds...  -> full hit list per seed
import sys, json
sys.path.insert(0, sys.argv[1])
import sim_span as S
leg = sys.argv[2]
for s in map(int, sys.argv[3:]):
    vf = S.vertex_floor(leg, seed=s)
    print(json.dumps({"seed": s, "leg": leg, "floor": vf["floor"], "n_hits": len(vf["hits"]), "n_in_window": len(vf["in_window"]),
                      "hits": [{"v": round(h["vertex"], 4), "p": h["p"], "frag": h["frag"], "wake": h["wake"]} for h in vf["hits"]]}), flush=True)
