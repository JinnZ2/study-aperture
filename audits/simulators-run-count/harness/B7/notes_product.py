# run from notes copy; product_test(seed=) check_datasets.py:145 (default 1000)
import sys, statistics as st
sys.path.insert(0,"../sim-span")
import check_datasets as C
R=[]
for s in [1000]+list(range(1,21)):
    rows=C.product_test(seed=s); v=C.product_verdict(rows)
    vs=[r["vertex"] for r in rows]
    R.append(dict(spread=v["vertex_spread"],err=v["mean_err"],allu=all(r["is_u"] for r in rows),
        down=all(vs[i]>vs[i+1] for i in range(3)) if None not in vs else False, low=min(x for x in vs if x is not None), vs=[round(x,2) if x else None for x in vs]))
o,r=R[0],R[1:]
for k in ["spread","err","low"]:
    v=[x[k] for x in r]; print(k,"orig %.3f min %.3f med %.3f max %.3f"%(o[k],min(v),st.median(v),max(v)))
for k in ["allu","down"]: print(k,"orig",o[k],"sat",sum(x[k] for x in r),"/",len(r))
print("err<0.05",sum(x["err"]<0.05 for x in r)); print([x["vs"] for x in r])
# 1-hour WASO (pairs constructed here, not in the repo)
C.EQUAL_PRODUCT=[(0.5,120.0),(1.0,60.0),(2.0,30.0),(4.0,15.0)]
print("1h WASO is_u by seed:",[[q["is_u"] for q in C.product_test(seed=s)] for s in [1000,1,2,3,4,5]])
