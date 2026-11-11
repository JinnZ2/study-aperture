"""Self-check: run the lab's own determinations through the lab.

Run with:  python -m playground.self_check

Runs the milestone-1 diagnostic suite (L0 gate, harnesses) and the
milestone-2 system-track suite (return test, continuity matrix, track
transitions) together: planted defects, design-contract guards, and
control cases. Exit code 0 means every planted defect was caught and
correctly classified, every guard held, and every control behaved as
designed. Anything else fails the build: the laboratory does not ship a
diagnostic infrastructure whose own determinations have not been tested.
"""

from __future__ import annotations

from .validation.diagnostic_metrics import format_summary, summarize
from .validation.planted_defects import (
    run_control_cases,
    verify_guards,
    verify_planted_defects,
)
from .validation.system_track_defects import (
    run_system_track_controls,
    verify_system_track_defects,
    verify_system_track_guards,
)


def run_self_check() -> int:
    guards = verify_guards() + verify_system_track_guards()
    checks = verify_planted_defects() + verify_system_track_defects()
    controls = run_control_cases() + run_system_track_controls()
    summary = summarize(checks, guards, controls)
    print(format_summary(summary))
    return 0 if summary.passed else 1


if __name__ == "__main__":
    raise SystemExit(run_self_check())
