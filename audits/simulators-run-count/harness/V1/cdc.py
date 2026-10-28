import sys, json
sys.path.insert(0, sys.argv[1])
import credential_channel as cc
n=int(sys.argv[2])
for s in map(int, sys.argv[3:]):
    r=cc.i5_attribution_error(cc.i5_events(seed=s, n=n))
    lv=sorted(r["by_credited_level"]); rates=[round(r["by_credited_level"][l]["error_rate"],3) for l in lv]
    print(json.dumps(dict(seed=s, n=n, levels=lv, rates=rates, upward_share=r["upward_share"],
      l1_zero=r["by_credited_level"].get(1,{}).get("error_rate")==0.0,
      nondecreasing=all(a<=b for a,b in zip(rates,rates[1:])), l3_gt_l2=r["by_credited_level"][3]["error_rate"]>r["by_credited_level"][2]["error_rate"])))
