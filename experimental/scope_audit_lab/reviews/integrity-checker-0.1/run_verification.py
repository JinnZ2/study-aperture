#!/usr/bin/env python3
"""Reproduce fixed repository tests and an example report; stdlib authoring tool.

This script executes only the repository's explicitly named test programs.
Unlike integrity_checker.py, it is a verification runner, not a submitted-data
checker. It never executes commands named by an input evidence record.
"""

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
SPEC = importlib.util.spec_from_file_location("verified_integrity_checker", LAB / "integrity_checker.py")
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", required=True, help="New directory, never overwrite existing artifacts.")
    args = parser.parse_args()
    out = Path(args.artifact_dir)
    out.mkdir(parents=True, exist_ok=False)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(LAB / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(suite)
    regressions = []
    for filename in (
        "assess.py", "vendored/false_agree.py", "vendored/provenance_graph.py",
        "vendored/safe_provenance.py", "vendored/conditional_claims.py",
    ):
        proc = subprocess.run([sys.executable, str(ROOT / filename), "selftest"],
                              cwd=ROOT, capture_output=True, text=True, timeout=60, check=False)
        regressions.append({
            "procedure": [filename, "selftest"], "exit_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr,
        })

    # Public CLI demonstration, not an in-memory substitute for the delivered CLI.
    example = LAB / "examples/schema-draft-0.2/records.json"
    relative_example = str(example.relative_to(ROOT))
    command = [sys.executable, "experimental/scope_audit_lab/integrity_checker.py", relative_example]
    proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                          timeout=60, check=False)
    report = json.loads(proc.stdout)
    report_bytes = (json.dumps(report, indent=2, allow_nan=False) + "\n").encode()
    markdown_bytes = checker.markdown(report).encode()
    (out / "example-report.json").write_bytes(report_bytes)
    (out / "example-report.md").write_bytes(markdown_bytes)
    (out / "tests.log").write_text(log.getvalue(), encoding="utf-8")

    protected = {
        "requirements/scope-audit-lab-0.2.md": "50a1bf3d5b556cdb08c4367b5e442cdd512b7f2fbda9498383645b4c8e57a10d",
        "schemas/draft-0.1/evidence.schema.json": "db9d9902bd943e80cdccc660b22dbb12192732adc5bfcd5aecb0c4f801975775",
        "examples/schema-draft-0.1/records.json": "4d152cf48c629ff0e96857fe40716844669ef445f6f6d472fcac57c5192e9f90",
    }
    preserved = {
        name: {"expected": expected,
               "observed": hashlib.sha256((LAB / name).read_bytes()).hexdigest()}
        for name, expected in protected.items()
    }
    paths = [
        LAB / "integrity_checker.py", LAB / "tests/test_integrity_checker.py",
        Path(__file__), example,
        LAB / "schemas/draft-0.2/extensions.schema.json",
    ]
    checks = {
        "unit_tests_successful": result.wasSuccessful(),
        "parent_regressions_successful": all(r["exit_code"] == 0 for r in regressions),
        "example_cli_reports_gaps_with_exit_1": proc.returncode == 1 and report["summary"]["status"] == "INTEGRITY_GAPS_RECORDED",
        "example_sources_remain_unresolved": any(f["code"] == "REFERENCE_UNRESOLVED" for f in report["findings"]),
        "example_identity_coverage_complete_but_outcomes_unevaluated": (
            report["anchor_condition_coverage"][0]["identity_coverage"] == "COMPLETE"
            and any(f["code"] == "CONDITION_NOT_EVALUATED" for f in report["findings"])
            and not report["anchor_condition_coverage"][0]["condition_truth_established"]
        ),
        "protected_artifacts_unchanged": all(p["expected"] == p["observed"] for p in preserved.values()),
    }
    evidence = {
        "artifact_kind": "NARROW_INTEGRITY_CHECKER_VERIFICATION",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "checks": checks,
        "examined_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        "unit_tests": {
            "count": result.testsRun, "successful": result.wasSuccessful(),
            "events": result.events,
            "failures": [{"test": str(t), "traceback": s} for t, s in result.failures],
            "errors": [{"test": str(t), "traceback": s} for t, s in result.errors],
        },
        "parent_regressions": regressions,
        "example_cli": {"argv_without_interpreter": command[1:],
                        "exit_code": proc.returncode, "stderr": proc.stderr,
                        "report_summary": report["summary"]},
        "protected_artifacts": preserved,
        "artifact_sha256": {
            "example-report.json": hashlib.sha256(report_bytes).hexdigest(),
            "example-report.md": hashlib.sha256(markdown_bytes).hexdigest(),
            "tests.log": hashlib.sha256(log.getvalue().encode()).hexdigest(),
        },
        "limits": [
            "Synthetic tests and implementation share an author; no independent audit.",
            "These are narrow implementation tests, not the baseline acceptance matrix.",
            "No physics/empirical validity, source authenticity, prototype compatibility, or voice access was established.",
            "Runtime checker is read-only; this explicitly invoked authoring runner creates new review artifacts and runs fixed tests.",
        ],
    }
    (out / "verification.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "unit_test_count": result.testsRun,
                      "example_summary": report["summary"], "artifacts": str(out)}, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
