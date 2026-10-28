"""proxy-investigation-lab README:49 "gaming ... inflates top-decile variance": compare the shipped
statistic WITH gaming (adapt_rate 0.35, default) against WITHOUT (adapt_rate 0), same seed.
Run: PYTHONPATH=<copy>/proxy-investigation-lab/src python3 -B proxy_gamed_vs_ungamed.py"""
from proxy_lab.goodhart import red_team
import statistics as st
seeds = range(99, 119)
g = [red_team(seed=s).detection_surface["variance_ratio_top_decile"] for s in seeds]
u = [red_team(seed=s, adapt_rate=0.0).detection_surface["variance_ratio_top_decile"] for s in seeds]
print("gamed   min %.3f med %.3f max %.3f" % (min(g), st.median(g), max(g)))
print("ungamed min %.3f med %.3f max %.3f" % (min(u), st.median(u), max(u)))
print("gamed > ungamed at", sum(a > b for a, b in zip(g, u)), "/ 20 seeds")
