import sys, json
sys.path.insert(0, sys.argv[1]); import synthetic_catalog as sc
for s in map(int, sys.argv[2:]):
    c = sc.grid(s, collision=0.3)["corners"]
    j = c["dense/low"]["measured"]["jaccard"]
    cells = [(k, m, v["measured_minus_true"], v["fabrications_hidden_by_matcher"], v["true_items_missed_by_matcher"]) for k, cc in c.items() for m, v in cc["measured"].items()]
    falsif = [x for x in cells if abs(x[2]) < 0.05 and x[3] == 0 and x[4] == 0]
    jac = [x for x in cells if x[1] == "jaccard"]
    print(json.dumps(dict(seed=s, dl_jacc_scalar=j["measured_minus_true"], dl_hidden=j["fabrications_hidden_by_matcher"], dl_missed=j["true_items_missed_by_matcher"],
        dl_true_fab=c["dense/low"]["true_fabrication_rate"], dl_exact_scalar=c["dense/low"]["measured"]["exact"]["measured_minus_true"],
        jacc_cells=[(k, round(d,3), h, mi) for k,_,d,h,mi in jac], falsifier_cells=falsif)), flush=True)
