"""Determination-track planted defects: sensitivity-qualified absence and UNKNOWN expiry.

Milestone 3 of the laboratory testing its own determinations. The suite
plugs deliberately broken sensitivity ladders, unqualified non-detections,
scope-mismatched observations, and stale reliance on expired UNKNOWNs into
the detection and lifecycle machinery, and requires that every defect is
caught and classified into the correct failure class.

The load-bearing assertions:

- An instrument that misses the ladder or reports detections where none
  are possible is an INSTRUMENT failure.
- A non-detection without an established sensitivity, without an effect
  size of interest, or below the detection limit is not evidence of
  absence (DETERMINATION indeterminate).
- Sensitivity is not transferable between conditions: a scope mismatch
  yields an indeterminate determination, never a qualified claim.
- Expiry is a revision trigger, not a refutation: an expired UNKNOWN
  produces a determination-track transition and no failure findings.
- A determination resting on an expired or superseded UNKNOWN is stale
  (DETERMINATION failure); resting on an open UNKNOWN is not.
"""

from __future__ import annotations

from ..detection.non_detection import (
    NonDetectionObservation,
    record_non_detection,
)
from ..detection.scoped_absence import AbsenceClaim, claim_absence
from ..detection.sensitivity import (
    SensitivityCase,
    SensitivityDetermination,
    establish_sensitivity,
)
from ..failures import Axis, Status
from ..lifecycle.reevaluation import reevaluate, stale_reliance
from ..lifecycle.state_transitions import Track
from ..lifecycle.unknown_expiry import (
    ExpiryTrigger,
    ExpiryTriggerKind,
    UnknownDetermination,
    UnknownState,
    check_expiry,
)
from .planted_defects import (
    ControlCheck,
    PlantedDefect,
    GuardCheck,
    verify_defects,
)


class _ThresholdInstrument:
    """y = x when x is at or above threshold, else 0.0; plus a constant noise offset.

    Models an instrument with a genuine detection threshold: magnitudes
    below the threshold produce no output, at or above it produce the full
    signal.
    """

    def __init__(
        self, instrument_id: str, threshold: float = 0.0, offset: float = 0.0
    ) -> None:
        self.instrument_id = instrument_id
        self.threshold = threshold
        self.offset = offset

    def run(self, inputs: dict[str, float]) -> dict[str, float]:
        x = inputs["x"]
        signal = x if x >= self.threshold else 0.0
        return {"y": signal + self.offset}


def full_ladder() -> tuple[SensitivityCase, ...]:
    return tuple(
        SensitivityCase.from_maps(
            f"ladder-{size:g}",
            size,
            expected,
            {"x": size},
            {"y": 0.0},
            {"y": 1e-9},
        )
        for size, expected in (
            (0.01, False),
            (0.05, False),
            (0.1, True),
            (0.5, True),
            (1.0, True),
        )
    )


def sub_limit_ladder() -> tuple[SensitivityCase, ...]:
    return tuple(
        SensitivityCase.from_maps(
            f"ladder-{size:g}", size, False, {"x": size}, {"y": 0.0}, {"y": 1e-9}
        )
        for size in (0.01, 0.05)
    )


LADDER_CONDITIONS = {"regime": "passive", "band": "K"}


def established_sensitivity() -> SensitivityDetermination:
    return establish_sensitivity(
        _ThresholdInstrument("ladder-clean", 0.1, 0.0),
        full_ladder(),
        LADDER_CONDITIONS,
    )


def _claim_record(
    claim_id: str, observation: NonDetectionObservation
) -> tuple:
    """Run the full qualification path; return (record, claim-or-rejection)."""
    nd = record_non_detection(observation, established_sensitivity())
    outcome = claim_absence(claim_id, nd)
    if isinstance(outcome, AbsenceClaim):
        return nd.record, outcome
    return outcome.record, outcome


