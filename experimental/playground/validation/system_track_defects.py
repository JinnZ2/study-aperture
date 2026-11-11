"""System-track planted defects: the continuity machinery under test.

Milestone 2 of the laboratory testing its own determinations. The suite
plugs deliberately broken return loops, configurations, and transition
sequences into the return test, the continuity matrix, and the track
machinery, and requires that every defect is caught and classified into the
correct failure class.

The load-bearing assertions:

- An asserted return violated by measured values is INDETERMINATE on the
  physical and instrument axes (genuine change vs measurement error).
- An asserted return violated by the description's own values is a
  PHYSICAL failure.
- A non-return with no assertion is an observed transition, not a failure.
- An incomplete record is a DETERMINATION indeterminacy.
- The four continuity cells plus INDETERMINATE are distinct outcomes.
- The two state tracks never map onto each other.
"""

from __future__ import annotations

from ..failures import Axis, Status
from ..gates.l0_closure import ValueProvenance
from ..lifecycle.state_transitions import (
    Track,
    TrackCrossingError,
    as_other_track,
    assert_single_track,
    determination_transition,
    system_track_transition_for_return,
    system_transition,
)
from ..reference.anchor import AnchorState
from ..reference.continuity import (
    ConfigurationObservation,
    ConfigurationPersistence,
    ContinuityCell,
    SystemPersistence,
    classify_continuity,
    compare_configurations,
)
from ..reference.return_test import ReturnOutcome, ReturnTestSpec, return_test
from .planted_defects import (
    ControlCheck,
    PlantedDefect,
    GuardCheck,
    verify_defects,
)

_TOLERANCES = {"energy": 0.1, "magnetization": 0.01}


def cell_anchor() -> AnchorState:
    return AnchorState.from_maps("cell-A", {"energy": 100.0, "magnetization": 0.5})


def _spec(
    expected_return: bool,
    energy: float,
    provenance: ValueProvenance,
    *,
    tolerances: dict[str, float] | None = None,
    drop_observation: str | None = None,
) -> ReturnTestSpec:
    returned = {
        "energy": (energy, provenance),
        "magnetization": (0.5, ValueProvenance.MEASURED),
    }
    if drop_observation:
        returned.pop(drop_observation)
    return ReturnTestSpec.from_maps(
        anchor=cell_anchor(),
        returned=returned,
        tolerances=_TOLERANCES if tolerances is None else tolerances,
        expected_return=expected_return,
    )


def lattice_configuration() -> ConfigurationObservation:
    return ConfigurationObservation.from_map(
        "cell-A-configuration",
        {"topology": "square-lattice", "coupling": "nearest-neighbor"},
    )


def rewired_configuration() -> ConfigurationObservation:
    return ConfigurationObservation.from_map(
        "cell-A-configuration",
        {"topology": "square-lattice", "coupling": "long-range"},
    )


SYSTEM_TRACK_DEFECTS: tuple[PlantedDefect, ...] = (
    PlantedDefect(
        defect_id="expected-return-measured-non-return",
        description=(
            "The description asserts a return; measured return values miss "
            "the anchor."
        ),
        expected=(
            (Axis.PHYSICAL, Status.INDETERMINATE),
            (Axis.INSTRUMENT, Status.INDETERMINATE),
            (Axis.DETERMINATION, Status.OK),
        ),
        exercise=lambda: return_test(
            _spec(True, 105.0, ValueProvenance.MEASURED)
        ).record,
    ),
    PlantedDefect(
        defect_id="expected-return-model-non-return",
        description=(
            "The description asserts a return its own model-asserted values "
            "do not produce."
        ),
        expected=(
            (Axis.PHYSICAL, Status.FAILED),
            (Axis.DETERMINATION, Status.OK),
        ),
        must_be_untested=(Axis.INSTRUMENT,),
        exercise=lambda: return_test(_spec(True, 105.0, ValueProvenance.MODEL)).record,
    ),
    PlantedDefect(
        defect_id="unasserted-non-return",
        description=(
            "A non-return with no return assertion: an observed transition, "
            "not a failure."
        ),
        expected=((Axis.DETERMINATION, Status.OK),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: return_test(
            _spec(False, 105.0, ValueProvenance.MEASURED)
        ).record,
    ),
    PlantedDefect(
        defect_id="missing-return-tolerance",
        description="An observed quantity with no declared tolerance.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: return_test(
            _spec(
                True,
                105.0,
                ValueProvenance.MEASURED,
                tolerances={"magnetization": 0.01},
            )
        ).record,
    ),
    PlantedDefect(
        defect_id="missing-return-observation",
        description="A tolerance declared for a quantity never observed on return.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: return_test(
            _spec(
                True,
                100.0,
                ValueProvenance.MEASURED,
                drop_observation="magnetization",
            )
        ).record,
    ),
    PlantedDefect(
        defect_id="tolerance-for-unanchored-quantity",
        description="A tolerance names a quantity the anchor never defined.",
        expected=((Axis.DETERMINATION, Status.INDETERMINATE),),
        must_be_untested=(Axis.PHYSICAL, Axis.INSTRUMENT),
        exercise=lambda: return_test(
            _spec(
                True,
                100.0,
                ValueProvenance.MEASURED,
                tolerances={"energy": 0.1, "magnetization": 0.01, "spin": 0.1},
            )
        ).record,
    ),
)


def verify_system_track_defects():
    """The milestone-2 (system track) defect suite."""
    return verify_defects(SYSTEM_TRACK_DEFECTS)


