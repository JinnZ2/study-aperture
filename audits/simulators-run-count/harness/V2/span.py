import sys, json
sys.path.insert(0, sys.argv[1]); import sim_span as S
for s in map(int, sys.argv[2:]):
    out = {"seed": s}
    for leg in S.LEGS:
        vf = S.vertex_floor(leg, seed=s)
        out[leg] = {"hits": len(vf["hits"]), "in_window": len(vf["in_window"]), "floor": vf["floor"],
                    "a_range": [min(h["a"] for h in vf["hits"]), max(h["a"] for h in vf["hits"])] if vf["hits"] else None,
                    "a_sorted": sorted(round(h["a"], 4) for h in vf["hits"])}
    print(json.dumps(out), flush=True)
