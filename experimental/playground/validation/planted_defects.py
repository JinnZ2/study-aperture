"""Planted defects: the laboratory testing its own determinations.

Each planted defect is a deliberately broken artifact. The self-check runs
the milestone-1 machinery against every defect and requires two things:

1. the defect is caught (a finding is produced), and
2. it is classified into the CORRECT failure class.

If a planted instrument defect surfaces as a physical failure, or a ledger
gap surfaces as a conservation violation, the taxonomy is wrong — and the
self-check fails the build. The defects exist so that a disagreement
between the laboratory and its own design contract is detected here, in the
lab's infancy, rather than after the equation library exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ..failures import Axis, CollapseError, FailureRecord, Finding, Status
from ..gates.gate_results import GateOutcome
from ..gates.l0_closure import (
    BoundaryAccounting,
    Direction,
    Exchange,
    QuantityAccount,
    ValueProvenance,
    l0_closure_gate,
)
from ..provenance.claim_status import ClaimRecord, ClaimState, SupportState
from ..provenance.evidence_chain import EvidenceChain
from .known_answer import KnownAnswerCase, validate_known_answers
from .null_harness import NullCase, validate_nulls


class LinearInstrument:
    """y = slope * x + intercept. The simplest possible instrument under test."""

    def __init__(self, instrument_id: str, slope: float, intercept: float) -> None:
        self.instrument_id = instrument_id
        self.slope = slope
        self.intercept = intercept

    def run(self, inputs: dict[str, float]) -> dict[str, float]:
        return {"y": self.slope * inputs["x"] + self.intercept}


KNOWN_ANSWER_CASES: tuple[KnownAnswerCase, ...] = tuple(
    KnownAnswerCase.from_maps(
        f"ka-linear-{x}", {"x": float(x)}, {"y": float(x)}, {"y": 1e-9}
    )
    for x in (0, 1, 2)
)
NULL_CASES: tuple[NullCase, ...] = (
    NullCase.from_maps("null-zero-input", {"x": 0.0}, {"y": 0.0}, {"y": 1e-9}),
)


def balanced_energy_ledger() -> BoundaryAccounting:
    account = QuantityAccount(
        quantity="energy",
        initial=100.0,
        final=100.0,
        initial_provenance=ValueProvenance.SPECIFIED,
        final_provenance=ValueProvenance.MEASURED,
        exchanges=(
            Exchange(
                quantity="energy",
                direction=Direction.INFLOW,
                magnitude=10.0,
                label="heater-pulse",
                provenance=ValueProvenance.SPECIFIED,
                registered_by="control:heater",
            ),
            Exchange(
                quantity="energy",
                direction=Direction.OUTFLOW,
                magnitude=10.0,
                label="calorimeter-reading",
                provenance=ValueProvenance.MEASURED,
                registered_by="observer:calorimeter",
            ),
        ),
        tolerance=0.1,
    )
    return BoundaryAccounting(
        boundary_label="cell-A",
        accounts=(account,),
        declared_complete=True,
        registered_interventions=("control:heater", "observer:calorimeter"),
    )


def unregistered_control_ledger() -> BoundaryAccounting:
    ledger = balanced_energy_ledger()
    return BoundaryAccounting(
        boundary_label=ledger.boundary_label,
        accounts=ledger.accounts,
        declared_complete=ledger.declared_complete,
        registered_interventions=ledger.registered_interventions
        + ("control:stirrer",),
    )


def model_imbalance_ledger() -> BoundaryAccounting:
    account = QuantityAccount(
        quantity="energy",
        initial=100.0,
        final=101.0,
        initial_provenance=ValueProvenance.SPECIFIED,
        final_provenance=ValueProvenance.MODEL,
        exchanges=(
            Exchange(
                quantity="energy",
                direction=Direction.INFLOW,
                magnitude=10.0,
                label="heater-pulse",
                provenance=ValueProvenance.SPECIFIED,
                registered_by="control:heater",
            ),
            Exchange(
                quantity="energy",
                direction=Direction.OUTFLOW,
                magnitude=10.0,
                label="cooler-pulse",
                provenance=ValueProvenance.SPECIFIED,
                registered_by="control:cooler",
            ),
        ),
        tolerance=0.1,
    )
    return BoundaryAccounting(
        boundary_label="cell-B",
        accounts=(account,),
        declared_complete=True,
        registered_interventions=("control:heater", "control:cooler"),
    )


def measured_imbalance_ledger() -> BoundaryAccounting:
    account = QuantityAccount(
        quantity="energy",
        initial=100.0,
        final=100.0,
        initial_provenance=ValueProvenance.SPECIFIED,
        final_provenance=ValueProvenance.SPECIFIED,
        exchanges=(
            Exchange(
                quantity="energy",
                direction=Direction.INFLOW,
                magnitude=10.0,
                label="heater-pulse",
                provenance=ValueProvenance.SPECIFIED,
                registered_by="control:heater",
            ),
            Exchange(
                quantity="energy",
                direction=Direction.OUTFLOW,
                magnitude=8.0,
                label="calorimeter-reading",
                provenance=ValueProvenance.MEASURED,
                registered_by="observer:calorimeter",
            ),
        ),
        tolerance=0.1,
    )
    return BoundaryAccounting(
        boundary_label="cell-C",
        accounts=(account,),
        declared_complete=True,
        registered_interventions=("control:heater", "observer:calorimeter"),
    )


def incomplete_ledger_imbalance() -> BoundaryAccounting:
    ledger = model_imbalance_ledger()
    return BoundaryAccounting(
        boundary_label=ledger.boundary_label,
        accounts=ledger.accounts,
        declared_complete=False,
        registered_interventions=ledger.registered_interventions,
    )


@dataclass(frozen=True)
class PlantedDefect:
    defect_id: str
    description: str
    expected: tuple[tuple[Axis, Status], ...]
    exercise: Callable[[], FailureRecord]
    must_be_untested: tuple[Axis, ...] = ()


DEFECTS: tuple[PlantedDefect, ...] = (
    PlantedDefect(
        defect_id="unregistered-control",
        description=(
            "A control is declared in the experimental specification but never "
            "enters the boundary ledger."
        ),
        expected=((Axis.DETERMINATION, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: l0_closure_gate(unregistered_control_ledger()).record,
    ),
    PlantedDefect(
        defect_id="model-conservation-violation",
        description=(
            "A declared-complete ledger with no measured values does not balance."
        ),
        expected=((Axis.PHYSICAL, Status.FAILED), (Axis.DETERMINATION, Status.OK)),
        must_be_untested=(Axis.INSTRUMENT,),
        exercise=lambda: l0_closure_gate(model_imbalance_ledger()).record,
    ),
    PlantedDefect(
        defect_id="measured-imbalance-unresolved",
        description=(
            "A declared-complete ledger with measured values does not balance."
        ),
        expected=(
            (Axis.PHYSICAL, Status.INDETERMINATE),
            (Axis.INSTRUMENT, Status.INDETERMINATE),
            (Axis.DETERMINATION, Status.OK),
        ),
        exercise=lambda: l0_closure_gate(measured_imbalance_ledger()).record,
    ),
    PlantedDefect(
        defect_id="incomplete-ledger-gap",
        description="An unbalanced ledger that is not declared complete.",
        expected=((Axis.DETERMINATION, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: l0_closure_gate(incomplete_ledger_imbalance()).record,
    ),
    PlantedDefect(
        defect_id="known-answer-violation",
        description="An instrument that returns wrong values on known-answer cases.",
        expected=((Axis.INSTRUMENT, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: validate_known_answers(
            LinearInstrument("linear-defective", 1.0, 0.5), KNOWN_ANSWER_CASES
        ).record,
    ),
    PlantedDefect(
        defect_id="null-false-positive",
        description="An instrument that reports a detection on a null system.",
        expected=((Axis.INSTRUMENT, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: validate_nulls(
            LinearInstrument("linear-null-defective", 1.0, 0.5), NULL_CASES
        ).record,
    ),
)


@dataclass(frozen=True)
class DefectCheck:
    defect_id: str
    caught: bool
    correctly_classified: bool
    mismatches: tuple[str, ...]
    actual: FailureRecord


def verify_planted_defects() -> tuple[DefectCheck, ...]:
    checks: list[DefectCheck] = []
    for defect in DEFECTS:
        actual = defect.exercise()
        mismatches: list[str] = []
        for axis, status in defect.expected:
            got = actual.status_for(axis)
            if got is not status:
                mismatches.append(
                    f"expected {axis.value}={status.value}, got {got.value}"
                )
        for axis in defect.must_be_untested:
            got = actual.status_for(axis)
            if got is not Status.UNTESTED:
                mismatches.append(
                    f"expected {axis.value}=untested (no promotion), got {got.value}"
                )
        caught = len(actual.findings) > 0
        checks.append(
            DefectCheck(
                defect_id=defect.defect_id,
                caught=caught,
                correctly_classified=caught and not mismatches,
                mismatches=tuple(mismatches),
                actual=actual,
            )
        )
    return tuple(checks)


@dataclass(frozen=True)
class GuardCheck:
    guard_id: str
    description: str
    passed: bool
    detail: str = ""


def verify_guards() -> tuple[GuardCheck, ...]:
    """Design-contract guards: the forbidden promotions, tested directly."""
    checks: list[GuardCheck] = []

    # G1: the record refuses to become a single verdict.
    try:
        bool(FailureRecord())
        checks.append(
            GuardCheck(
                "collapse-refusal",
                "FailureRecord refuses boolean coercion.",
                False,
                "no error raised",
            )
        )
    except CollapseError:
        checks.append(
            GuardCheck("collapse-refusal", "FailureRecord refuses boolean coercion.", True)
        )

    # G2: UNTESTED is not a finding.
    try:
        Finding(
            axis=Axis.PHYSICAL,
            severity=Status.UNTESTED,
            code="X",
            message="",
            source="guard",
        )
        checks.append(
            GuardCheck(
                "untested-not-a-finding",
                "Findings cannot carry UNTESTED severity.",
                False,
                "no error raised",
            )
        )
    except ValueError:
        checks.append(
            GuardCheck(
                "untested-not-a-finding",
                "Findings cannot carry UNTESTED severity.",
                True,
            )
        )

    # G3: binding evidence changes no claim state or support.
    claim = ClaimRecord(
        claim_id="guard-claim",
        statement="guard statement",
        state=ClaimState.RECORDED,
    )
    chain = EvidenceChain().bind(
        "guard-claim", "guard report payload", produced_by="self-check"
    )
    unchanged = (
        claim.state is ClaimState.RECORDED
        and claim.support is SupportState.NONE
    )
    checks.append(
        GuardCheck(
            "binding-promotes-nothing",
            "Evidence binding leaves claim state and support unchanged.",
            unchanged,
            f"links={len(chain.links)}",
        )
    )

    # G4: a gate pass does not validate physics.
    result = l0_closure_gate(balanced_energy_ledger())
    ok = (
        result.outcome is GateOutcome.PASS
        and result.record.status_for(Axis.PHYSICAL) is Status.UNTESTED
    )
    checks.append(
        GuardCheck(
            "pass-is-not-physical-validation",
            "An L0 pass leaves the physical axis UNTESTED.",
            ok,
        )
    )

    return tuple(checks)


@dataclass(frozen=True)
class ControlCheck:
    control_id: str
    description: str
    passed: bool
    detail: str = ""


def run_control_cases() -> tuple[ControlCheck, ...]:
    """Non-defect controls: the machinery behaving as designed."""
    checks: list[ControlCheck] = []

    # C1: a balanced, complete ledger passes and validates nothing physical.
    result = l0_closure_gate(balanced_energy_ledger())
    ok = (
        result.outcome is GateOutcome.PASS
        and result.record.status_for(Axis.DETERMINATION) is Status.OK
        and result.record.status_for(Axis.PHYSICAL) is Status.UNTESTED
        and result.record.status_for(Axis.INSTRUMENT) is Status.UNTESTED
    )
    checks.append(
        ControlCheck(
            "balanced-ledger-passes",
            "A balanced ledger passes the gate without validating physics.",
            ok,
            result.record.describe(),
        )
    )

    # C2: a clean instrument is validated within its cases, with no physical promotion.
    clean = LinearInstrument("linear-clean", 1.0, 0.0)
    ka = validate_known_answers(clean, KNOWN_ANSWER_CASES)
    nu = validate_nulls(clean, NULL_CASES)
    ok = (
        ka.validated_within_tested_cases
        and nu.clean_within_tested_cases
        and ka.record.status_for(Axis.PHYSICAL) is Status.UNTESTED
        and nu.record.status_for(Axis.PHYSICAL) is Status.UNTESTED
    )
    checks.append(
        ControlCheck(
            "clean-instrument-validated",
            "A clean instrument validates on both harnesses with no physical promotion.",
            ok,
            ka.record.describe(),
        )
    )

    # C3: an empty harness is not a pass.
    empty = validate_known_answers(clean, ())
    ok = empty.record.status_for(Axis.INSTRUMENT) is Status.INDETERMINATE
    checks.append(
        ControlCheck(
            "empty-harness-is-not-a-pass",
            "A harness run with zero cases yields INDETERMINATE, not OK.",
            ok,
            empty.record.describe(),
        )
    )

    return tuple(checks)
