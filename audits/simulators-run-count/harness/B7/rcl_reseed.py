# run from reporting-chain-loss copy
import statistics as st, preentry_register as PR
rows=[]
for ws,ds in [(0,1)]+[(s,s+1) for s in range(1,21)]:
    cal=PR.calibration(PR.make_world(seed=ws,calibrated=True)); unc=PR.calibration(PR.make_world(seed=ws,calibrated=False))
    dc=PR.delegation_corruption(PR.make_world(seed=ws,calibrated=True),seed=ds)
    rows.append((cal["rho"],cal["verdict"],unc["rho"],unc["verdict"],dc["declared_and_excluded"]["rho"],dc["declared_and_excluded"]["verdict"],dc["pooled_as_zero"]["rho"],dc["pooled_as_zero"]["verdict"]))
for r in rows: print(["%.3f"%x if isinstance(x,float) else x for x in r])
o,R=rows[0],rows[1:]
for i,n in [(0,"cal"),(2,"unc"),(4,"decl"),(6,"pooled")]:
    v=[r[i] for r in R]; print(n,"orig %.3f min %.3f med %.3f max %.3f"%(o[i],min(v),st.median(v),max(v)))
print("RCL_007 both branches (cal TRACKS & unc DOES_NOT):",sum(r[1]=="TRACKS_calibrated" and r[3]=="DOES_NOT_TRACK" for r in R),"/",len(R))
print("RCL_008 flip (decl TRACKS & pooled DOES_NOT):",sum(r[5]=="TRACKS_calibrated" and r[7]=="DOES_NOT_TRACK" for r in R),"/",len(R))
print("RCL_008 pooled<decl:",sum(r[6]<r[4] for r in R),"/",len(R))
