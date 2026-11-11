"""Return-to-anchor test: system-track continuity.

Perturb the system, then test whether it returns to the frozen anchor
within declared tolerances. The test preserves the distinction between
system persistence and configuration persistence: the continuity matrix
(reference/continuity.py) classifies the two separately, and a system can
return to its anchor state while its configuration changed, and vice versa.

Classification contract (mirrors the L0 gate; classification follows the
provenance of the compared quantities):

- Non-return with an asserted return expectation and measured values
  -> INDETERMINATE on the physical and instrument axes: genuine system
     change and measurement error cannot be distinguished at this level.

- Non-return with an asserted return expectation and model-asserted
  (non-measured) values
  -> PHYSICAL failure: the description asserts a return its own values do
     not produce.

- Non-return with no return assertion
  -> no failure finding: an observed transition, recorded on the system
     track (lifecycle.state_transitions). The residual is data about the
     system, not a defect in it.

- Missing observation, missing tolerance, or tolerance naming a quantity
  absent from the anchor
  -> DETERMINATION INDETERMINATE: the record is incomplete and the loop
     cannot be closed.

- Complete record
  -> DETERMINATION OK: the loop closed on every declared quantity. This is
     a bookkeeping fact; it is not a physical validation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Mapping

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.l0_closure import ValueProvenance
from .anchor import AnchorState
from .continuity import SystemPersistence
from .misclosure import Misclosure, compute_misclosure


class ReturnOutcome(enum.Enum):
    RETURNED = "returned"
    NOT_RETURNED = "not_returned"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class QuantityReturn:
    quantity: str
    returned: float
    provenance: ValueProvenance


@dataclass(frozen=True)
class ReturnTestSpec:
    anchor: AnchorState
    returned: tuple[QuantityReturn, ...]
    tolerances: tuple[tuple[str, float], ...]
    expected_return: bool  # does the description assert the system returns?

    @classmethod
    def from_maps(
        cls,
        anchor: AnchorState,
        returned: Mapping[str, tuple[float, ValueProvenance]],
        tolerances: Mapping[str, float],
        expected_return: bool,
    ) -> "ReturnTestSpec":
        return cls(
            anchor=anchor,
            returned=tuple(
                QuantityReturn(quantity=q, returned=v, provenance=p)
                for q, (v, p) in sorted(returned.items())
            ),
            tolerances=tuple(sorted(tolerances.items())),
            expected_return=expected_return,
        )


@dataclass(frozen=True)
class ReturnTestResult:
    outcome: ReturnOutcome
    record: FailureRecord
    misclosures: tuple[Misclosure, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def system_persistence(self) -> SystemPersistence:
        if self.outcome is ReturnOutcome.RETURNED:
            return SystemPersistence.PERSISTED
        if self.outcome is ReturnOutcome.NOT_RETURNED:
            return SystemPersistence.CHANGED
        return SystemPersistence.INDETERMINATE

    @property
    def returned(self) -> bool:
        """Convenience only: the outcome, not a verdict about any model."""
        return self.outcome is ReturnOutcome.RETURNED


def return_test(spec: ReturnTestSpec) -> ReturnTestResult:
    """Run the return loop against the frozen anchor; classify by what is established."""
    record = FailureRecord()
    notes: list[str] = [
        f"anchor={spec.anchor.label}",
        f"expected_return={spec.expected_return}",
    ]
    anchor_map = spec.anchor.as_dict()
    tolerance_map = dict(spec.tolerances)
    returned_map = {r.quantity: r for r in spec.returned}

    # Completeness: the protocol is the tolerance set. Every tolerance must
    # name an anchor quantity and have an observation; every observation
    # must have a tolerance.
    missing: list[str] = []
    for quantity in tolerance_map:
        if quantity not in anchor_map:
            missing.append(
                f"{quantity}: tolerance names a quantity absent from the anchor"
            )
        elif quantity not in returned_map:
            missing.append(f"{quantity}: tolerance declared but never observed on return")
    for quantity in returned_map:
        if quantity not in tolerance_map:
            missing.append(f"{quantity}: observed without a declared tolerance")

    if missing:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="RT_RECORD_INCOMPLETE",
                message=(
                    "The return record is incomplete; the loop cannot be "
                    "closed: " + "; ".join(missing)
                ),
                source="reference.return_test",
                evidence=(EvidenceRef("anchor", spec.anchor.label),),
            )
        )
        notes.extend(missing)
        return ReturnTestResult(ReturnOutcome.INDETERMINATE, record, notes=tuple(notes))

    record = record.with_finding(
        Finding(
            axis=Axis.DETERMINATION,
            severity=Status.OK,
            code="RT_LOOP_CLOSED",
            message=(
                "The return record is complete; the loop closed on every "
                "declared quantity. This is a bookkeeping fact; it is not a "
                "physical validation."
            ),
            source="reference.return_test",
            evidence=tuple(
                EvidenceRef("return-observation", q) for q in sorted(tolerance_map)
            ),
        )
    )

    returned_values = {q: r.returned for q, r in returned_map.items()}
    misclosures = compute_misclosure(spec.anchor, returned_values, tolerance_map)
    for m in misclosures:
        notes.append(
            f"{m.quantity}: residual={m.residual:.6g} tolerance={m.tolerance:.6g}"
        )
    beyond = tuple(m for m in misclosures if not m.within_tolerance)

    if not beyond:
        return ReturnTestResult(ReturnOutcome.RETURNED, record, misclosures, tuple(notes))

    evidence = tuple(EvidenceRef("return-observation", m.quantity) for m in beyond)

    if not spec.expected_return:
        # No assertion means no violated assertion: the non-return is an
        # observed transition, recorded on the system track, not a failure.
        notes.append(
            "observed non-return (no return asserted): recorded as a "
            "system-track transition, not a failure"
        )
        return ReturnTestResult(ReturnOutcome.NOT_RETURNED, record, misclosures, tuple(notes))

    if any(
        returned_map[m.quantity].provenance is ValueProvenance.MEASURED
        for m in beyond
    ):
        record = record.with_finding(
            Finding(
                axis=Axis.PHYSICAL,
                severity=Status.INDETERMINATE,
                code="RT_RETURN_UNRESOLVED",
                message=(
                    "The system did not return to anchor within tolerance and "
                    "the return values are measured; genuine system change and "
                    "measurement error cannot be distinguished at this level."
                ),
                source="reference.return_test",
                evidence=evidence,
            )
        )
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.INDETERMINATE,
                code="RT_RETURN_UNRESOLVED",
                message=(
                    "The return misclosure may be measurement error; see the "
                    "paired physical-axis finding."
                ),
                source="reference.return_test",
                evidence=evidence,
            )
        )
    else:
        record = record.with_finding(
            Finding(
                axis=Axis.PHYSICAL,
                severity=Status.FAILED,
                code="RT_RETURN_VIOLATION",
                message=(
                    "The description asserts a return its own model-asserted "
                    "values do not produce; the asserted description fails "
                    "the return test."
                ),
                source="reference.return_test",
                evidence=evidence,
            )
        )

    return ReturnTestResult(ReturnOutcome.NOT_RETURNED, record, misclosures, tuple(notes))
