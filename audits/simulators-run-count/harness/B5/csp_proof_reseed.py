import sys, os, json
sys.path.insert(0, os.getcwd())
import p3_comprehension as P
corpus = P.read_corpus("fixtures/corpus")
docs = dict(corpus)
mode = sys.argv[1]; seeds=[int(x) for x in sys.argv[2].split(",")]
out={}
for sd in seeds:
    if mode == "control":   # fixture c fixed (made with seed 0), control cipher reseeded
        c = corpus
    else:                   # regen: c = encipher(b, sd) and control at sd
        c = [("a_units.txt", docs["a_units.txt"]), ("b_protocol.txt", docs["b_protocol.txt"]), ("c_ciphered.txt", P.encipher(docs["b_protocol.txt"], sd))]
    r = P.check(c, sd)
    out[sd] = {"verdict": r["verdict"], "pairs": [(p["a"][:1]+p["b"][:1], round(p["delta"],4), p["verdict"]) for p in r["pairs"]],
               "fixed_points": sum(1 for x,y in zip(P.ALPHABET, P.cipher_alphabet(sd)) if x==y)}
print(json.dumps(out))