def verify_system_track_guards() -> tuple[GuardCheck, ...]:
    """Design-contract guards for the system track."""
    checks: list[GuardCheck] = []

    # S1: the four continuity cells plus INDETERMINATE are distinct outcomes.
    cells = {
        classify_continuity(
            SystemPersistence.PERSISTED, ConfigurationPersistence.PERSISTED
        ),
        classify_continuity(
            SystemPersistence.PERSISTED, ConfigurationPersistence.CHANGED
        ),
        classify_continuity(
            SystemPersistence.CHANGED, ConfigurationPersistence.PERSISTED
        ),
        classify_continuity(
            SystemPersistence.CHANGED, ConfigurationPersistence.CHANGED
        ),
        classify_continuity(
            SystemPersistence.INDETERMINATE, ConfigurationPersistence.PERSISTED
        ),
    }
    s1 = len(cells) == 5 and ContinuityCell.INDETERMINATE in cells
    checks.append(
        GuardCheck(
            "continuity-cells-distinct",
            "The four continuity cells plus INDETERMINATE are distinct outcomes.",
            s1,
            f"cells={sorted(c.value for c in cells)}",
        )
    )

    # S2: track crossing is refused.
    transition = system_transition("anchored", "changed", "test")
    try:
        as_other_track(transition)
        s2, detail = False, "no error raised"
    except TrackCrossingError:
        s2, detail = True, ""
    checks.append(
        GuardCheck(
            "track-crossing-refused",
            "A transition on one track is never mapped onto the other.",
            s2,
            detail,
        )
    )

    # S3: mixed tracks are rejected.
    mixed = (
        system_transition("anchored", "changed", "test"),
        determination_transition("recorded", "expired", "test"),
    )
    try:
        assert_single_track(mixed)
        s3, detail = False, "no error raised"
    except TrackCrossingError:
        s3, detail = True, ""
    checks.append(
        GuardCheck(
            "mixed-tracks-rejected",
            "A transition sequence must belong to exactly one track.",
            s3,
            detail,
        )
    )

    return tuple(checks)


def run_system_track_controls() -> tuple[ControlCheck, ...]:
    """Non-defect controls: the continuity machinery behaving as designed."""
    checks: list[ControlCheck] = []

    # C1: full continuity — the system returns and the configuration persists.
    result = return_test(_spec(False, 100.0, ValueProvenance.MEASURED))
    cell = classify_continuity(
        result.system_persistence,
        compare_configurations(lattice_configuration(), lattice_configuration()),
    )
    ok = (
        result.outcome is ReturnOutcome.RETURNED
        and cell is ContinuityCell.CONTINUOUS
    )
    checks.append(
        ControlCheck(
            "continuous-system",
            "Return within tolerance with a persisted configuration yields CONTINUOUS.",
            ok,
            f"outcome={result.outcome.value} cell={cell.value}",
        )
    )

    # C2: return with reconfiguration — same state, different organization.
    result = return_test(_spec(False, 100.0, ValueProvenance.MEASURED))
    cell = classify_continuity(
        result.system_persistence,
        compare_configurations(lattice_configuration(), rewired_configuration()),
    )
    ok = cell is ContinuityCell.RETURN_WITH_RECONFIGURATION
    checks.append(
        ControlCheck(
            "return-with-reconfiguration",
            "A returned state with a changed configuration is its own cell, not CONTINUOUS.",
            ok,
            f"cell={cell.value}",
        )
    )

    # C3: drift with stable configuration — state changed, structure persisted.
    result = return_test(_spec(False, 105.0, ValueProvenance.MEASURED))
    cell = classify_continuity(
        result.system_persistence,
        compare_configurations(lattice_configuration(), lattice_configuration()),
    )
    ok = cell is ContinuityCell.DRIFT_WITH_STABLE_CONFIGURATION
    checks.append(
        ControlCheck(
            "drift-with-stable-configuration",
            "A changed state with a persisted configuration is its own cell.",
            ok,
            f"cell={cell.value}",
        )
    )

    # C4: discontinuity — both changed.
    result = return_test(_spec(False, 105.0, ValueProvenance.MEASURED))
    cell = classify_continuity(
        result.system_persistence,
        compare_configurations(lattice_configuration(), rewired_configuration()),
    )
    ok = cell is ContinuityCell.DISCONTINUOUS
    checks.append(
        ControlCheck(
            "discontinuous-system",
            "A changed state with a changed configuration yields DISCONTINUOUS.",
            ok,
            f"cell={cell.value}",
        )
    )

    # C5: an indeterminate component yields an indeterminate cell.
    result = return_test(
        _spec(True, 105.0, ValueProvenance.MEASURED, tolerances={"energy": 0.1})
    )
    cell = classify_continuity(
        result.system_persistence, ConfigurationPersistence.PERSISTED
    )
    ok = cell is ContinuityCell.INDETERMINATE
    checks.append(
        ControlCheck(
            "indeterminate-component-is-indeterminate-cell",
            "An incomplete record never projects onto a definite continuity cell.",
            ok,
            f"outcome={result.outcome.value} cell={cell.value}",
        )
    )

    # C6: a return outcome becomes a system-track transition, never a determination one.
    result = return_test(_spec(False, 105.0, ValueProvenance.MEASURED))
    transition = system_track_transition_for_return(result)
    ok = transition.track is Track.SYSTEM and transition.to_state == "not_returned"
    checks.append(
        ControlCheck(
            "return-outcome-is-system-track-transition",
            "The return outcome records on the system track only.",
            ok,
            transition.describe(),
        )
    )

    return tuple(checks)
