# usage: rcl.py SIMDIR WORLD_SEED|vary delegation_seeds...
import sys, json
sys.path.insert(0, sys.argv[1])
import preentry_register as PR
print("TRACK_RHO", PR.TRACK_RHO)
for d in map(int, sys.argv[3:]):
    w = d-1 if sys.argv[2]=="vary" else int(sys.argv[2])
    r = PR.delegation_corruption(PR.make_world(seed=w, calibrated=True), seed=d)
    a, b = r["declared_and_excluded"], r["pooled_as_zero"]
    print(json.dumps(dict(world=w, deleg=d, declared_rho=round(a["rho"],4), declared=a["verdict"], pooled_rho=round(b["rho"],4), pooled=b["verdict"], flip=a["verdict"]!=b["verdict"], lower=b["rho"]<a["rho"])))
