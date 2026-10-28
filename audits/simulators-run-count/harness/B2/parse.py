import re, sys, json, statistics as st
def blocks(fn):
    txt=open(fn).read()
    out={}
    for b in txt.split("=== SEED ")[1:]:
        s,rest=b.split("\n",1); out[int(s)]=rest
    return out
def verdicts(t):
    return {m.group(1).strip():m.group(2)=="HOLDS" for m in re.finditer(r"^\s+(C\d(?: v\d)?)\s+(HOLDS|REFUTED)",t,re.M)}
res={}
# CGT
for fn,tag in (("out_cgt_orig.txt","orig"),("out_cgt.txt","re")):
    for s,t in blocks(fn).items():
        v=verdicts(t)
        dc=re.search(r"decoupled\s+coh=([\d.]+) acc=([\d.]+)",t); cp=re.search(r"coupled\s+coh=([\d.]+) acc=([\d.]+)",t)
        caps=[(float(a),float(b)) for a,b in re.findall(r"cap=\d+\s+coh=([\d.]+) acc=([\d.]+)",t)]
        sl=re.search(r"acc_slope=([-\d.e]+), coh_slope=([-\d.e]+)",t)
        lat=re.findall(r"mean scored lat = ([\d.]+)",t)
        gens=re.findall(r"gen=(\d+)\s+coh=([\d.]+) acc=([\d.]+)",t)
        res.setdefault("cgt",{})[s]=dict(v=v,dc_coh=float(dc[1]),dc_acc=float(dc[2]),cp_gap=round(abs(float(cp[1])-float(cp[2])),3),
            cap_dacc=round(abs(caps[2][1]-caps[0][1]),3),cap_coh=[c for c,_ in caps],acc_slope=float(sl[1]),coh_slope=float(sl[2]),
            lat_cp=float(lat[0]),lat_dc=float(lat[1]))
for fn in ("out_adt_orig.txt","out_adt.txt"):
    for s,t in blocks(fn).items():
        v=verdicts(t); r={m[0]:(int(m[1]),int(m[2])) for m in re.findall(r"route=(\w+)\s+total_lat=(\d+) dropouts=(\d+)",t)}
        e1=[float(x) for x in re.findall(r"d=[\d.]+\s+lat=([\d.]+)",t)]
        rat=[float(x) for x in re.findall(r"ratio=([\d.]+)",t)]
        res.setdefault("adt",{})[s]=dict(v=v,routes=r,ratios=rat)
for fn in ("out_sdt_orig.txt","out_sdt.txt"):
    for s,t in blocks(fn).items():
        v=verdicts(t); eq=[float(x) for x in re.findall(r"f=[\d.]+\s+m_eq=([\d.]+)",t)]
        d=re.search(r"Δ\(f alone\)=([-\d.]+)\s+Δ\(β↓ alone\)=([-\d.]+)\s+Δ\(both\)=([-\d.]+)",t)
        e1=re.search(r"gen100=([\d.]+) → end=([\d.]+)",t)
        res.setdefault("sdt",{})[s]=dict(v=v,eq=eq,df=float(d[1]),db=float(d[2]),dboth=float(d[3]),end=float(e1[2]))
json.dump(res,open("parsed.json","w"),indent=0,default=str)
def summ(key,claim,valfn):
    d=res[key]; orig=min(d) if key!="x" else None
    o={"cgt":11,"adt":7,"sdt":3}[key]
    re_=[s for s in d if s!=o]
    sat=sum(d[s]["v"][claim] for s in re_)
    vals=[valfn(d[s]) for s in re_]
    print(f"{key} {claim}: orig={d[o]['v'][claim]} origval={valfn(d[o])} sat={sat}/{len(re_)} min={min(vals)} med={st.median(vals)} max={max(vals)}")
for c,f in (("C1",lambda r:r["dc_acc"]),("C2 v1",lambda r:r["cap_coh"][2]-r["cap_coh"][0]),("C2 v2",lambda r:r["cap_dacc"]),("C3 v1",lambda r:r["lat_dc"]),("C3 v2",lambda r:round(r["lat_dc"]-r["lat_cp"],2)),("C4 v1",lambda r:r["acc_slope"]),("C4 v2",lambda r:r["acc_slope"])):
    summ("cgt",c,f)
summ("adt","C2",lambda r:r["routes"]["random"][0]-r["routes"]["deepest"][0])
for c in ("C1","C3","C4"): summ("adt",c,lambda r:r["ratios"][1])
for c,f in (("C1",lambda r:r["end"]),("C2",lambda r:r["eq"][4]),("C3",lambda r:r["eq"][7]),("C4",lambda r:round(r["dboth"]/max(r["df"]+r["db"],1e-9),2))):
    summ("sdt",c,f)
