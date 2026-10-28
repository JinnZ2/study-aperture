# run from floor-resilience copy: python3 ../../harness/fr_drain.py
import sys, statistics as st
sys.path.insert(0, '.')
from floor_resilience import drain_sim as ds
seeds = [1000] + [1000 + 1013*i for i in range(1, 21)]
rows = []
for s in seeds:
    a = ds.simulate(ds.plant_a(), seed=s, rng='js'); b = ds.simulate(ds.plant_b(), seed=s, rng='js')
    rows.append((s, round(a.scrap_change*100), round(b.scrap_change*100), a.indicator_month, a.alarm_month, a.lead_time))
    print(rows[-1])
r = rows[1:]
for i, name in [(1,'A%'),(2,'B%'),(5,'lead')]:
    v = [x[i] for x in r if x[i] is not None]
    print(name, 'min', min(v), 'med', st.median(v), 'max', max(v), 'none', sum(1 for x in r if x[i] is None))
print('A==48', sum(x[1]==48 for x in r), 'B==7', sum(x[2]==7 for x in r), 'lead==14', sum(x[5]==14 for x in r), 'A>B', sum(x[1]>x[2] for x in r), 'all three exact', sum(x[1]==48 and x[2]==7 and x[5]==14 for x in r))
