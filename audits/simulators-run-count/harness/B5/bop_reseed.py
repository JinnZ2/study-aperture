# reseed harness for battery-offgas-prearm; mirrors test_prearm.py checks with fixture seeds passed in
import sys, os, json
sys.path.insert(0, os.getcwd())
import prearm as P
CFG = P.demo_config()
seeds=[int(x) for x in sys.argv[1].split(",")]
out={}
for sd in seeds:
    r={}
    b=P.evaluate(CFG,{"gas":P.fx_breathing(seed=sd)}); r["breath_quiet"]= b["detect_t"] is None and not b["actions"]
    ramp,run_s=P.fx_runaway(seed=sd); e=P.evaluate(CFG,{"gas":ramp}); r["ramp_detect_t"]=e["detect_t"]
    r["ramp_ok"]= e["detect_t"] is not None and 1800.0<e["detect_t"]<run_s and [a["tier"] for a in e["actions"]]==[0,1,2]
    g=P.fx_glitch(seed=sd); r["ts_holds"]=P.evaluate(CFG,{"gas":g})["detect_t"] is None
    orig=P.slope; P.slope=P.slope_lsq
    try: r["lsq_trips"]=P.evaluate(CFG,{"gas":g})["detect_t"] is not None
    finally: P.slope=orig
    def pulse(w):
        s=P.fx_breathing(seed=sd,duration_s=1800); return [(t,v+(2000 if 900<=t<900+5*w else 0)) for t,v in s]
    r["step30_quiet"]=P.evaluate(CFG,{"gas":pulse(6)})["detect_t"] is None
    r["step35_fires"]=P.evaluate(CFG,{"gas":pulse(7)})["detect_t"] is not None
    out[sd]=r
print(json.dumps(out))
