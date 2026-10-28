import sys, json
sys.path.insert(0, sys.argv[1]); import prearm as P
CFG = P.demo_config()
def pulse(width, seed):
    s = P.fx_breathing(seed=seed, duration_s=1800)
    return [(t, v + (2000 if 900 <= t < 900 + 5 * width else 0)) for t, v in s]
seeds = list(map(int, sys.argv[3:])) if sys.argv[2] == 'list' else range(1, int(sys.argv[2]) + 1)
ok = 0; rows = []
for s in seeds:
    r6 = P.evaluate(CFG, {"gas": pulse(6, s)}); r7 = P.evaluate(CFG, {"gas": pulse(7, s)})
    rb = P.evaluate(CFG, {"gas": P.fx_breathing(seed=s, duration_s=1800)})
    good = r6["detect_t"] is None and r7["detect_t"] is not None
    ok += good
    rows.append(dict(seed=s, step30_detect=r6["detect_t"], step35_detect=r7["detect_t"], nostep_detect=rb["detect_t"], ok=good,
                     reason30=(r6["actions"][0]["reason"] if r6["actions"] else None)))
if sys.argv[2] == 'list':
    for r in rows: print(json.dumps(r))
print("satisfied", ok, "of", len(rows), "| 30s fires:", sum(r['step30_detect'] is not None for r in rows), "| 35s quiet:", sum(r['step35_detect'] is None for r in rows), "| no-step fires:", sum(r['nostep_detect'] is not None for r in rows))
