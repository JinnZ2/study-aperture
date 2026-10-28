import sys, json
sys.path.insert(0, sys.argv[1])
import synthetic_catalog as sc
for s in map(int, sys.argv[2:]):
    c=sc.grid(s)["corners"]; out={"seed":s}
    for k in ("sparse/high","dense/high"):
        t=c[k]["true_fabrication_rate"]
        dev={m:v["halluc"] for m,v in c[k]["measured"].items() if round(v["halluc"],3)!=round(t,3)}
        out[k]={"true":t,"deviating":dev,"all_equal":not dev}
    out["both_high_ok"]=out["sparse/high"]["all_equal"] and out["dense/high"]["all_equal"]
    print(json.dumps(out), flush=True)
