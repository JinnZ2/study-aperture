"""Usage: python3 reseed_refutations.py <fragility-cascade dir> [seed ...]
Seed 'orig' = no reseed (reproduces samples/test_refutations.sample.txt).
For an integer seed s: random.seed(s) is called immediately before each test_C1x()
(the module itself never seeds; the global stream is set by collapse_predictor imports).
Also records the number of DISTINCT per-trial outcomes seen inside each test."""
import sys, os, io, contextlib, random, json
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import test_refutations as T
out = {}
for s in sys.argv[2:]:
    t = T.RefutationTester(dim=8, generations=8, trials=50)
    orig = t.run_trial; seen = []
    def rt(*a, **k):
        p = orig(*a, **k)
        seen.append((round(p['resonance_factor'], 4), round(p['integrity'], 4), p['status'])); return p
    t.run_trial = rt
    row = {}
    for name in ("test_C12", "test_C13", "test_C14", "test_C15", "test_C16"):
        if s != "orig": random.seed(int(s))
        seen.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            r = getattr(t, name)()
        row[r["claim"]] = dict(verdict=r["verdict"], n=r["n_trials"], ce=r["counterexamples"],
                               notes=r["notes"], trials_run=len(seen), distinct=len(set(seen)),
                               first=seen[0] if seen else None)
    out[s] = row
print(json.dumps(out))
