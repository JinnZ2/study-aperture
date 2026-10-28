#!/usr/bin/env bash
# Run every check in the repository. CC0. Python 3 stdlib only; no network.
# Exit 0 only if every step passes. Used locally and by .github/workflows/checks.yml.
set -u
cd "$(dirname "$0")"
PY="${PYTHON:-python3}"
fail=0

step() {  # step <expected-exit> <label> <command...>
  local want="$1" label="$2"; shift 2
  local out code
  out="$("$@" 2>&1)"; code=$?
  if [ "$code" -eq "$want" ]; then
    echo "ok    $label"
  else
    echo "FAIL  $label (exit $code, expected $want)"
    echo "$out" | sed 's/^/      /'
    fail=1
  fi
}

# core toolkit
step 0 "assess.py selftest"                  "$PY" assess.py selftest
for f in provenance_graph false_agree conditional_claims safe_provenance; do
  step 0 "vendored/$f.py selftest"           bash -c "cd vendored && '$PY' $f.py selftest"
done
step 0 "example: reproducibility-model recompute" "$PY" examples/reproducibility-model/recompute.py selftest
step 0 "repo integrity tests"                "$PY" -m unittest discover -s tests

# scope audit lab
step 0 "lab: integrity checker tests"        "$PY" -m unittest discover -s experimental/scope_audit_lab/tests
# The draft-0.2 example bundle is deliberately incomplete: exit 1 (gaps recorded) is the correct result.
step 1 "lab: checker on draft-0.2 example"   "$PY" experimental/scope_audit_lab/integrity_checker.py \
                                               experimental/scope_audit_lab/examples/schema-draft-0.2/records.json
step 0 "lab: tolman-vi-2026-10-27 tests"     bash -c "cd experimental/scope_audit_lab/reviews/tolman-vi-2026-10-27 && '$PY' -m unittest test_case.py"
step 0 "lab: tolman-vi-phase-trace-0.1 tests" bash -c "cd experimental/scope_audit_lab/reviews/tolman-vi-phase-trace-0.1 && '$PY' -m unittest test_trace.py"

if [ "$fail" -eq 0 ]; then echo "ALL CHECKS PASSED"; else echo "CHECKS FAILED"; fi
exit "$fail"
