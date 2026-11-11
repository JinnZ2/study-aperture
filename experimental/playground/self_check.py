"""Self-check: run the lab's own determinations through the lab.

Run with:  python -m playground.self_check

Runs the milestone-1 diagnostic suite (L0 gate, harnesses), the
milestone-2 system-track suite (return test, continuity matrix, track
transitions), and the milestone-3 determination-track suite (sensitivity,
qualified non-detection, scoped absence, UNKNOWN expiry), plus the milestone-4
applicability suite and diagnostic-gated equation substitution: planted
defects, design-contract guards, control cases, and adversarial scoped-mapping
and bypass tests, plus finite-bond and finite-branching oracles and planted
backend defects, plus cross-system-class diagnostic and evidence-transfer
contracts. Exit code 0
means every planted defect was caught and correctly classified, every
guard held, and every control behaved as designed. Anything else fails
the build: the laboratory does not ship a diagnostic infrastructure whose
own determinations have not been tested.
"""

from __future__ import annotations

import unittest

from .validation.diagnostic_metrics import format_summary, summarize
from .validation.determination_track_defects import (
    run_determination_track_controls,
    verify_determination_track_defects,
    verify_determination_track_guards,
)
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
from .validation import (
    test_applicability, test_branching, test_cross_system, test_percolation, test_substitution,
)


def run_self_check() -> int:
    guards = (
        verify_guards()
        + verify_system_track_guards()
        + verify_determination_track_guards()
    )
    checks = (
        verify_planted_defects()
        + verify_system_track_defects()
        + verify_determination_track_defects()
    )
    controls = (
        run_control_cases()
        + run_system_track_controls()
        + run_determination_track_controls()
    )
    summary = summarize(checks, guards, controls)
    print(format_summary(summary))
    print("\nAPPLICABILITY MAPPING: scoped and adversarial tests", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_applicability)
    mapping_result = unittest.TextTestRunner(verbosity=1).run(suite)
    print("\nEQUATION SUBSTITUTION: diagnostic bypass and numeric-contract tests", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_substitution)
    equation_result = unittest.TextTestRunner(verbosity=1).run(suite)
    print("\nFINITE BOND PERCOLATION: exact oracles and diagnostic guards", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_percolation)
    percolation_result = unittest.TextTestRunner(verbosity=1).run(suite)
    print("\nFINITE BRANCHING: exact census oracle and diagnostic guards", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_branching)
    branching_result = unittest.TextTestRunner(verbosity=1).run(suite)
    print("\nCROSS-SYSTEM CLASSES: orthogonal diagnostics and scoped transfer guards", flush=True)
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_cross_system)
    cross_system_result = unittest.TextTestRunner(verbosity=1).run(suite)
    passed = (summary.passed and mapping_result.wasSuccessful()
              and equation_result.wasSuccessful() and percolation_result.wasSuccessful()
              and branching_result.wasSuccessful() and cross_system_result.wasSuccessful())
    print("COMBINED SELF-CHECK PASSED" if passed else "COMBINED SELF-CHECK FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(run_self_check())
