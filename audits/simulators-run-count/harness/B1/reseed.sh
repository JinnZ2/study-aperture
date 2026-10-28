#!/bin/bash
# usage: reseed.sh <dir> <file.py> <line> <sed-expr-with-SEED> <outdir> seeds...
d=$1; f=$2; l=$3; ex=$4; out=$5; shift 5
out=$(realpath -m $out); mkdir -p $out
for s in "$@"; do
  e=${ex//SEED/$s}
  sed "${l}s/${e}/" $d/$f > $d/_rs_${s}_$f
  (cd $d && python3 _rs_${s}_$f > $out/$s.txt 2>&1; echo "exit=$?" >> $out/$s.txt)
  rm $d/_rs_${s}_$f
done
