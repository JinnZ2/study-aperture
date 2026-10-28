# run from transmission-cascade copy. Seeds passed explicitly to the generator functions
# (transmission_cascade.py:208 cascade_events seed=3, :222 two_coders seed=5, test_cascade.py:70 low coders seed=9,
#  :235 condition_runs seed=11, :250 competing_rows seed=13). Reseed k uses base+100*k for every generator.
import statistics as st, transmission_cascade as tc
R=[]
for k in range(0,21):
    o=100*k
    ev=tc.cascade_events(seed=3+o); c1,c2=tc.two_coders(ev,agree=0.85,seed=5+o); rel=tc.r2_reliability(c1,c2)
    l1,l2=tc.two_coders(ev,agree=0.35,seed=9+o); rl=tc.r2_reliability(l1,l2)
    r1=tc.r1_distribution(ev,rel)
    over=[r1["distribution"][L]["OVERIMITATION"] for L in (1,2,3)] if r1["distribution"] else None
    r3=tc.r3_recompute(tc.condition_runs(seed=11+o))
    a=tc.r4_competing(tc.competing_rows(seed=13+o,id_effect=0.0)); b=tc.r4_competing(tc.competing_rows(seed=13+o,id_effect=0.8,type_effect=0.0))
    R.append(dict(kh=rel["kappa"],kl=rl["kappa"],tc1=rel["gate"]=="R1_INTERPRETABLE" and rl["gate"]=="R1_UNINTERPRETABLE",
      over=over,tc2=bool(over) and over[0]<over[2],tc2strict=bool(over) and over[0]<over[1]<over[2],
      emu=r3["emulation_share"],ovs=r3["overimitation_share"],tc3=r3["verdict"].startswith("type predicts") and r3["emulation_share"]>r3["overimitation_share"],
      ta=a["type_with_identification"],tb=b["type_with_identification"],
      tc5="survives" in a["verdict"] and "adds nothing" in b["verdict"],
      tc6=abs(b["type_with_identification"])<tc.MATERIAL<=abs(a["type_with_identification"])))
o,r=R[0],R[1:]
for key in ["kh","kl","emu","ovs","ta","tb"]:
    v=[x[key] for x in r]; print(key,"orig %.3f min %.3f med %.3f max %.3f"%(o[key],min(v),st.median(v),max(v)))
print("over orig",o["over"],"reseeds",[x["over"] for x in r])
for key in ["tc1","tc2","tc2strict","tc3","tc5","tc6"]: print(key,"orig",o[key],"sat",sum(x[key] for x in r),"/",len(r))
