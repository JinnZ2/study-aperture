import re,glob,statistics as st
for f in sorted(glob.glob('out/c013/*.txt'), key=lambda x:int(x.split('/')[-1][:-4])):
    t=open(f).read(); s=f.split('/')[-1][:-4]
    pat=r'^\s+(\d\.\d\d)\s+(-?[\d.]+)\s+([\d.]+)\s+(-?[\d.]+)$'
    r1=re.findall(pat,t.split('regime 1')[1].split('regime 2')[0],re.M)
    r2=re.findall(pat,t.split('regime 2')[1].split('regime 3')[0],re.M)
    r3=re.findall(r'^    (\S.*?)\s+(-?[\d.]+e[+-]\d+)\s+(-?[\d.]+)$',t.split('regime 3')[1].split('**All')[0],re.M)
    dev1=max(abs(float(a[3])-1/(1+float(a[0])**2)) for a in r1)
    dev2=max(abs(float(a[3])-(1-2*float(a[0]))) for a in r2)
    rat1=[float(a[3]) for a in r1[1:]]; rat2=[float(a[3]) for a in r2[1:]]; rat3=[float(a[2]) for a in r3[1:]]
    flat=all(0<=x<1 for x in rat1+rat2+rat3)
    print(s,round(dev1,4),round(dev2,4),rat3,flat, t.strip().split('\n')[-1])
