import sys, json
sys.path.insert(0, sys.argv[1]); import residual as R
orig = R._noise
mode = sys.argv[2]
offs = [0] + [1000*k for k in range(1, 21)] if mode == "k20" else range(1, 2001)
cnt = {"F1": {}, "F2": {}, "F3": {}}; rows = []
distinct = len({R.STABLE, R.GROWING, R.RATE_NOT_COMPUTABLE}) == 3
for off in offs:
    R._noise = lambda n, amp, seed, off=off: orig(n, amp, seed + off)
    st = {f: R.rate_check(R.fixture(f))["state"] for f in ("F1", "F2", "F3")}
    for f in st: cnt[f][st[f]] = cnt[f].get(st[f], 0) + 1
    rows.append(dict(off=off, **st))
if mode == "k20":
    for r in rows: print(json.dumps(r))
print("distinct output strings:", distinct)
print(json.dumps(cnt))
re = rows[1:] if mode == "k20" else rows
print("falsifier (F3 growing read STABLE):", sum(r["F3"] == R.STABLE for r in re), "/", len(re))
print("F3 GROWING:", sum(r["F3"] == R.GROWING for r in re), "| all three table rows:", sum(r["F1"]=="STABLE" and r["F2"]=="STABLE" and r["F3"]=="GROWING" for r in re), "/", len(re))