DETERMINATION_TRACK_DEFECTS: tuple[PlantedDefect, ...] = (
    PlantedDefect(
        defect_id="blind-instrument-misses-ladder",
        description="An instrument that detects nothing on a ladder with expected detections.",
        expected=((Axis.INSTRUMENT, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: establish_sensitivity(
            _ThresholdInstrument("ladder-blind", float("inf"), 0.0),
            full_ladder(),
            LADDER_CONDITIONS,
        ).record,
    ),
    PlantedDefect(
        defect_id="noisy-instrument-false-positives",
        description="An instrument that reports detections where none should be possible.",
        expected=((Axis.INSTRUMENT, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: establish_sensitivity(
            _ThresholdInstrument("ladder-noisy", float("inf"), 0.1),
            full_ladder(),
            LADDER_CONDITIONS,
        ).record,
    ),
    PlantedDefect(
        defect_id="sensitivity-ladder-empty",
        description="A sensitivity determination with no cases.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: establish_sensitivity(
            _ThresholdInstrument("ladder-clean", 0.1, 0.0),
            (),
            LADDER_CONDITIONS,
        ).record,
    ),
    PlantedDefect(
        defect_id="sensitivity-limit-not-established",
        description="A ladder of undetectable magnitudes bounds nothing.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: establish_sensitivity(
            _ThresholdInstrument("ladder-blind", float("inf"), 0.0),
            sub_limit_ladder(),
            LADDER_CONDITIONS,
        ).record,
    ),
    PlantedDefect(
        defect_id="non-detection-without-sensitivity",
        description="A non-detection with no established sensitivity.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: record_non_detection(
            NonDetectionObservation.from_map(
                "nd-1", LADDER_CONDITIONS, effect_size_of_interest=0.5
            ),
            None,
        ).record,
    ),
    PlantedDefect(
        defect_id="non-detection-below-sensitivity",
        description="The effect of interest is smaller than the detection limit.",
        expected=(
            (Axis.DETERMINATION, Status.INDETERMINATE),
            (Axis.INSTRUMENT, Status.OK),
        ),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: record_non_detection(
            NonDetectionObservation.from_map(
                "nd-small", LADDER_CONDITIONS, effect_size_of_interest=0.01
            ),
            established_sensitivity(),
        ).record,
    ),
    PlantedDefect(
        defect_id="absence-claim-scope-mismatch",
        description=(
            "The observation's conditions are not covered by the sensitivity's scope."
        ),
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL,),
        exercise=lambda: _claim_record(
            "ac-mismatch",
            NonDetectionObservation.from_map(
                "nd-mismatch",
                {"regime": "passive", "band": "K", "temperature": "4K"},
                effect_size_of_interest=0.5,
            ),
        )[0],
    ),
    PlantedDefect(
        defect_id="stale-reliance-on-expired-unknown",
        description="A determination rests on an expired, unreevaluated UNKNOWN.",
        expected=((Axis.DETERMINATION, Status.FAILED),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: stale_reliance({"u1": UnknownState.EXPIRED}),
    ),
)


def verify_determination_track_defects():
    """The milestone-3 (determination track) defect suite."""
    return verify_defects(DETERMINATION_TRACK_DEFECTS)


def _sample_unknown() -> UnknownDetermination:
    return UnknownDetermination(
        determination_id="u1",
        statement="the coupling regime is unresolved",
        expiry_triggers=(
            ExpiryTrigger(
                trigger_id="t1",
                kind=ExpiryTriggerKind.NEW_EVIDENCE,
                description="a new measurement of the coupling arrives",
            ),
        ),
    )


def verify_determination_track_guards() -> tuple[GuardCheck, ...]:
    """Design-contract guards for the determination track."""
    checks: list[GuardCheck] = []

    # G1: expiry is a transition, not a verdict — no failure findings.
    result = check_expiry(_sample_unknown(), ("t1",))
    ok = (
        result.expired
        and result.determination.state is UnknownState.EXPIRED
        and len(result.record.findings) == 0
        and result.transition is not None
        and result.transition.track is Track.DETERMINATION
    )
    checks.append(
        GuardCheck(
            "expiry-is-not-refutation",
            "An expired UNKNOWN produces a determination-track transition and no failure findings.",
            ok,
            f"state={result.determination.state.value} findings={len(result.record.findings)}",
        )
    )

    # G2: there is deliberately no REFUTED state.
    ok = not any(state.name == "REFUTED" for state in UnknownState)
    checks.append(
        GuardCheck(
            "no-refuted-state",
            "UnknownState has no REFUTED member; expiry is not a refutation.",
            ok,
        )
    )

    # G3: relying on an open UNKNOWN is not a failure.
    record = stale_reliance({"u-open": UnknownState.UNKNOWN})
    ok = len(record.findings) == 0
    checks.append(
        GuardCheck(
            "open-unknown-reliance-is-not-failure",
            "A determination may rest on an open UNKNOWN without a finding.",
            ok,
        )
    )

    return tuple(checks)


def run_determination_track_controls() -> tuple[ControlCheck, ...]:
    """Non-defect controls: the determination-track machinery behaving as designed."""
    checks: list[ControlCheck] = []

    # C1: a clean ladder establishes the detection limit.
    determination = established_sensitivity()
    ok = determination.established and determination.detection_limit == 0.1
    checks.append(
        ControlCheck(
            "ladder-establishes-limit",
            "A clean ladder establishes the smallest detected effect as the limit.",
            ok,
            determination.describes(),
        )
    )

    # C2: a covered effect size qualifies the non-detection.
    nd = record_non_detection(
        NonDetectionObservation.from_map(
            "nd-clean", LADDER_CONDITIONS, effect_size_of_interest=0.5
        ),
        established_sensitivity(),
    )
    ok = nd.qualified and nd.detection_limit == 0.1
    checks.append(
        ControlCheck(
            "qualified-non-detection",
            "A non-detection at or above the detection limit is qualified.",
            ok,
            f"qualified={nd.qualified}",
        )
    )

    # C3: a qualified non-detection under matching scope issues a scoped claim.
    _, claim = _claim_record(
        "ac-clean",
        NonDetectionObservation.from_map(
            "nd-clean", LADDER_CONDITIONS, effect_size_of_interest=0.5
        ),
    )
    ok = (
        isinstance(claim, AbsenceClaim)
        and claim.effect_size_floor == 0.5
        and claim.detection_limit == 0.1
        and dict(claim.scope) == LADDER_CONDITIONS
    )
    checks.append(
        ControlCheck(
            "scoped-absence-claim-issued",
            "A qualified non-detection under matching scope issues a scoped claim.",
            ok,
            claim.statement if isinstance(claim, AbsenceClaim) else "rejected",
        )
    )

    # C4: expiry fires and records a determination-track transition.
    result = check_expiry(_sample_unknown(), ("t1",))
    ok = (
        result.expired
        and result.determination.state is UnknownState.EXPIRED
        and result.transition is not None
        and result.transition.track is Track.DETERMINATION
        and result.transition.from_state == "unknown"
        and result.transition.to_state == "expired"
    )
    checks.append(
        ControlCheck(
            "expiry-transition-recorded",
            "Expiry records a determination-track transition from unknown to expired.",
            ok,
            result.transition.describe() if result.transition else "none",
        )
    )

    # C5: reevaluation preserves the original and issues a successor.
    reeval = reevaluate(
        result.determination,
        "u1-r1",
        "the coupling regime is resolved under the new measurement",
        reason="expiry trigger t1",
    )
    ok = (
        reeval.original.state is UnknownState.REEVALUATED
        and reeval.original.statement == "the coupling regime is unresolved"
        and reeval.successor.determination_id == "u1-r1"
        and reeval.successor.state is UnknownState.UNKNOWN
    )
    checks.append(
        ControlCheck(
            "reevaluation-preserves-original",
            "Reevaluation marks the original REEVALUATED and issues a successor alongside it.",
            ok,
            reeval.transition.describe(),
        )
    )

    return tuple(checks)
