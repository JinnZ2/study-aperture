#!/usr/bin/env python3
"""Record fixed authoring tests, parent regressions, and final artifact digests."""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default="test-verification.json",help="New filename within the review directory.")
    args=parser.parse_args()
    if Path(args.output).name != args.output:
        raise ValueError("A plain new filename is required.")
    commands = [
        ["-m", "unittest", "discover", "-s", str(HERE), "-p", "test_case.py", "-v"],
        ["-m", "unittest", "discover", "-s", "experimental/scope_audit_lab/tests", "-v"],
        *[[name, "selftest"] for name in ("assess.py","vendored/false_agree.py","vendored/provenance_graph.py",
                                         "vendored/safe_provenance.py","vendored/conditional_claims.py")],
        ["assess.py","check","--file",str(HERE/"study-record.json")],
    ]
    results=[]
    for command in commands:
        p=subprocess.run([sys.executable,*command],cwd=ROOT,text=True,capture_output=True,timeout=60,check=False)
        results.append({"argv_without_interpreter":command,"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
    manifest=json.loads((HERE/"artifacts/verification.json").read_text())
    code_and_inputs_ok=all(hashlib.sha256((HERE.parents[1]/name).read_bytes()).hexdigest()==value
                           for name,value in manifest["examined_sha256"].items())
    artifacts_ok=all(hashlib.sha256((HERE/"artifacts"/name).read_bytes()).hexdigest()==value
                     for name,value in manifest["output_sha256"].items())
    all_tests_passed=all(r["exit_code"]==0 for r in results)
    result={
        "recorded_at_utc":datetime.now(timezone.utc).isoformat(),
        "all_fixed_procedures_completed_with_exit_zero":all_tests_passed,
        "case_code_input_hashes_match":code_and_inputs_ok,"case_output_hashes_match":artifacts_ok,
        "procedures":results,
        "review_procedure_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "case_test_source_sha256":hashlib.sha256((HERE/"test_case.py").read_bytes()).hexdigest(),
        "case_manifest_sha256":hashlib.sha256((HERE/"artifacts/verification.json").read_bytes()).hexdigest(),
        "toolkit_record_sha256":hashlib.sha256((HERE/"study-record.json").read_bytes()).hexdigest(),
        "case_artifact_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((HERE/"artifacts").iterdir()) if p.is_file()},
        "limits":["Authoring tests of fixed selected probes, not independent scientific reproduction or whole-paper validation."],
    }
    with (HERE/args.output).open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps({"all_tests_passed":all_tests_passed,"code_and_inputs_ok":code_and_inputs_ok,
                      "artifacts_ok":artifacts_ok},indent=2))
    return 0 if all_tests_passed and code_and_inputs_ok and artifacts_ok else 1


if __name__=="__main__":
    raise SystemExit(main())
