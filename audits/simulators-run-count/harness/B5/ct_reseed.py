# reseed harness for conversation-type CT_002; binarise_cost(seed=...) per seed
import sys, os, json
sys.path.insert(0, os.getcwd())
import design_check as D
out={}
for sd in [int(x) for x in sys.argv[1].split(",")]:
    out[sd]={sh:[round(D.binarise_cost(t,shape=sh,seed=sd)["recovered"],4) for t in (0.3,0.5,0.7)] for sh in ("uniform","bimodal")}
print(json.dumps(out))
