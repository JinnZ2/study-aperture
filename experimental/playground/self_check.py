"""Milestone-1 self-check: run the lab's own determinations through the lab.

Run with:  python -m playground.self_check

Exit code 0 means every planted defect was caught and correctly classified,
every design-contract guard held, and every control behaved as designed.
Anything else fails the build: the laboratory does not ship a diagnostic
infrastructure whose own determinations have not been tested.
"""

from __future__ import annotations

from .validation.diagnostic_metrics import format_summary, summarize
from .validation.planted_defects import (
    run_control_cases,
    verify_guards,
    verify_planted_defects,
)


def run_self_check() -> int:
    guards = verify_guards()
    checks = verify_planted_defects()
    controls = run_control_cases()
    summary = summarize(checks, guards, controls)
    print(format_summary(summary))
    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(run_self_check())
