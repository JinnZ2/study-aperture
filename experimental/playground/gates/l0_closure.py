"""L0: the accounting-closure gate.

Position in the pipeline:

    experimental definition -> anchor freeze -> boundary specification
    -> control specification -> L0 closure gate
       pass -> known-answer and null harnesses
       fail or indeterminate -> BLOCKED / unresolved

L0 runs before any physics is evaluated. Its question is narrow: does the
boundary accounting close? Every quantity that crosses the selected boundary
must appear in the ledger, every registered intervention (control or observer)
that exchanges anything across the boundary must have an entry, and the books
must balance within a declared tolerance.

Classification contract
-----------------------
The gate cannot, by itself, decide whether an unbalanced ledger means the
description is physically inadequate or the measurement is wrong. It therefore
classifies by what is *established*, not by convenience:

- Missing registration, or a ledger not declared complete
  -> DETERMINATION failure. The experimental record is insufficient to
     support any conclusion; this says nothing about the model or instrument.

- Balance violated, declared-complete ledger, no measured values involved
  -> PHYSICAL failure. The asserted description violates accounting closure.
     This is the only outcome that reflects on the model.

- Balance violated, measured values involved
  -> INDETERMINATE on both the physical and instrument axes. Measurement
     error and description failure cannot be distinguished at this level;
     the laboratory records the ambiguity instead of resolving it by fiat.

- Balance achieved
  -> DETERMINATION status OK. Closing the books is a bookkeeping fact; it is
     explicitly NOT a physical validation of anything.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .gate_results import GateOutcome, GateResult
from .gate_registry import GateSpec, register


class Direction(enum.Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


class ValueProvenance(enum.Enum):
    SPECIFIED = "specified"  # fixed by the experimental specification (boundary, control)
    MODEL = "model"  # asserted by the description / equation family
    MEASURED = "measured"  # produced by an instrument


@dataclass(frozen=True)
class Exchange:
    """One crossing of the boundary, in one quantity kind."""

    quantity: str
    direction: Direction
    magnitude: float
    label: str
    provenance: ValueProvenance
    registered_by: str  # e.g. "control:heater-1", "observer:calorimeter"


@dataclass(frozen=True)
class QuantityAccount:
    quantity: str
    initial: float | None = None
    final: float | None = None
    initial_provenance: ValueProvenance = ValueProvenance.SPECIFIED
    final_provenance: ValueProvenance = ValueProvenance.SPECIFIED
    exchanges: tuple[Exchange, ...] = ()
    tolerance: float | None = None


@dataclass(frozen=True)
class BoundaryAccounting:
    """The ledger of everything declared to cross one selected boundary."""

    boundary_label: str
    accounts: tuple[QuantityAccount, ...] = ()
    declared_complete: bool = False
    registered_interventions: tuple[str, ...] = ()


def _entry_ref(boundary: str, account: QuantityAccount, label: str) -> EvidenceRef:
    return EvidenceRef("ledger-entry", f"{boundary}/{account.quantity}/{label}")


def _check_registration(accounting: BoundaryAccounting) -> tuple[FailureRecord, list[str]]:
    record = FailureRecord()
    notes: list[str] = []
    registered_sources = {
        e.registered_by for account in accounting.accounts for e in account.exchanges
    }

    if not accounting.registered_interventions:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="L0_INTERVENTION_REGISTRY_EMPTY",
                message=(
                    "No interventions (controls or observers) are registered for this "
                    "boundary; the laboratory cannot verify that all boundary crossings "
                    "were declared."
                ),
                source="gates.l0_closure",
                evidence=(EvidenceRef("boundary", accounting.boundary_label),),
            )
        )
        notes.append("intervention registry empty")
        return record, notes

    missing = [
        i for i in accounting.registered_interventions if i not in registered_sources
    ]
    if missing:
        for intervention in missing:
            record = record.with_finding(
                Finding(
                    axis=Axis.DETERMINATION,
                    severity=Status.FAILED,
                    code="L0_UNREGISTERED_INTERVENTION",
                    message=(
                        f"Intervention '{intervention}' is registered in the experimental "
                        f"specification but has no entry in the boundary ledger."
                    ),
                    source="gates.l0_closure",
                    evidence=(
                        EvidenceRef("boundary", accounting.boundary_label),
                        EvidenceRef("intervention", intervention),
                    ),
                )
            )
            notes.append(f"unregistered intervention: {intervention}")
    else:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.OK,
                code="L0_REGISTRATION_COMPLETE",
                message=(
                    f"All {len(accounting.registered_interventions)} registered "
                    f"intervention(s) appear in the boundary ledger."
                ),
                source="gates.l0_closure",
                evidence=tuple(
                    EvidenceRef("intervention", i)
                    for i in accounting.registered_interventions
                ),
            )
        )
    return record, notes


def _check_quantity(
    accounting: BoundaryAccounting, account: QuantityAccount
) -> tuple[FailureRecord, list[str]]:
    record = FailureRecord()
    notes: list[str] = []
    refs = tuple(
        _entry_ref(accounting.boundary_label, account, e.label)
        for e in account.exchanges
    ) + (
        _entry_ref(accounting.boundary_label, account, "initial"),
        _entry_ref(accounting.boundary_label, account, "final"),
    )

    inflow = sum(
        e.magnitude for e in account.exchanges if e.direction is Direction.INFLOW
    )
    outflow = sum(
        e.magnitude for e in account.exchanges if e.direction is Direction.OUTFLOW
    )

    if account.initial is None or account.final is None:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="L0_ENDPOINT_MISSING",
                message=(
                    f"Quantity '{account.quantity}' is missing an initial or final "
                    f"state; the books cannot be closed."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        notes.append(f"{account.quantity}: endpoint missing")
        return record, notes

    if account.tolerance is None:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="L0_TOLERANCE_UNDEFINED",
                message=(
                    f"Quantity '{account.quantity}' has no declared accounting "
                    f"tolerance; a misclosure cannot be judged."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        notes.append(f"{account.quantity}: tolerance undefined")
        return record, notes

    misclosure = (account.initial + inflow - outflow) - account.final
    notes.append(
        f"{account.quantity}: misclosure={misclosure:.6g} "
        f"tolerance={account.tolerance:.6g}"
    )

    if abs(misclosure) <= account.tolerance:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.OK,
                code="L0_BALANCED",
                message=(
                    f"Quantity '{account.quantity}' balances within tolerance. Closing "
                    f"the books is a bookkeeping fact; it is not a physical validation."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        return record, notes

    if not accounting.declared_complete:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.FAILED,
                code="L0_ACCOUNTING_GAP",
                message=(
                    f"Quantity '{account.quantity}' does not balance and the ledger is "
                    f"not declared complete. A physical violation cannot be distinguished "
                    f"from a bookkeeping gap; the determination is insufficient, and "
                    f"nothing is asserted about the model."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        return record, notes

    involved = [e.provenance for e in account.exchanges] + [
        account.initial_provenance,
        account.final_provenance,
    ]
    if any(p is ValueProvenance.MEASURED for p in involved):
        record = record.with_finding(
            Finding(
                axis=Axis.PHYSICAL,
                severity=Status.INDETERMINATE,
                code="L0_BALANCE_UNRESOLVED",
                message=(
                    f"Quantity '{account.quantity}' does not balance and measured values "
                    f"are involved. Measurement error and description failure cannot be "
                    f"distinguished at this level; both the physical and instrument axes "
                    f"are recorded as indeterminate."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.INDETERMINATE,
                code="L0_BALANCE_UNRESOLVED",
                message=(
                    f"Quantity '{account.quantity}' misclosure may be measurement error; "
                    f"see the paired physical-axis finding."
                ),
                source="gates.l0_closure",
                evidence=refs,
            )
        )
        return record, notes

    record = record.with_finding(
        Finding(
            axis=Axis.PHYSICAL,
            severity=Status.FAILED,
            code="L0_CONSERVATION_VIOLATION",
            message=(
                f"Quantity '{account.quantity}' does not balance under a "
                f"declared-complete ledger with no measured values; the asserted "
                f"description violates accounting closure."
            ),
            source="gates.l0_closure",
            evidence=refs,
        )
    )
    return record, notes


def l0_closure_gate(accounting: BoundaryAccounting) -> GateResult:
    """Evaluate whether the boundary accounting closes. Emits typed findings only."""
    record = FailureRecord()
    notes: list[str] = [
        f"boundary={accounting.boundary_label}",
        f"declared_complete={accounting.declared_complete}",
    ]

    reg_record, reg_notes = _check_registration(accounting)
    record = record.merge(reg_record)
    notes.extend(reg_notes)

    for account in accounting.accounts:
        acct_record, acct_notes = _check_quantity(accounting, account)
        record = record.merge(acct_record)
        notes.extend(acct_notes)

    if any(f.severity is Status.FAILED for f in record.findings):
        outcome = GateOutcome.FAIL
    elif any(f.severity is Status.INDETERMINATE for f in record.findings):
        outcome = GateOutcome.INDETERMINATE
    else:
        outcome = GateOutcome.PASS

    return GateResult(
        gate_id="l0_closure", outcome=outcome, record=record, notes=tuple(notes)
    )


register(
    GateSpec(
        gate_id="l0_closure",
        stage="l0_closure",
        question="Does the boundary accounting close before any physics is evaluated?",
        can_emit=(Axis.PHYSICAL, Axis.INSTRUMENT, Axis.DETERMINATION),
        module="playground.gates.l0_closure",
    )
)
