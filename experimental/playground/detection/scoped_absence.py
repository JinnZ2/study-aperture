"""Scoped absence claims.

An absence claim carries its scope: valid only within the tested boundary,
controls, and observer regime, and only up to the instrument's established
sensitivity. The claim states what is absent, at what magnitude threshold,
within which conditions, and up to which detection limit. It is never a
universal absence: outside the recorded scope, the claim says nothing.

Scope contract: the sensitivity must have been established under conditions
that cover the observation. Sensitivity is not transferable between
conditions; a mismatch or an undeclared condition yields an INDETERMINATE
determination, never a qualified claim.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .non_detection import NonDetectionRecord


@dataclass(frozen=True)
class AbsenceClaim:
    claim_id: str
    statement: str
    effect_size_floor: float  # effects at or above this size are claimed absent
    detection_limit: float
    scope: tuple[tuple[str, str], ...]  # conditions within which the claim holds
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AbsenceRejection:
    record: FailureRecord
    reason: str
    notes: tuple[str, ...] = ()


def claim_absence(
    claim_id: str, non_detection: NonDetectionRecord
) -> AbsenceClaim | AbsenceRejection:
    """Convert a qualified non-detection into a scoped absence claim, or reject it."""
    if not non_detection.qualified:
        return AbsenceRejection(
            non_detection.record,
            "the non-detection is not qualified; see its findings",
            non_detection.notes,
        )

    assert non_detection.sensitivity is not None  # qualified implies established
    assert non_detection.sensitivity.detection_limit is not None
    assert non_detection.observation.effect_size_of_interest is not None

    record = non_detection.record
    observation_conditions = dict(non_detection.observation.conditions)
    sensitivity_conditions = dict(non_detection.sensitivity.conditions)
    evidence = (
        EvidenceRef("non-detection", non_detection.observation.observation_id),
    )

    problems: list[str] = []
    for key, value in observation_conditions.items():
        if key not in sensitivity_conditions:
            problems.append(
                f"{key}={value}: the observation has a condition the sensitivity "
                f"scope does not cover"
            )
        elif sensitivity_conditions[key] != value:
            problems.append(
                f"{key}: observed as {value!r}, sensitivity established under "
                f"{sensitivity_conditions[key]!r}"
            )
    for key in sensitivity_conditions:
        if key not in observation_conditions:
            problems.append(
                f"{key}: the sensitivity scope depends on a condition the "
                f"observation does not declare"
            )

    if problems:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="SA_SCOPE_MISMATCH",
                message=(
                    "The sensitivity was established under conditions that do "
                    "not cover this observation; sensitivity is not "
                    "transferable between conditions: " + "; ".join(problems)
                ),
                source="detection.scoped_absence",
                evidence=evidence,
            )
        )
        return AbsenceRejection(
            record,
            "scope mismatch: the sensitivity does not cover the observation's conditions",
            tuple(problems),
        )

    effect_size = non_detection.observation.effect_size_of_interest
    detection_limit = non_detection.sensitivity.detection_limit
    claim = AbsenceClaim(
        claim_id=claim_id,
        statement=(
            f"Within {dict(observation_conditions)}, no effect of size at or "
            f"above {effect_size:g} is present, up to the instrument's "
            f"established detection limit {detection_limit:g}."
        ),
        effect_size_floor=effect_size,
        detection_limit=detection_limit,
        scope=non_detection.observation.conditions,
        notes=(
            "The claim holds only within the recorded scope and only above the "
            "recorded floor; outside either, it says nothing.",
        ),
    )
    return claim
