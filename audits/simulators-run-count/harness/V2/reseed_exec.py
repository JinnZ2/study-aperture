"""Usage: python3 reseed_exec.py <module.py> <exact old line text> <new text with {s}> <seed> [<seed> ...]
Reads the module source from the work copy, replaces the seed constant (in memory only;
equivalent to editing that line in the copy), execs it as __main__, prints
'=== SEED s' followed by the module's stdout for each seed."""
import sys, io, contextlib, os
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
seeds = [int(x) for x in sys.argv[4:]]
src = open(path).read()
assert src.count(old) == 1, f"seed line not found exactly once: {old!r}"
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
for s in seeds:
    code = compile(src.replace(old, new.format(s=s)), path, "exec")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(code, {"__name__": "__main__"})
    print(f"=== SEED {s}"); print(buf.getvalue())
