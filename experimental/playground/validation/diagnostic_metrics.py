"""Honest summaries of self-check results.

The summary deliberately reports per-defect misclassifications rather than a
single accuracy figure: one number would hide exactly the confusion between
failure classes that this laboratory exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass

from .planted_defects import ControlCheck, DefectCheck, GuardCheck


@dataclass(frozen=True)
class SelfCheckSummary:
    defects_planted: int
    defects_caught: int
    defects_correctly_classified: int
    misclassifications: tuple[str, ...]  # per-defect mismatch strings
    defects_not_caught: tuple[str, ...]
    guards_run: int
    guards_passed: int
    guard_failures: tuple[tuple[str, str], ...]
    controls_run: int
    controls_passed: int
    control_failures: tuple[tuple[str, str], ...]

    @property
    def passed(self) -> bool:
        return (
            self.defects_caught == self.defects_planted
            and self.defects_correctly_classified == self.defects_planted
            and self.guards_passed == self.guards_run
            and self.controls_passed == self.controls_run
        )


def summarize(
    checks: tuple[DefectCheck, ...],
    guards: tuple[GuardCheck, ...],
    controls: tuple[ControlCheck, ...],
) -> SelfCheckSummary:
    return SelfCheckSummary(
        defects_planted=len(checks),
        defects_caught=sum(1 for c in checks if c.caught),
        defects_correctly_classified=sum(1 for c in checks if c.correctly_classified),
        misclassifications=tuple(
            f"{c.defect_id}: " + "; ".join(c.mismatches)
            for c in checks
            if c.mismatches
        ),
        defects_not_caught=tuple(c.defect_id for c in checks if not c.caught),
        guards_run=len(guards),
        guards_passed=sum(1 for g in guards if g.passed),
        guard_failures=tuple(
            (g.guard_id, g.detail or g.description) for g in guards if not g.passed
        ),
        controls_run=len(controls),
        controls_passed=sum(1 for c in controls if c.passed),
        control_failures=tuple(
            (c.control_id, c.detail or c.description)
            for c in controls
            if not c.passed
        ),
    )


def format_summary(summary: SelfCheckSummary) -> str:
    lines = [
        "PLAYGROUND SELF-CHECK (diagnostic infrastructure + system track)",
        "",
        f"guards:   {summary.guards_passed}/{summary.guards_run} passed",
        f"defects:  {summary.defects_caught}/{summary.defects_planted} caught, "
        f"{summary.defects_correctly_classified}/{summary.defects_planted} "
        f"correctly classified",
        f"controls: {summary.controls_passed}/{summary.controls_run} passed",
        "",
    ]
    if summary.defects_not_caught:
        lines.append("defects not caught:")
        lines.extend(f"  - {d}" for d in summary.defects_not_caught)
    if summary.misclassifications:
        lines.append("misclassified defects:")
        lines.extend(f"  - {m}" for m in summary.misclassifications)
    if summary.guard_failures:
        lines.append("guard failures:")
        lines.extend(f"  - {gid}: {detail}" for gid, detail in summary.guard_failures)
    if summary.control_failures:
        lines.append("control failures:")
        lines.extend(f"  - {cid}: {detail}" for cid, detail in summary.control_failures)
    if summary.passed:
        lines.append("SELF-CHECK PASSED")
    else:
        lines.append("SELF-CHECK FAILED")
    return "\n".join(lines)
