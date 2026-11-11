"""Instrument sensitivity determination.

The detection limit of an instrument, established per instrument and per
condition set. Sensitivity is not transferable between instruments or
regimes: a limit established under one set of conditions says nothing
about another. An established sensitivity is the prerequisite for
converting a non-detection into a scoped absence claim; without it, a
non-detection is only a non-detection.

Classification contract:

- An instrument that misses a magnitude the ladder expects detectable, or
  reports detections where none should be possible
  -> INSTRUMENT failure: the instrument does not meet the asserted
     sensitivity.

- No cases, or a ladder in which nothing is detected
  -> DETERMINATION INDETERMINATE: no detection limit is established,
     which is not the same as zero sensitivity.

- A consistent ladder
  -> INSTRUMENT OK, within the tested ladder and conditions only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status


class DetectingInstrument(Protocol):
    """Anything runnable on an input mapping that returns an output mapping."""

    instrument_id: str

    def run(self, inputs: Mapping[str, float]) -> Mapping[str, float]: ...


def _pairs(mapping: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted(mapping.items()))


@dataclass(frozen=True)
class SensitivityCase:
    """One rung of a sensitivity ladder: a known effect size, expected or not."""

    case_id: str
    effect_size: float
    expected_detectable: bool
    inputs: tuple[tuple[str, float], ...]
    null_outputs: tuple[tuple[str, float], ...]
    tolerances: tuple[tuple[str, float], ...]

    @classmethod
    def from_maps(
        cls,
        case_id: str,
        effect_size: float,
        expected_detectable: bool,
        inputs: Mapping[str, float],
        null_outputs: Mapping[str, float],
        tolerances: Mapping[str, float],
    ) -> "SensitivityCase":
        return cls(
            case_id=case_id,
            effect_size=effect_size,
            expected_detectable=expected_detectable,
            inputs=_pairs(inputs),
            null_outputs=_pairs(null_outputs),
            tolerances=_pairs(tolerances),
        )

    @property
    def input_map(self) -> dict[str, float]:
        return dict(self.inputs)

    @property
    def null_map(self) -> dict[str, float]:
        return dict(self.null_outputs)

    @property
    def tolerance_map(self) -> dict[str, float]:
        return dict(self.tolerances)


@dataclass(frozen=True)
class SensitivityDetermination:
    instrument_id: str
    detection_limit: float | None  # smallest detected effect size
    conditions: tuple[tuple[str, str], ...]  # scope under which established
    record: FailureRecord
    notes: tuple[str, ...] = ()

    @property
    def established(self) -> bool:
        """True only when a detection limit was established within the tested scope."""
        return self.detection_limit is not None

    def describes(self) -> str:
        limit = f"{self.detection_limit:g}" if self.detection_limit is not None else "none"
        return f"instrument={self.instrument_id} limit={limit} conditions={dict(self.conditions)}"


def _detects(case: SensitivityCase, got: Mapping[str, float]) -> bool:
    for key, null_value in case.null_map.items():
        if key not in got:
            continue
        if abs(got[key] - null_value) > case.tolerance_map[key]:
            return True
    return False


def establish_sensitivity(
    instrument: DetectingInstrument,
    cases: tuple[SensitivityCase, ...],
    conditions: Mapping[str, str],
) -> SensitivityDetermination:
    """Run the ladder; establish the detection limit or record why it cannot be established."""
    record = FailureRecord()
    notes: list[str] = []
    scope = tuple(sorted(conditions.items()))
    evidence = tuple(EvidenceRef("sensitivity-case", c.case_id) for c in cases)

    if not cases:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="SENSITIVITY_NO_CASES",
                message=(
                    "Sensitivity determination ran with no cases; no detection "
                    "limit is established, which is not the same as zero "
                    "sensitivity."
                ),
                source="detection.sensitivity",
            )
        )
        return SensitivityDetermination(
            instrument.instrument_id, None, scope, record, ("no cases",)
        )

    detected_sizes: list[float] = []
    for case in cases:
        try:
            got = dict(instrument.run(case.input_map))
        except Exception as exc:  # an instrument that crashes fails as an instrument
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="SENSITIVITY_INSTRUMENT_ERROR",
                    message=(
                        f"Instrument raised {type(exc).__name__} on case "
                        f"'{case.case_id}': {exc}"
                    ),
                    source="detection.sensitivity",
                    evidence=(EvidenceRef("sensitivity-case", case.case_id),),
                )
            )
            continue

        detected = _detects(case, got)
        if detected:
            detected_sizes.append(case.effect_size)
        notes.append(
            f"{case.case_id}: size={case.effect_size:g} detected={detected} "
            f"expected={case.expected_detectable}"
        )

        if detected and not case.expected_detectable:
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="SENSITIVITY_FALSE_POSITIVE",
                    message=(
                        f"Instrument reports a detection at effect size "
                        f"{case.effect_size:g}, which the ladder expects to be "
                        f"undetectable; the noise floor is at or above this "
                        f"magnitude."
                    ),
                    source="detection.sensitivity",
                    evidence=(EvidenceRef("sensitivity-case", case.case_id),),
                )
            )
        elif not detected and case.expected_detectable:
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="SENSITIVITY_MISS",
                    message=(
                        f"Instrument fails to detect an effect of size "
                        f"{case.effect_size:g} that the ladder expects "
                        f"detectable; the instrument does not meet the "
                        f"asserted sensitivity."
                    ),
                    source="detection.sensitivity",
                    evidence=(EvidenceRef("sensitivity-case", case.case_id),),
                )
            )

    if any(f.severity is Status.FAILED for f in record.findings):
        return SensitivityDetermination(
            instrument.instrument_id, None, scope, record, tuple(notes)
        )

    if not detected_sizes:
        record = record.with_finding(
            Finding(
                axis=Axis.DETERMINATION,
                severity=Status.INDETERMINATE,
                code="SENSITIVITY_LIMIT_NOT_ESTABLISHED",
                message=(
                    "No case in the ladder was detected; the tested magnitudes "
                    "bound nothing and no detection limit is established."
                ),
                source="detection.sensitivity",
                evidence=evidence,
            )
        )
        return SensitivityDetermination(
            instrument.instrument_id, None, scope, record, tuple(notes)
        )

    detection_limit = min(detected_sizes)
    record = record.with_finding(
        Finding(
            axis=Axis.INSTRUMENT,
            severity=Status.OK,
            code="SENSITIVITY_ESTABLISHED",
            message=(
                f"Detection limit {detection_limit:g} (smallest detected effect "
                f"size), established within the tested ladder and conditions. "
                f"Sensitivity is not transferable outside these conditions."
            ),
            source="detection.sensitivity",
            evidence=evidence,
        )
    )
    return SensitivityDetermination(
        instrument.instrument_id, detection_limit, scope, record, tuple(notes)
    )
