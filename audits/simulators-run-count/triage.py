"""C2 triage: static scan of Simulators for randomness, seeding, and multi-run patterns.
Reads text only; imports nothing from the scanned tree. Usage: python3 -I triage.py <repo> <out.json>"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2])

STOCH = re.compile(r"^\s*(import random\b|from random import|import numpy)|np\.random\.|numpy\.random|default_rng\(|random\.Random\(|\brandom\.(random|gauss|uniform|choice|choices|shuffle|sample|randint|normalvariate|expovariate|betavariate|lognormvariate)\(", re.M)
SEEDED = re.compile(r"\.seed\(\s*\w|default_rng\(\s*[\w]|random\.Random\(\s*[\w]|\b(SEED|seed)\s*[:=]\s*\d")
MULTI = re.compile(
    r"for\s+\w*seed\w*\s+in\b|\bseeds\s*=|\bn_?seeds\b|\bn_?runs\b|\bn_?trials\b|\bN_TRIALS\b|\bn_?draws\b|\bn_?reps\b|"
    r"\breplicat\w*|\bensemble\w*|monte.?carlo|\bbootstrap\w*|\bpermutation\w*|\bnull_?distribution|\bn_?boot\b|\bn_?perm\b|"
    r"for\s+\w+\s+in\s+range\(\s*(N_|n_|NUM_|num_)\w*(RUN|run|TRIAL|trial|SEED|seed|DRAW|draw|REP|rep)", re.I)
SELF_FLAG = re.compile(r"\bone draw\b|\bsingle seed\b|\bone seed\b|\bsingle draw\b|\bsingle run\b|\bone run\b|\bn\s*=\s*1\b|\bN_OF_1\b|seed-?dependen\w*|\bacross seeds\b|\bper seed\b|\b\d+\s*/\s*\d+\s+seeds\b|\bin \d+ of \d+ seeds\b|\b\d+ seeds\b", re.I)
CLAIM_ID = re.compile(r"\b[A-Z][A-Z0-9]{1,5}_\d{3}\b")
ILLUS = re.compile(r"\bILLUSTRATIVE\b|\bCONSTRUCTED\b|\bPLACEHOLDER\b")

folders = defaultdict(lambda: {"py": 0, "stoch": [], "seeded": [], "multi": [], "claim_files": [],
                               "claim_ids": set(), "self_flags": [], "illustrative_md": 0})
for p in sorted(ROOT.rglob("*")):
    if ".git" in p.parts or not p.is_file():
        continue
    rel = p.relative_to(ROOT)
    top = rel.parts[0] if len(rel.parts) > 1 else "(root)"
    if top in ("legacy", "archive"):  # archived drops: out of scope
        continue
    f = folders[top]
    try:
        text = p.read_text(errors="replace")
    except OSError:
        continue
    if p.suffix == ".py":
        f["py"] += 1
        if STOCH.search(text):
            f["stoch"].append(str(rel))
            if SEEDED.search(text):
                f["seeded"].append(str(rel))
            if MULTI.search(text):
                f["multi"].append(str(rel))
    elif p.suffix == ".md":
        if p.name in ("CLAIM_TABLE.md", "CLAIMS.md"):
            f["claim_files"].append(str(rel))
            f["claim_ids"].update(CLAIM_ID.findall(text))
        if ILLUS.search(text):
            f["illustrative_md"] += 1
        for m in SELF_FLAG.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            f["self_flags"].append(f"{rel}:{line}: {m.group(0)}")

rows = []
for name, f in sorted(folders.items()):
    stoch, multi = set(f["stoch"]), set(f["multi"])
    if not f["py"]:
        cls = "NO_CODE"
    elif not stoch:
        cls = "DETERMINISTIC_ONLY"
    elif stoch <= multi:
        cls = "STOCHASTIC_ALL_MULTI"
    elif stoch & multi:
        cls = "STOCHASTIC_MIXED"
    else:
        cls = "STOCHASTIC_NO_MULTI"
    rows.append({"folder": name, "class": cls, "py": f["py"], "stochastic_files": sorted(stoch),
                 "seeded_files": sorted(f["seeded"]), "multi_run_files": sorted(multi),
                 "stochastic_without_multi": sorted(stoch - multi),
                 "claim_files": f["claim_files"], "claim_count": len(f["claim_ids"]),
                 "self_flags": f["self_flags"][:40], "illustrative_md": f["illustrative_md"]})
OUT.write_text(json.dumps(rows, indent=1))
from collections import Counter
c = Counter(r["class"] for r in rows)
print("folders:", len(rows), dict(c))
print("claims in stochastic folders without multi-run in some file:",
      sum(r["claim_count"] for r in rows if r["class"] in ("STOCHASTIC_NO_MULTI", "STOCHASTIC_MIXED")))
for r in rows:
    if r["class"] in ("STOCHASTIC_NO_MULTI", "STOCHASTIC_MIXED"):
        print(f'{r["class"]:22} {r["folder"]:38} py={r["py"]:3} stoch={len(r["stochastic_files"]):2} '
              f'no_multi={len(r["stochastic_without_multi"]):2} claims={r["claim_count"]:3} selfflags={len(r["self_flags"])}')
