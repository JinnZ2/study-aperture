"""Reevaluation on revision edges.

A revision dependency (new evidence, an expired UNKNOWN, a changed condition)
triggers reevaluation of the affected determination. Reevaluation reopens
the determination; it does not overturn it by default. The original
determination is preserved — superseded, not overwritten — and the successor
is issued alongside it, never in its place.

A determination that rests on an expired or superseded UNKNOWN without
itself being revisited is stale: its provenance no longer supports the
conclusion (a DETERMINATION failure). Relying on an open UNKNOWN is allowed
and is not a failure; the unknown is preserved, not converted into a
verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .state_transitions import StateTransition, determination_transition
from .unknown_expiry import UnknownDetermination, UnknownState


@dataclass(frozen=True)
class ReevaluationResult:
    original: UnknownDetermination  # preserved, now REEVALUATED
    successor: UnknownDetermination  # issued alongside, never in place
    transition: StateTransition
    notes: tuple[str, ...] = ()


def reevaluate(
    unknown: UnknownDetermination,
    successor_id: str,
    new_statement: str,
    reason: str,
    scope_conditions: Mapping[str, str] | None = None,
    expiry_triggers: tuple = (),
    evidence: tuple[EvidenceRef, ...] = (),
) -> ReevaluationResult:
    """Reopen a determination; issue a successor; preserve the original.

    The original is marked REEVALUATED and left otherwise unchanged; the
    successor starts as a fresh open UNKNOWN. Reevaluation does not overturn
    the original by default — the successor must stand on its own evidence.
    """
    if successor_id == unknown.determination_id:
        raise ValueError(
            "The successor determination must have its own identifier; "
            "reevaluation issues a new determination, it does not overwrite "
            "the original."
        )
    original = replace(unknown, state=UnknownState.REEVALUATED)
    successor = UnknownDetermination(
        determination_id=successor_id,
        statement=new_statement,
        state=UnknownState.UNKNOWN,
        scope_conditions=tuple(sorted((scope_conditions or {}).items())),
        expiry_triggers=expiry_triggers,
        evidence=evidence,
    )
    transition = determination_transition(
        unknown.state.value,
        "reevaluated",
        reason,
        evidence=evidence,
    )
    return ReevaluationResult(
        original,
        successor,
        transition,
        (
            f"reason: {reason}",
            "original preserved as REEVALUATED; successor issued alongside it, "
            "not in its place",
        ),
    )


def stale_reliance(cited: Mapping[str, UnknownState]) -> FailureRecord:
    """Check a determination's reliance on UNKNOWN determinations.

    Relying on an open UNKNOWN is allowed and recorded without a finding.
    Relying on an EXPIRED or REEVALUATED one without revisiting the
    dependent determination is a DETERMINATION failure: the provenance no
    longer supports the conclusion.
    """
    record = FailureRecord()
    for determination_id, state in sorted(cited.items()):
        if state in (UnknownState.EXPIRED, UnknownState.REEVALUATED):
            record = record.with_finding(
                Finding(
                    axis=Axis.DETERMINATION,
                    severity=Status.FAILED,
                    code="STALE_UNKNOWN_RELIANCE",
                    message=(
                        f"Determination relies on '{determination_id}', which is "
                        f"{state.value}; the dependent determination must be "
                        f"revisited before its conclusion stands."
                    ),
                    source="lifecycle.reevaluation",
                    evidence=(
                        EvidenceRef("unknown-determination", determination_id),
                    ),
                )
            )
    return record
