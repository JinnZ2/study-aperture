# run from the model-ecology copy: python3 ../../harness/me_reseed.py
# Re-runs demo.py's pipeline with make_signal(seed) for seeds 0..23 (demo.py:115 uses default seed=3).
import sys, json, io, contextlib
sys.path.insert(0, '.')
import demo as D
import models as M
from core import _mean, _std
from phylogeny import within_vs_cross, artificial_consensus
from disagreement import information_contribution
from meta_engine import sweep_observers, observer_sensitivity, representation_invariance
def conclusion(x):
    h = len(x)//2; sa, sb = _std(x[:h]), _std(x[h:])
    return abs(sa-sb)/(max(sa,sb)+1e-9) > 0.15
out = []
for seed in range(24):
    signal = D.make_signal(seed)
    mods = M.all_models()
    results = {m.name: m.predict(signal) for m in mods}
    series = {k: v.prediction for k, v in results.items()}
    L = min(len(v) for v in series.values()); series = {k: v[:L] for k, v in series.items()}
    shift_idx = D.SHIFT - D.WINDOW
    consensus = D.add_diagnostics(results, series)
    truth = D.local_variance(signal, D.WINDOW)[:L]
    p1 = within_vs_cross(series); ac = artificial_consensus(series)
    testable = [r for r in D.sweep_threshold(series, shift_idx) if not r['saturated']]
    d_s = _mean([r['lead_struct']-r['early_struct'] for r in testable]) if testable else None
    d_i = _mean([r['lead_isol']-r['early_isol'] for r in testable]) if testable else None
    census = {n: information_contribution(s, truth, consensus, shift_idx) for n, s in series.items()}
    prophets = sorted(n for n, v in census.items() if v['species']=='prophet')
    os_ = observer_sensitivity(mods, results, sweep_observers(32))
    ri = representation_invariance(signal, conclusion)
    w = os_['winners']; top = max(w, key=w.get)
    out.append(dict(seed=seed, p=p1['p_value'], sig=p1['p_value']<0.05, n_eff=ac['n_empirical'], n_phylo=ac['n_phylo'],
        phylo_err=ac['phylo_error'], infl=ac['inflation_factor'], d_s=d_s, d_i=d_i,
        D1=(d_s is not None and d_s>0 and d_s>d_i), sync=(d_s is not None and d_s<0), prophets=prophets,
        churn=os_['observer_churn'], invariant=os_['invariant'], top=top, top_n=w[top],
        manifold=ri['support'].get('manifold')))
    print(json.dumps(out[-1]))
json.dump(out, open('../../harness/me_reseed.json','w'))
