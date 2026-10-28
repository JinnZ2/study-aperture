# reseed harness for credential-channel; mirrors test_credential.py checks with world seeds passed in
import sys, os, json
sys.path.insert(0, os.getcwd())
import credential_channel as cc
seeds=[int(x) for x in sys.argv[1].split(",")]
out={}
for sd in seeds:
    r1=cc.i1_route_correlation(cc.i1_candidates(seed=sd))
    i3=cc.i3_gap_vs_exposure(cc.i3_rows(seed=sd)); i4=cc.i4_inventory_vs_exposure(cc.i4_rows(seed=sd))
    i5=cc.i5_attribution_error(cc.i5_events(seed=sd)); L=i5["by_credited_level"]
    rates=[L[k]["error_rate"] for k in sorted(L) if L[k]["error_rate"] is not None]
    out[sd]={"rho_a":r1["rho_a"],"rho_b":r1["rho_b"],"i1_verdict_ok":"uncorrelated or inverse" in r1["verdict"],
             "i3":i3["exposure_coef"],"i4":i4["exposure_coef"],"upshare":i5["upward_share"],
             "l1":L.get(1,{}).get("error_rate"),"l3_gt_l2":(L.get(3,{}).get("error_rate") or 0)>(L.get(2,{}).get("error_rate") or 0),
             "monotone":all(rates[i]<=rates[i+1] for i in range(len(rates)-1)),"rates":rates}
print(json.dumps(out))
