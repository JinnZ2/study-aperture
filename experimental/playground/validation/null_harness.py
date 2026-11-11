"""Null harness: the instrument must not detect what is not there.

A null case presents the instrument with a system in which the measured
effect is absent. A detection is an INSTRUMENT failure (false positive).
A clean null is recorded as such, and the record states the limit of what
that means: a clean null does not establish detection sensitivity.
Sensitivity and scoped absence are separate determinations
(detection.sensitivity).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .known_answer import Instrument, _pairs
from .numeric_contract import finite_outputs, pair_map, validate_case_data


@dataclass(frozen=True)
class NullCase:
    case_id: str
    inputs: tuple[tuple[str, float], ...]
    null_outputs: tuple[tuple[str, float], ...]
    tolerances: tuple[tuple[str, float], ...]
    description: str = ""

    @classmethod
    def from_maps(
        cls,
        case_id: str,
        inputs: Mapping[str, float],
        null_outputs: Mapping[str, float],
        tolerances: Mapping[str, float],
        description: str = "",
    ) -> "NullCase":
        return cls(
            case_id=case_id,
            inputs=_pairs(inputs),
            null_outputs=_pairs(null_outputs),
            tolerances=_pairs(tolerances),
            description=description,
        )

    @property
    def input_map(self) -> dict[str, float]:
        return pair_map(self.inputs)

    @property
    def null_map(self) -> dict[str, float]:
        return pair_map(self.null_outputs)

    @property
    def tolerance_map(self) -> dict[str, float]:
        return pair_map(self.tolerances)


@dataclass(frozen=True)
class NullValidation:
    instrument_id: str
    record: FailureRecord
    cases_run: tuple[str, ...] = ()
    cases_flagged: tuple[str, ...] = ()

    @property
    def clean_within_tested_cases(self) -> bool:
        """True only when at least one null case ran and none was flagged.

        This establishes no detection sensitivity.
        """
        return bool(self.cases_run) and not self.cases_flagged


def validate_nulls(
    instrument: Instrument, cases: tuple[NullCase, ...]
) -> NullValidation:
    """Run the instrument on every null case; flag detections as instrument failures."""
    record = FailureRecord()
    flagged: list[str] = []
    case_ids = tuple(c.case_id for c in cases)

    if not cases:
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.INDETERMINATE,
                code="NULL_NO_CASES",
                message=(
                    "Null harness ran with no cases; the instrument's false-positive "
                    "behavior is unknown, which is not the same as clean."
                ),
                source="validation.null_harness",
            )
        )
        return NullValidation(instrument.instrument_id, record)

    try:
        if len(case_ids) != len(set(case_ids)) or any(not c.strip() for c in case_ids):
            raise ValueError("case IDs must be nonempty and unique")
        for case in cases:
            validate_case_data(case.inputs, case.null_outputs, case.tolerances)
    except (ValueError, TypeError, AttributeError) as exc:
        record = record.with_finding(Finding(
            Axis.DETERMINATION, Status.FAILED, "NULL_INVALID_CASES",
            f"Null protocol is invalid: {exc}", "validation.null_harness",
        ))
        return NullValidation(instrument.instrument_id, record)

    for case in cases:
        try:
            got = finite_outputs(instrument.run(case.input_map))
        except Exception as exc:
            flagged.append(case.case_id)
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="NULL_INSTRUMENT_ERROR",
                    message=(
                        f"Instrument raised {type(exc).__name__} on null case "
                        f"'{case.case_id}': {exc}"
                    ),
                    source="validation.null_harness",
                    evidence=(EvidenceRef("null-case", case.case_id),),
                )
            )
            continue

        detections: list[str] = []
        for key, null_value in case.null_map.items():
            tol = case.tolerance_map[key]
            if key not in got:
                detections.append(f"{key}: no output produced")
                continue
            if abs(got[key] - null_value) > tol:
                detections.append(
                    f"{key}: null value {null_value:.6g}, got {got[key]:.6g} "
                    f"(tolerance {tol:.6g})"
                )

        if detections:
            flagged.append(case.case_id)
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="NULL_FALSE_POSITIVE",
                    message=(
                        f"False positive on null case '{case.case_id}': "
                        + "; ".join(detections)
                    ),
                    source="validation.null_harness",
                    evidence=(EvidenceRef("null-case", case.case_id),),
                )
            )

    if not flagged:
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.OK,
                code="NULL_CLEAN",
                message=(
                    f"Instrument produced no false positives on {len(cases)} null "
                    f"case(s). A clean null does not establish detection sensitivity; "
                    f"sensitivity and scoped absence are separate determinations."
                ),
                source="validation.null_harness",
                evidence=tuple(
                    EvidenceRef("null-case", cid) for cid in case_ids
                ),
            )
        )

    return NullValidation(
        instrument_id=instrument.instrument_id,
        record=record,
        cases_run=case_ids,
        cases_flagged=tuple(flagged),
    )
