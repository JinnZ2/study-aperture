import sys, json
sys.path.insert(0, sys.argv[1])
import transmission_cascade as tc
for s in map(int, sys.argv[2:]):
    a = tc.r4_competing(tc.competing_rows(seed=s, id_effect=0.0))
    b = tc.r4_competing(tc.competing_rows(seed=s, id_effect=0.8, type_effect=0.0))
    rel = lambda r: abs(r["type_with_identification"]) > 0.5*abs(r["type_alone"]) and r["type_with_identification"]*r["type_alone"] > 0
    print(json.dumps(dict(seed=s, real_with_id=round(a["type_with_identification"],4), null_with_id=round(b["type_with_identification"],4),
        null_alone=round(b["type_alone"],4), floor_separates=abs(b["type_with_identification"])<tc.MATERIAL<=abs(a["type_with_identification"]),
        relative_only_fires_on_null=rel(b), relative_only_fires_on_real=rel(a), verdict_real=a["verdict"], verdict_null=b["verdict"])))
