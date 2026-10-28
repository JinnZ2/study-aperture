import sys, numpy as np
sys.path.insert(0, '.')
from l0_physics_causality import *
out=set()
for s in [0]+list(range(1,21)):
    np.random.seed(s)
    w=PhysicalWorld(mass=1.0,max_speed=2.0)
    t,f=ai_hallucinated_plan(200)
    c,v,p=l0_grounding_inspector(t,f,w,0.05)
    sp=np.linalg.norm(np.diff(c,axis=0),axis=1)/0.05
    pw=ProbabilisticWorld(); c2,lp=l0_probabilistic_inspector(t,f,pw,0.05)[:2]
    r=(int(np.sum(v)), round(float(sp.max()),4), round(float(c[-1,1]),4), round(float(np.sum(lp)),2))
    out.add(r); print(s,r)
print("distinct:",len(out))
# GL_L0_003 sweep reseeds
bad=0
for s in range(1,21):
    rng=np.random.default_rng(s); w=PhysicalWorld()
    m=0
    for _ in range(200):
        _,nv=w.apply_physics(rng.standard_normal(2)*3,rng.standard_normal(2)*3,rng.standard_normal(2)*1000,w.dt)
        m=max(m,np.linalg.norm(nv))
    bad+= m>w.max_speed+1e-9
    print('sweep seed',s,'max|v|',m)
print('sweep seeds failing',bad,'/20')
