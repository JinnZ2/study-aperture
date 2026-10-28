"""Consolidate the C2 audit: first pass + verification -> final verdict per single-draw claim.
Stdlib only, deterministic, reads only ./data. Usage: python3 consolidate.py [--markdown]
Writes data/final.json and prints the summary (and with --markdown, the per-claim table)."""
import collections, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

def jsonl(name):
    return [json.loads(l) for l in (DATA / name).read_text().splitlines() if l.strip()]

first = jsonl("first_pass.jsonl")
claims = [r for r in first if not r.get("summary")]
folders = [r for r in first if r.get("summary")]
checks = {(r["folder"], r["claim_id"]): r for r in jsonl("verification.jsonl") + jsonl("lead_verification.jsonl")}

# Judgement calls for REVISED rows, made explicit so they can be audited.
# Each maps to the verdict of the FAIR test (in-scope randomness, criterion matching the wording).
REVISED_TO = {
    ("model-ecology", "M1a"): "HOLDS",                                       # observer-only reseed
    ("proxy-investigation-lab", "README.md:49"): "FAILS_IN_SOME",             # gamed vs ungamed: 17/20
    ("floor-resilience", "README.md:106"): "NOT_STOCHASTIC_IN_SCOPE",         # one fixed shipped plant
    ("recommender-confound", "RC_013"): "HOLDS",                              # existential claim
    ("residual-direction", "RDD_005"): "HOLDS",                               # STABLE vs GROWING distinct
    ("sim-span", "RESULTS.md:26"): "DIRECTION_HOLDS_MAGNITUDE_VARIES",       # "10x" not met even at orig
    ("credential-channel", "CDC_006"): "NOT_STOCHASTIC_IN_SCOPE",             # one fixed constructed world
    ("reporting-chain-loss", "RCL_008"): "HOLDS",                             # "can flip" needs one flip
    ("residual-direction", "RDD_006"): "NOT_STOCHASTIC_IN_SCOPE",             # fixed fixture F4
    ("transmission-cascade", "TC_006"): "NOT_STOCHASTIC_IN_SCOPE",            # "on the two constructed worlds"
    ("sim-span", "RESULTS.md:91"): "FAILS_IN_SOME",                           # corrected criterion: 17/20
}
FIXED = {"CONFIRMED": "FAILS_IN_SOME", "SELF_FLAGGED_NEARBY": "SELF_FLAGGED_NEARBY",
         "NOT_REPRODUCED_AT_ORIGINAL": "NOT_REPRODUCED_AT_ORIGINAL"}

final = []
for r in claims:
    if not r["category"].startswith("SINGLE"):
        continue
    key = (r["folder"], r["claim_id"])
    first_verdict = (r.get("verdict") or "").split("(")[0].strip()
    v = checks.get(key)
    if v is None:
        verdict, satisfied, source = first_verdict, f'{r.get("satisfied")}/{r.get("reseeds")}', "first pass"
    else:
        vv = v["verifier_verdict"]
        verdict = REVISED_TO[key] if vv == "REVISED" else FIXED[vv]
        satisfied, source = str(v.get("satisfied") or "-"), "verified"
    final.append({"folder": r["folder"], "claim_id": r["claim_id"], "evidence": r["evidence"],
                  "self_flagged_by_repo": r["category"] == "SINGLE_RUN_SELF_FLAGGED",
                  "first_pass_verdict": first_verdict, "final_verdict": verdict,
                  "satisfied": satisfied, "source": source,
                  "error_class_found": (v or {}).get("error_class_found", [])})
final.sort(key=lambda x: (x["final_verdict"], x["folder"], x["claim_id"]))
(DATA / "final.json").write_text(json.dumps(final, indent=1) + "\n")

tot = collections.Counter()
for s in folders:
    for k in ("claims_total", "not_stochastic", "out_of_scope", "multi_run",
              "single_self_flagged", "single_unflagged", "unresolved"):
        tot[k] += int(s.get(k) or 0)
triage = json.loads((DATA / "triage.json").read_text())
tclass = collections.Counter(t["class"] for t in triage)
fv = collections.Counter(x["final_verdict"] for x in final)
changed = [x for x in final if x["first_pass_verdict"] == "FAILS_IN_SOME" and x["final_verdict"] != "FAILS_IN_SOME"]

print(f"triage: {len(triage)} folders  {dict(sorted(tclass.items()))}")
print(f"audited: {len(folders)} folders, {tot['claims_total']} claims")
for k in ("not_stochastic", "out_of_scope", "multi_run", "single_self_flagged", "single_unflagged", "unresolved"):
    print(f"  {k:22} {tot[k]}")
print(f"single-draw claims re-run: {len(final)}")
for k, n in sorted(fv.items(), key=lambda kv: -kv[1]):
    print(f"  {k:34} {n}")
first_fails = sum(x["first_pass_verdict"] == "FAILS_IN_SOME" for x in final)
print(f"first-pass FAILS_IN_SOME: {first_fails}; changed on verification: {len(changed)}")

if "--markdown" in sys.argv:
    print("\n| folder | claim | final verdict | satisfied | first pass | repo flagged |\n|---|---|---|---|---|---|")
    for x in final:
        print(f'| {x["folder"]} | {x["claim_id"]} | {x["final_verdict"]} | {x["satisfied"]} | '
              f'{x["first_pass_verdict"]} | {"yes" if x["self_flagged_by_repo"] else ""} |')
