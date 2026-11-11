"""Typed failure records: three orthogonal failure axes, never collapsed.

The laboratory distinguishes three kinds of failure, and merging them is the
primary design error this module exists to prevent:

- PHYSICAL failure: the proposed model violates relevant physical constraints
  or fails to describe observations.
- INSTRUMENT failure: the measurement or diagnostic mechanism cannot reliably
  detect what it is intended to measure.
- DETERMINATION failure: the experimental choices, boundaries, controls, or
  provenance are insufficient to support the conclusion.

The axes are independent by construction. A model can be physically adequate
while the instrument is inadequate; an instrument can function correctly while
the experimental boundary is inappropriate. No code path in this package may
collapse the three axes into a single generic MODEL_FAILED result.

Statuses
--------
Each axis carries one of four statuses:

- OK            an explicit finding cleared this axis, within its recorded scope
- FAILED        a finding failed this axis
- INDETERMINATE the question was posed and could not be settled
- UNTESTED      no check addressed this axis

INDETERMINATE and UNTESTED are outcomes, not missing data. Non-detection is
not absence, and an expired UNKNOWN is not a negative result.

Forbidden promotions (enforced by structure and by guards in self_check):
- An instrument PASS must not silently validate a model.
- A clean determination must not silently certify an instrument.
- An integrity PASS must not silently change claim support.

Enforcement: FailureRecord refuses boolean coercion, and there is no method
that returns a single generic verdict. Query per axis.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterable, Mapping


class Axis(enum.Enum):
    PHYSICAL = "physical"
    INSTRUMENT = "instrument"
    DETERMINATION = "determination"


class Status(enum.Enum):
    UNTESTED = "untested"
    OK = "ok"
    INDETERMINATE = "indeterminate"
    FAILED = "failed"


_PRECEDENCE: Mapping[Status, int] = {
    Status.FAILED: 3,
    Status.INDETERMINATE: 2,
    Status.OK: 1,
    Status.UNTESTED: 0,
}


class CollapseError(TypeError):
    """Raised when the three failure axes would be collapsed into one verdict."""


@dataclass(frozen=True)
class EvidenceRef:
    """A pointer to the record that produced a finding (never that record's truth)."""

    kind: str  # e.g. "ledger-entry", "known-answer-case", "null-case"
    locator: str  # stable identifier inside that record
    digest: str | None = None  # optional content binding


@dataclass(frozen=True)
class Finding:
    """One typed observation attached to one failure axis."""

    axis: Axis
    severity: Status  # OK, INDETERMINATE, or FAILED; never UNTESTED
    code: str  # machine-readable, e.g. "L0_ACCOUNTING_GAP"
    message: str
    source: str  # emitting module, e.g. "gates.l0_closure"
    evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        if self.severity not in (Status.OK, Status.INDETERMINATE, Status.FAILED):
            raise ValueError(
                "Finding severity must be OK, INDETERMINATE, or FAILED; "
                "UNTESTED is not a finding, it is the absence of findings."
            )


@dataclass(frozen=True)
class FailureRecord:
    """The failure state of one determination.

    The three axis statuses are derived properties, not writable fields:
    they are computed from the findings, so the findings are the single
    source of truth and no code path can set an axis directly.
    """

    findings: tuple[Finding, ...] = ()

    def _axis_status(self, axis: Axis) -> Status:
        severities = [f.severity for f in self.findings if f.axis is axis]
        if not severities:
            return Status.UNTESTED
        return max(severities, key=lambda s: _PRECEDENCE[s])

    @property
    def physical(self) -> Status:
        return self._axis_status(Axis.PHYSICAL)

    @property
    def instrument(self) -> Status:
        return self._axis_status(Axis.INSTRUMENT)

    @property
    def determination(self) -> Status:
        return self._axis_status(Axis.DETERMINATION)

    def status_for(self, axis: Axis) -> Status:
        return self._axis_status(axis)

    def with_finding(self, finding: Finding) -> "FailureRecord":
        return FailureRecord(self.findings + (finding,))

    def with_findings(self, findings: Iterable[Finding]) -> "FailureRecord":
        record = self
        for finding in findings:
            record = record.with_finding(finding)
        return record

    def merge(self, other: "FailureRecord") -> "FailureRecord":
        """Union of two records; per-axis status follows finding precedence."""
        return self.with_findings(other.findings)

    @property
    def is_indeterminate(self) -> bool:
        return any(
            self._axis_status(axis) is Status.INDETERMINATE for axis in Axis
        )

    @property
    def conclusion_blocked(self) -> bool:
        """A FAILED instrument or determination axis blocks the conclusion.

        The physical axis is deliberately excluded: a physically failed model
        does not block the conclusion that the model failed.
        """
        return self.instrument is Status.FAILED or self.determination is Status.FAILED

    @property
    def inference_blocked(self) -> bool:
        """A FAILED instrument axis blocks inferences drawn from measurements."""
        return self.instrument is Status.FAILED

    @property
    def model_affected(self) -> bool:
        """Only the physical axis reflects on the model itself."""
        return self.physical is Status.FAILED

    def describe(self) -> str:
        return (
            f"physical={self.physical.value} "
            f"instrument={self.instrument.value} "
            f"determination={self.determination.value} "
            f"findings={len(self.findings)}"
        )

    def __bool__(self) -> bool:
        raise CollapseError(
            "FailureRecord refuses boolean coercion: physical, instrument, and "
            "determination failure are orthogonal axes with non-verdict states. "
            "Query status_for(Axis...) or the blocked/affected properties. A "
            "generic MODEL_FAILED verdict is exactly what this laboratory "
            "must not produce."
        )
