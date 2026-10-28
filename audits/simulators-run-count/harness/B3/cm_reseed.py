"""Reseed one stochastic climate-modeling audit.
Usage (cwd = sim/climate-modeling): python3 cm_reseed.py <DataAggregationAudit|CascadeSpeedAudit> seed [seed...]
Equivalent to editing the seed= literal at audits/data_aggregation.py:22 / audits/cascade_speed.py:27."""
import sys, json, time, functools
sys.path.insert(0, '.')
import audits.data_aggregation as da, audits.cascade_speed as cs
from run_audits import run_single_audit
name = sys.argv[1]
mod, cls = (da, 'StochasticForcing') if name == 'DataAggregationAudit' else (cs, 'FatTailedForcing')
orig = getattr(mod, cls)
for s in map(int, sys.argv[2:]):
    def patched(*a, _s=s, **k):
        k['seed'] = _s
        return orig(*a, **k)
    setattr(mod, cls, patched)
    t = time.time()
    r = run_single_audit(name)
    print(json.dumps({"audit": name, "seed": s, "status": r["status"], "metrics": r["metrics"],
                      "true_final": r["true_final"], "audited_final": r["audited_final"], "sec": round(time.time()-t,1)}), flush=True)
