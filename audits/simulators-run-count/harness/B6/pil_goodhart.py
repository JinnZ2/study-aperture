# reseed proxy_lab.goodhart.red_team (default seed=99) at seeds 1..20; imports from the copy
import sys, os, statistics as st; sys.path.insert(0, os.path.join(sys.argv[1], "src"))
from proxy_lab.goodhart import red_team
o = red_team(); print("orig", o.baseline_correlation, o.gamed_correlation, o.fidelity_collapse, o.gaming_latency_periods, o.detection_surface["variance_ratio_top_decile"], o.detection_surface["slope_top_vs_bottom"])
R = [red_team(seed=s) for s in range(1, 21)]
def r(v): return (round(min(v),4), round(st.median(v),4), round(max(v),4))
print("base", r([x.baseline_correlation for x in R])); print("gamed", r([x.gamed_correlation for x in R]))
print("collapse", r([x.fidelity_collapse for x in R]), "collapse>0", sum(x.fidelity_collapse > 0 for x in R))
print("round3 base==0.904", sum(round(x.baseline_correlation,3)==0.904 for x in R), "gamed==0.713", sum(round(x.gamed_correlation,3)==0.713 for x in R), "collapse==0.191", sum(round(x.fidelity_collapse,3)==0.191 for x in R))
print("latency", sorted(set(x.gaming_latency_periods for x in R)))
print("slope", r([x.detection_surface["slope_top_vs_bottom"] for x in R]), "slope>0", sum(x.detection_surface["slope_top_vs_bottom"]>0 for x in R))
print("varratio", r([x.detection_surface["variance_ratio_top_decile"] for x in R]), ">1", sum(x.detection_surface["variance_ratio_top_decile"]>1 for x in R))
