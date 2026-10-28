"""M1a in scope: dataset fixed at seed 3 (the claim's "this dataset"); vary ONLY the observer draw.
Run from inside a copy of Simulators/model-ecology:  python3 -B m1a_observer_only.py"""
import io, re, contextlib, demo, meta_engine
orig = meta_engine.sweep_observers
def run(s):
    demo.sweep_observers = lambda n, s=s: orig(n, seed=s)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        demo.main()
    return eval(re.search(r"winners by observer = (\{.*\})", buf.getvalue()).group(1))
print("observer seed 7 (orig):", run(7))
h = [run(s).get("hilbert", 0) for s in range(100, 120)]
print("hilbert votes /32 at observer seeds 100..119:", h)
