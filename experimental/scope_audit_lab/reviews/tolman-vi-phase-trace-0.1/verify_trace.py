#!/usr/bin/env python3
"""Record fixed tests, deterministic isolated offline reproduction, and hashes."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
LAB=HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default="test-verification.json")
    args=parser.parse_args()
    if Path(args.output).name!=args.output:
        raise ValueError("A plain new filename is required.")
    commands=[
        ["-m","unittest","discover","-s",str(HERE),"-p","test_trace.py","-v"],
        ["-m","unittest","discover","-s",str(HERE.parent/"tolman-vi-2026-10-27"),"-p","test_case.py","-v"],
        ["-m","unittest","discover","-s",str(LAB/"tests"),"-v"],
        *[[name,"selftest"] for name in ["assess.py","vendored/false_agree.py","vendored/provenance_graph.py",
                                       "vendored/safe_provenance.py","vendored/conditional_claims.py"]],
    ]
    procedures=[]
    for command in commands:
        p=subprocess.run([sys.executable,*command],cwd=ROOT,text=True,capture_output=True,timeout=90)
        match=re.search(r"Ran (\d+) tests",p.stderr)
        procedures.append({"argv_without_interpreter":command,"exit_code":p.returncode,
                           "test_count":int(match[1]) if match else None,"stdout":p.stdout,"stderr":p.stderr})
    with tempfile.TemporaryDirectory(prefix="tolman-phase-trace-") as temp:
        directory=Path(temp)/"new-output"
        p=subprocess.run([sys.executable,"-I",str(HERE/"run_trace.py"),"--output-dir",str(directory)],
                         cwd=ROOT,text=True,capture_output=True,timeout=90)
        comparisons={}
        if p.returncode==0:
            for name in ["computed.json","evidence-bundle.json","integrity-report.json","integrity-report.md"]:
                comparisons[name]={"recorded_sha256":digest(HERE/"artifacts"/name),
                                   "rerun_sha256":digest(directory/name)}
                comparisons[name]["identical"]=comparisons[name]["recorded_sha256"]==comparisons[name]["rerun_sha256"]
        rerun={"exit_code":p.returncode,"stdout":p.stdout,"stderr":p.stderr,"deterministic_outputs":comparisons,
               "limits":"Run timestamp is intentionally not compared; reproduction is not independent scientific confirmation."}
    manifest=json.loads((HERE/"artifacts/verification.json").read_text())
    matches=all(digest(LAB/name)==value for name,value in manifest["examined_sha256"].items())
    outputs_match=all(digest(HERE/"artifacts"/name)==value for name,value in manifest["output_sha256"].items())
    bundle=json.loads((HERE/"artifacts/evidence-bundle.json").read_text())
    records={r["record_id"]:r for r in bundle["records"]}
    mappings=json.loads((HERE/"mappings.json").read_text())
    mapping_ids=[m["mapping_id"] for m in mappings["mappings"]]
    mapping_links_ok=len(mapping_ids)==len(set(mapping_ids)) and mappings["status"]=="DRAFT_NOT_EXECUTABLE"
    for m in mappings["mappings"]:
        r=records[m["assessment_id"]]
        mapping_links_ok=bool(mapping_links_ok and r["payload"]["criteria"][0]["criterion_id"]==m["criterion_id"]
                              and r["payload"]["criteria"][0]["exact_rule"]==m["exact_rule"]
                              and r["payload"]["criteria"][0]["version"]["value"]==mappings["common_binding"]["criterion_version"]
                              and r["payload"]["subjects"][0]["subject"]["record_id"]==mappings["common_binding"]["subject_id"]
                              and r["payload"]["subjects"][0]["selector"]["value"]==mappings["common_binding"]["selector"]
                              and r["record_version"]["value"]==mappings["common_binding"]["subject_version"])
    checked={"fixed_procedures_exit_zero":all(p["exit_code"]==0 for p in procedures),
             "isolated_rerun_exit_zero":p.returncode==0,"deterministic_outputs_match":len(comparisons)==4 and all(x["identical"] for x in comparisons.values()),
             "code_input_hashes_match":matches,"output_hashes_match":outputs_match,
             "draft_mapping_id_version_links_match":mapping_links_ok}
    examined=[Path(__file__),HERE/"test_trace.py",HERE/"mappings.json",HERE/"source-review.json",
              HERE/"capture_sources.py",HERE.parent/"tolman-vi-2026-10-27/test_case.py",
              *sorted((LAB/"tests").glob("test*.py")),
              *[ROOT/name for name in ["assess.py","vendored/false_agree.py","vendored/provenance_graph.py",
                                      "vendored/safe_provenance.py","vendored/conditional_claims.py"]]]
    result={"executed_at_utc":datetime.now(timezone.utc).isoformat(),"checks":checked,
            "procedures":procedures,"isolated_rerun":rerun,
            "examined_sha256":{str(path.relative_to(ROOT)):digest(path) for path in examined},
            "case_artifact_sha256":{p.name:digest(p) for p in (HERE/"artifacts").iterdir()},
            "limits":["Tests authored in the same process, not independent scientific validation.",
                      "Mapping link checks do not execute scientific mappings or establish property alignment."]}
    with (HERE/args.output).open("x") as f:
        json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps({"checks":checked,"test_counts":[p["test_count"] for p in procedures[:3]]},indent=2))
    return 0 if all(checked.values()) else 1


if __name__=="__main__":
    raise SystemExit(main())
