# run from sim-span copy: python3 span_grid.py SEED [SEED...]  -> one JSON line per seed (vertex_floor per leg, sim_span.py:292 seed arg)
import sys, json, sim_span as S
for s in map(int, sys.argv[1:]):
    out={"seed":s}
    for leg in S.LEGS:
        vf=S.vertex_floor(leg, seed=s)
        out[leg]={"hits":len(vf["hits"]),"in_window":len(vf["in_window"]),"floor":vf["floor"],
                  "a_range":[min(h["a"] for h in vf["hits"]),max(h["a"] for h in vf["hits"])] if vf["hits"] else None,
                  "lowest3_p":[h["p"] for h in vf["hits"][:3]]}
    print(json.dumps(out),flush=True)
