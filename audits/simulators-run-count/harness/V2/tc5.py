import sys, json
sys.path.insert(0, sys.argv[1]); import transmission_cascade as tc
def one(s):
    a = tc.r4_competing(tc.competing_rows(seed=s, id_effect=0.0)); b = tc.r4_competing(tc.competing_rows(seed=s, id_effect=0.8, type_effect=0.0))
    return dict(seed=s, real_type_b=round(a["type_with_identification"],4), real_type_verdict=a["verdict"], null_type_b=round(b["type_with_identification"],4), null_type_verdict=b["verdict"],
                A_ok="survives" in a["verdict"], B_ok="adds nothing" in b["verdict"])
if sys.argv[2] == "k20":
    R = [one(13 + 100*k) for k in range(21)]
    for r in R: print(json.dumps(r))
    R = R[1:]
else:
    R = [one(s) for s in range(1, 2001)]
print("both halves:", sum(r["A_ok"] and r["B_ok"] for r in R), "/", len(R), "| real-type survives:", sum(r["A_ok"] for r in R), "| null-type adds nothing:", sum(r["B_ok"] for r in R))
