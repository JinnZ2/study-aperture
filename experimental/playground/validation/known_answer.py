"""Known-answer harness: validate an instrument against systems with known answers.

Scope contract (this is the whole point of the harness):

- A known-answer pass certifies the INSTRUMENT within the tested case set
  only. It does not address the physical adequacy of any model, and the
  record it returns says so explicitly.
- An instrument error (crash, missing output) is an INSTRUMENT failure, not
  a physical one.
- A harness run with zero cases is INDETERMINATE, not a pass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from .numeric_contract import finite_outputs, pair_map, validate_case_data


class Instrument(Protocol):
    """Anything runnable on an input mapping that returns an output mapping."""

    instrument_id: str

    def run(self, inputs: Mapping[str, float]) -> Mapping[str, float]: ...


def _pairs(mapping: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted(mapping.items()))


@dataclass(frozen=True)
class KnownAnswerCase:
    case_id: str
    inputs: tuple[tuple[str, float], ...]
    expected: tuple[tuple[str, float], ...]
    tolerances: tuple[tuple[str, float], ...]
    description: str = ""

    @classmethod
    def from_maps(
        cls,
        case_id: str,
        inputs: Mapping[str, float],
        expected: Mapping[str, float],
        tolerances: Mapping[str, float],
        description: str = "",
    ) -> "KnownAnswerCase":
        return cls(
            case_id=case_id,
            inputs=_pairs(inputs),
            expected=_pairs(expected),
            tolerances=_pairs(tolerances),
            description=description,
        )

    @property
    def input_map(self) -> dict[str, float]:
        return pair_map(self.inputs)

    @property
    def expected_map(self) -> dict[str, float]:
        return pair_map(self.expected)

    @property
    def tolerance_map(self) -> dict[str, float]:
        return pair_map(self.tolerances)


@dataclass(frozen=True)
class InstrumentValidation:
    instrument_id: str
    record: FailureRecord
    cases_run: tuple[str, ...] = ()
    cases_failed: tuple[str, ...] = ()

    @property
    def validated_within_tested_cases(self) -> bool:
        """True only when at least one case ran and every case matched.

        This is not a physical validation of anything.
        """
        return bool(self.cases_run) and not self.cases_failed


def validate_known_answers(
    instrument: Instrument, cases: tuple[KnownAnswerCase, ...]
) -> InstrumentValidation:
    """Run the instrument on every known-answer case; classify mismatches on the instrument axis."""
    record = FailureRecord()
    failed: list[str] = []
    case_ids = tuple(c.case_id for c in cases)

    if not cases:
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.INDETERMINATE,
                code="KA_NO_CASES",
                message=(
                    "Known-answer harness ran with no cases; the instrument is "
                    "unvalidated, which is not the same as validated."
                ),
                source="validation.known_answer",
            )
        )
        return InstrumentValidation(instrument.instrument_id, record)

    # Preflight the entire case set before running the instrument. Invalid
    # experimental criteria are a determination failure, not instrument failure.
    try:
        if len(case_ids) != len(set(case_ids)) or any(not c.strip() for c in case_ids):
            raise ValueError("case IDs must be nonempty and unique")
        for case in cases:
            validate_case_data(case.inputs, case.expected, case.tolerances)
    except (ValueError, TypeError, AttributeError) as exc:
        record = record.with_finding(Finding(
            Axis.DETERMINATION, Status.FAILED, "KA_INVALID_CASES",
            f"Known-answer protocol is invalid: {exc}", "validation.known_answer",
        ))
        return InstrumentValidation(instrument.instrument_id, record)

    for case in cases:
        try:
            got = finite_outputs(instrument.run(case.input_map))
        except Exception as exc:  # an instrument that crashes fails as an instrument
            failed.append(case.case_id)
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="KA_INSTRUMENT_ERROR",
                    message=(
                        f"Instrument raised {type(exc).__name__} on case "
                        f"'{case.case_id}': {exc}"
                    ),
                    source="validation.known_answer",
                    evidence=(EvidenceRef("known-answer-case", case.case_id),),
                )
            )
            continue

        mismatches: list[str] = []
        for key, expected in case.expected_map.items():
            tol = case.tolerance_map[key]
            if key not in got:
                mismatches.append(f"{key}: no output produced")
                continue
            if abs(got[key] - expected) > tol:
                mismatches.append(
                    f"{key}: expected {expected:.6g}, got {got[key]:.6g} "
                    f"(tolerance {tol:.6g})"
                )

        if mismatches:
            failed.append(case.case_id)
            record = record.with_finding(
                Finding(
                    axis=Axis.INSTRUMENT,
                    severity=Status.FAILED,
                    code="KA_MISMATCH",
                    message=(
                        f"Known-answer mismatch on case '{case.case_id}': "
                        + "; ".join(mismatches)
                    ),
                    source="validation.known_answer",
                    evidence=(EvidenceRef("known-answer-case", case.case_id),),
                )
            )

    if not failed:
        record = record.with_finding(
            Finding(
                axis=Axis.INSTRUMENT,
                severity=Status.OK,
                code="KA_VALIDATED",
                message=(
                    f"Instrument matched {len(cases)} known-answer case(s) within "
                    f"declared tolerances. Validation scope is the tested case set "
                    f"only; this certifies the instrument, not the physical "
                    f"adequacy of any model."
                ),
                source="validation.known_answer",
                evidence=tuple(
                    EvidenceRef("known-answer-case", cid) for cid in case_ids
                ),
            )
        )

    return InstrumentValidation(
        instrument_id=instrument.instrument_id,
        record=record,
        cases_run=case_ids,
        cases_failed=tuple(failed),
    )
