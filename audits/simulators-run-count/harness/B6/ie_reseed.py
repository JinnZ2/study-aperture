# Rerun every PHASE-6 forward simulation of instrument-epistemology at other seeds.
# Patches instrum.simulation.inject_and_recover's default seed (17) in-process; repo files untouched.
import sys, os, runpy, io, contextlib, re, statistics as st
root = sys.argv[1]; sys.path.insert(0, os.path.join(root, "src"))
import instrum.simulation as sim
orig = sim.inject_and_recover
res = {}
for seed in [17] + list(range(1, 21)):
    def patched(*a, **k):
        k["seed"] = seed; return orig(*a, **k)
    sim.inject_and_recover = patched
    for e in ["lidar_biomass","edna_biodiversity","camera_trap_density","satellite_sst","isotope_diet","seismometer"]:
        buf = io.StringIO()
        cwd=os.getcwd(); os.chdir(os.path.join(root,"experiments",e))
        try:
            with contextlib.redirect_stdout(buf):
                runpy.run_path(os.path.join(root,"experiments",e,"run.py"), run_name="__main__")
        finally: os.chdir(cwd)
        for line in buf.getvalue().splitlines():
            if line.startswith("PHASE 6"):
                m = re.search(r"recovered ([\d.]+).*-> (\S+)", line)
                key = e + ":" + line.split()[1]
                res.setdefault(key, []).append((seed, float(m.group(1)), m.group(2)))
for k, v in res.items():
    vals = [x[1] for x in v[1:]]
    print(k, "orig", v[0][1:], "reseeds K=%d min %.4f med %.4f max %.4f" % (len(vals), min(vals), st.median(vals), max(vals)),
          "verdicts", sorted(set(x[2] for x in v[1:])))
