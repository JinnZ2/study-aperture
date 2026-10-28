# run from floor-resilience copy. Regenerates the EXAMPLE site at other seeds
# (replacing make_example.py:19 R = random.Random(20261023)) into scratch files.
import sys, re, subprocess, datetime as dt, statistics as st, pathlib
sys.path.insert(0, '.')
from floor_resilience.schema import load_site
from floor_resilience import scrap as S
src = pathlib.Path('examples/make_example.py').read_text()
out = pathlib.Path('../../harness/fr_sites'); out.mkdir(exist_ok=True)
codes = S.load_map()
seeds = [20261023] + list(range(1, 21))
res = []
for s in seeds:
    p = out / f'site_{s}.yaml'
    code = src.replace('R = random.Random(20261023)', f'R = random.Random({s})').replace(
        'OUT = Path(__file__).with_name("example_site.yaml")', f'OUT = Path({str(p.resolve())!r})')
    sp = out / f'mk_{s}.py'; sp.write_text(code)
    subprocess.run([sys.executable, str(sp)], check=True, capture_output=True)
    site, gaps = load_site(p)
    ld = dt.date(2025, 3, 1); win = dt.timedelta(days=S.FLAG_WINDOW_DAYS)
    b = S._window_share(site.scrap, codes, 'lathe-2', ld - win, ld)
    a = S._window_share(site.scrap, codes, 'lathe-2', ld, ld + win)
    flags, _ = S.departure_flags(site, codes)
    flagged = any(f.machine == 'lathe-2' for f in flags) if flags else False
    res.append((s, round(b.share*100), round(a.share*100), flagged))
    print(res[-1])
r = res[1:]
d = [x[2]-x[1] for x in r]
print('before', min(x[1] for x in r), st.median([x[1] for x in r]), max(x[1] for x in r))
print('after', min(x[2] for x in r), st.median([x[2] for x in r]), max(x[2] for x in r))
print('rise', min(d), st.median(d), max(d), 'rise>0', sum(x>0 for x in d), 'flagged', sum(x[3] for x in r))
