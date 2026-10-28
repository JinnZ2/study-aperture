# run from recommender-confound copy: python3 ../../scripts/rc_reseed.py
import json, statistics as st, synthetic_catalog as sc, abstention_channel as ac
seeds=[1]+list(range(2,22))
R={k:[] for k in "rc1_exactmax rc1_exactmin rc1_truemin rc1_truemax rc1_ok rc2_sparse rc2_both rc3_collapse rc3_v1 rc3_v2 rc3_ok rc10_c0_exact0 rc10_jacc_hidden rc10_highneg rc10_onlylow_nonneg rc10_jacc_allneg rc10_fracneg rc13_scalar rc13_hid rc13_miss rc13_ok".split()}
for s in seeds:
    g=sc.grid(s); c=g["corners"]
    ex=[v["measured"]["exact"]["halluc"] for v in c.values()]; tr=[v["true_fabrication_rate"] for v in c.values()]
    R["rc1_exactmin"].append(min(ex)); R["rc1_exactmax"].append(max(ex)); R["rc1_truemin"].append(min(tr)); R["rc1_truemax"].append(max(tr))
    R["rc1_ok"].append(all(v["measured"]["exact"]["measured_minus_true"]>=0 for v in c.values()) and g["swing_across_corners_by_matcher"]["exact"]>0)
    eq=lambda k: all(round(m["halluc"],3)==round(c[k]["true_fabrication_rate"],3) for m in c[k]["measured"].values())
    R["rc2_sparse"].append(eq("sparse/high")); R["rc2_both"].append(eq("sparse/high") and eq("dense/high"))
    a=ac.sim(s); R["rc3_collapse"].append(a["collapse"]); R["rc3_v1"].append(a["v1"]["halluc_mean"]); R["rc3_v2"].append(a["v2"]["halluc_mean"]); R["rc3_ok"].append(a["collapse"]>0)
    R["rc10_c0_exact0"].append(all(v["measured"]["exact"]["fabrications_hidden_by_matcher"]==0 for v in c.values()))
    R["rc10_jacc_hidden"].append("/".join(str(c[k]["measured"]["jaccard"]["fabrications_hidden_by_matcher"]) for k in c))
    g3=sc.grid(s,collision=0.3); c3=g3["corners"]
    cells=[(k,m,v["measured_minus_true"]) for k,cc in c3.items() for m,v in cc["measured"].items()]
    R["rc10_highneg"].append(all(d<0 for k,m,d in cells if k.endswith("high")))
    R["rc10_onlylow_nonneg"].append(all(k.endswith("low") for k,m,d in cells if d>=0) and all(d<0 for k,m,d in cells if k.endswith("high")) and all(d<0 for k,m,d in cells if m=="jaccard"))
    R["rc10_jacc_allneg"].append(all(d<0 for k,m,d in cells if m=="jaccard"))
    R["rc10_fracneg"].append(sum(d<0 for *_,d in cells)/len(cells))
    j=c3["dense/low"]["measured"]["jaccard"]
    R["rc13_scalar"].append(j["measured_minus_true"]); R["rc13_hid"].append(j["fabrications_hidden_by_matcher"]); R["rc13_miss"].append(j["true_items_missed_by_matcher"])
    R["rc13_ok"].append(abs(j["measured_minus_true"])<0.05 and j["fabrications_hidden_by_matcher"]>0 and j["true_items_missed_by_matcher"]>0)
for k,v in R.items():
    o=v[0]; r=v[1:]
    if isinstance(o,bool): print(k,"orig",o,"reseed sat",sum(r),"/",len(r))
    elif isinstance(o,str): print(k,"orig",o,"reseeds",r)
    else: print(k,"orig",o,"min",min(r),"median",st.median(r),"max",max(r))
