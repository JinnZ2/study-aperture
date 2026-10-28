import sys, json
sys.path.insert(0, sys.argv[1])
import s9_corpus_position_filter as S
ws=(0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0)
for s in sys.argv[2:]:
    s=int(s); rows=[S.relevance_test(w, seed=s) for w in ws]; rows=[r for r in rows if r]
    cc=[round(r["corr_with_content"],4) for r in rows]
    print(json.dumps(dict(seed=s, corr_content=cc, peak_abs=max(abs(c) for c in cc), peak_signed=max(cc))))
