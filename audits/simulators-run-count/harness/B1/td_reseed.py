import sys, statistics as st
sys.path.insert(0, sys.argv[1]); import power as P
seeds=[1000+i for i in range(20)]
for n in (20,40,160):
    a=[P.order_recovery(n,P.PROFILE,seed=s)["exact_order"] for s in seeds]
    b=[P.first_to_drop(n,P.PROFILE,seed=s+2)["recovered_uniquely"] for s in seeds]
    c=[P.pair_recovery(n,0.4,0.6,seed=s+1)["accuracy_on_decided"] for s in seeds]
    print(n,"exact",min(a),st.median(a),max(a),"| first",min(b),st.median(b),max(b),"| pair",min(c),st.median(c),max(c))
a=[P.order_recovery(20,P.PROFILE,seed=s)["exact_order"] for s in seeds]; print("exact<0.05 at n20:",sum(x<0.05 for x in a))
for n in (10,20): print("pair",n,[round(P.pair_recovery(n,0.4,0.6,seed=s+1)["accuracy_on_decided"],3) for s in seeds])
print("pair gap.1 n80",[round(P.pair_recovery(80,0.45,0.55,seed=s+1)["accuracy_on_decided"],3) for s in seeds])
