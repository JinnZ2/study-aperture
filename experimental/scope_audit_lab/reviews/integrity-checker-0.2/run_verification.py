#!/usr/bin/env python3
"""Execute fixed repository tests and both CLI fixtures; write new artifacts."""

import argparse
import hashlib
import importlib.util
import io
import json
import platform
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


LAB = Path(__file__).resolve().parents[2]
ROOT = LAB.parents[1]
SPEC = importlib.util.spec_from_file_location("verified_checker_v02", LAB / "integrity_checker.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.events.append({"test": test.id(), "outcome": "PASSED"})

    def addFailure(self, test, error):
        super().addFailure(test, error)
        self.events.append({"test": test.id(), "outcome": "FAILED"})

    def addError(self, test, error):
        super().addError(test, error)
        self.events.append({"test": test.id(), "outcome": "ERROR"})


def cli(bundle):
    relative = str(bundle.relative_to(ROOT))
    argv = ["experimental/scope_audit_lab/integrity_checker.py", relative]
    proc = subprocess.run([sys.executable, "-I", *argv], cwd=ROOT,
                          capture_output=True, text=True, timeout=60, check=False)
    return {"argv_without_interpreter": ["-I", *argv], "exit_code": proc.returncode,
            "stderr": proc.stderr}, json.loads(proc.stdout)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True, help="New directory only.")
    args = parser.parse_args()
    out = Path(args.artifact_dir)
    out.mkdir(parents=True, exist_ok=False)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(LAB / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(suite)
    (out / "tests.log").write_text(log.getvalue(), encoding="utf-8")
    regressions = []
    for filename in (
        "assess.py", "vendored/false_agree.py", "vendored/provenance_graph.py",
        "vendored/safe_provenance.py", "vendored/conditional_claims.py",
    ):
        proc = subprocess.run([sys.executable, str(ROOT / filename), "selftest"],
                              cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
        regressions.append({"procedure": [filename, "selftest"], "exit_code": proc.returncode,
                            "stdout": proc.stdout, "stderr": proc.stderr})
    base = LAB / "examples/schema-draft-0.2/records.json"
    fixture = LAB / "examples/integrity-relevance-0.2/records.json"
    base_run, base_report = cli(base)
    demo_run, demo_report = cli(fixture)
    for name, report in (("base", base_report), ("relevance", demo_report)):
        (out / (name + "-report.json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (out / (name + "-report.md")).write_text(checker.markdown(report), encoding="utf-8")
    expected = json.loads(fixture.read_text())["expected_link_relevance"]
    observed = [{"owner_record_id": row["owner_record_id"], "status": row["link_relevance"]}
                for row in demo_report["assessment_link_relevance"]]
    protected = {
        "requirements/scope-audit-lab-0.2.md": "50a1bf3d5b556cdb08c4367b5e442cdd512b7f2fbda9498383645b4c8e57a10d",
        "schemas/draft-0.1/evidence.schema.json": "db9d9902bd943e80cdccc660b22dbb12192732adc5bfcd5aecb0c4f801975775",
        "examples/schema-draft-0.1/records.json": "4d152cf48c629ff0e96857fe40716844669ef445f6f6d472fcac57c5192e9f90",
        "examples/schema-draft-0.2/records.json": "00f09d8add5d159924f6dd02c577af7c61492d13c9e392d5be6dbccb1980394a",
    }
    preserved = {name: {"expected": value, "observed": digest(LAB / name)}
                 for name, value in protected.items()}
    checks = {
        "unit_tests_successful": result.wasSuccessful(),
        "parent_regressions_successful": all(r["exit_code"] == 0 for r in regressions),
        "base_gaps_preserved": (
            base_run["exit_code"] == 1 and base_report["summary"]["assessment_link_count"] == 0
            and base_report["summary"]["finding_counts"] == {"ERROR": 0, "UNKNOWN": 16, "INFO": 0}
        ),
        "relevance_cli_reports_gaps": demo_run["exit_code"] == 1,
        "all_three_relevance_scenarios_match": expected == observed,
        "no_scientific_support_promoted": all(
            not r["scientific_support_established"] and not r["property_alignment_established"]
            and not r["verdict_mapping_established"] for r in demo_report["assessment_link_relevance"]
        ),
        "protected_artifacts_unchanged": all(v["expected"] == v["observed"] for v in preserved.values()),
    }
    paths = [
        LAB / "integrity_checker.py", Path(__file__),
        Path(__file__).with_name("build_relevance_example.py"), fixture, base,
        LAB / "schemas/draft-0.1/evidence.schema.json",
        LAB / "schemas/draft-0.2/extensions.schema.json",
        *sorted((LAB / "tests").glob("test_*.py")),
    ]
    evidence = {
        "artifact_kind": "ASSESSMENT_LINK_RELEVANCE_VERIFICATION",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "checker_version": checker.VERSION,
        "checks": checks, "examined_sha256": {str(p.relative_to(ROOT)): digest(p) for p in paths},
        "unit_tests": {"count": result.testsRun, "successful": result.wasSuccessful(),
                       "events": result.events,
                       "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
                       "errors": [{"test": str(t), "traceback": s} for t, s in result.errors]},
        "parent_regressions": regressions,
        "base_cli": {**base_run, "summary": base_report["summary"]},
        "relevance_cli": {**demo_run, "summary": demo_report["summary"],
                          "expected_links": expected, "observed_links": observed},
        "protected_artifacts": preserved,
        "artifact_sha256": {p.name: digest(p) for p in sorted(out.iterdir())},
        "limits": [
            "Author-generated synthetic fixtures and implementation; not an independent audit.",
            "Literal subject/version/selector links, not free-form meaning or scientific support, were checked.",
            "Old verification artifacts are retained; baseline acceptance matrix and prototype compatibility remain unestablished.",
        ],
    }
    (out / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "test_count": result.testsRun,
                      "relevance_summary": demo_report["summary"]}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
