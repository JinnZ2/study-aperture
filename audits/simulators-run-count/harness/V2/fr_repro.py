import sys; sys.path.insert(0, '.')
from floor_resilience.schema import load_site
from floor_resilience import scrap
site, _ = load_site(sys.argv[1]); codes = scrap.load_map()
fl, n = scrap.departure_flags(site, codes)
for f in fl: print(f)
import datetime as dt
win = dt.timedelta(days=180); ld = dt.date(2025,3,1)
b = scrap._window_share(site.scrap, codes, 'lathe-2', ld-win, ld); a = scrap._window_share(site.scrap, codes, 'lathe-2', ld, ld+win)
print('before', round(b.share,4), 'after', round(a.share,4), 'checked', n)
