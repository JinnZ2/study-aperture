"""Non-detection records.

A non-detection is recorded as a non-detection: a null result within tested
conditions is not absence. The record preserves what was tested, under which
conditions, and what would have been required to detect the effect (the
established sensitivity). Converting a non-detection into an absence claim
requires an established sensitivity that covers the effect size in
question; that conversion lives in scoped_absence.

Qualification contract:

- No established sensitivity
  -> DETERMINATION INDETERMINATE: a non-detection without sensitivity is
     not evidence of absence; it is only a non-detection.

- No effect size of interest
  -> DETERMINATION INDETERMINATE: the non-detection cannot be qualified
     against any absence claim.

- Established limit exceeds the effect size of interest
  -> DETERMINATION INDETERMINATE: the instrument could not have detected an
     effect that small, so the non-detection establishes nothing about it.

- Established limit at or below the effect size of interest
  -> DETERMINATION OK: within its conditions, the instrument would have
     detected an effect of the size in question; the non-detection is
     qualified for a scoped absence claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .sensitivity import SensitivityDetermination


@dataclass(frozen=True)
class NonDetectionObservation:
    observation_id: str
    effect_size_of_interest: float | None = None  # magnitude the absence claim concerns
    conditions: tuple[tuple[str, str], ...] = ()
    notes: tuple[str, ...] = ()

    @classmethod
    def from_map(
        cls,
        observation_id: str,
        conditions: Mapping[str, str],
        effect_size_of_interest: float | None = None,
        notes: tuple[str, ...] = (),
    ) -> "NonDetectionObservation":
        return cls(
            observation_id=observation_id,
            effect_size_of_interest=effect_size_of_interest,
            conditions=tuple(sorted(conditions.items())),
            notes=notes,
        )


@dataclass(frozen=True)
class NonDetectionRecord:
    observation: NonDetectionObservation
    sensitivity: SensitivityDetermination | None
    qualified: bool
    record: FailureRecord
    notes: tuple[str, ...] = ()

    @property
    def detection_limit(self) -> float | None:
        if self.sensitivity is None:
            return None
        return self.sensitivity.detection_limit


def record_non_detection(
    observation: NonDetectionObservation,
    sensitivity: SensitivityDetermination | None,
) -> NonDetectionRecord:
    """Record a non-detection and qualify it against the established sensitivity."""
    record = FailureRecord()
    notes: list[str] = [f"observation={observation.observation_id}"]
    evidence = (EvidenceRef("non-detection", observation.observation_id),)

    if sensitivity is not None:
        record = record.merge(sensitivity.record)
        notes.append(f"sensitivity: {sensitivity.describes()}")

    if sensitivity is None or not sensitivity.established:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="ND_UNQUALIFIED",
                message=(
                    "A non-detection without an established sensitivity is not "
                    "evidence of absence; it is only a non-detection."
                ),
                source="detection.non_detection",
                evidence=evidence,
            )
        )
        return NonDetectionRecord(observation, sensitivity, False, record, tuple(notes))

    assert sensitivity.detection_limit is not None  # established implies a limit

    if observation.effect_size_of_interest is None:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="ND_NO_EFFECT_SIZE",
                message=(
                    "No effect size of interest is specified; the non-detection "
                    "cannot be qualified against any absence claim."
                ),
                source="detection.non_detection",
                evidence=evidence,
            )
        )
        return NonDetectionRecord(observation, sensitivity, False, record, tuple(notes))

    effect_size = observation.effect_size_of_interest
    if sensitivity.detection_limit > effect_size:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="ND_BELOW_SENSITIVITY",
                message=(
                    f"The established detection limit ({sensitivity.detection_limit:g}) "
                    f"exceeds the effect size of interest ({effect_size:g}); the "
                    f"instrument could not have detected an effect that small, so "
                    f"the non-detection establishes nothing about it."
                ),
                source="detection.non_detection",
                evidence=evidence,
            )
        )
        return NonDetectionRecord(observation, sensitivity, False, record, tuple(notes))

    record = record.with_finding(
        Finding(
            axis=Axis.DETERMINATION,
            severity=Status.OK,
            code="ND_QUALIFIED",
            message=(
                f"Within its conditions, the instrument would have detected an "
                f"effect of the size in question ({effect_size:g} at or above the "
                f"limit {sensitivity.detection_limit:g}); the non-detection is "
                f"qualified for a scoped absence claim."
            ),
            source="detection.non_detection",
            evidence=evidence,
        )
    )
    return NonDetectionRecord(observation, sensitivity, True, record, tuple(notes))
