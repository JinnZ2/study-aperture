# population+corpus fixed at seed 31/32; only the item/noise rng (Random(seed)) varies
import sys, json
sys.path.insert(0, sys.argv[1])
import s9_corpus_position_filter as S
op, oc = S.population, S.corpus
S.population = lambda n=6000, coupling=0.7, seed=17: op(n=n, coupling=coupling, seed=31)
S.corpus = lambda pop, seed=23: oc(pop, seed=32)
ws=(0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0)
for s in map(int, sys.argv[2:]):
    cc=[round(S.relevance_test(w, seed=s)["corr_with_content"],4) for w in ws]
    print(json.dumps(dict(item_seed=s, corr_content=cc, peak_abs=max(abs(c) for c in cc))))
