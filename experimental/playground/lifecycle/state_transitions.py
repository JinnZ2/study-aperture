"""State transitions for the system and determination tracks.

Two state tracks run through the laboratory and never merge:

- System track: anchor -> perturbation -> return -> misclosure.
- Determination track: issued -> conditions recorded -> expiry -> reevaluation.

Misclosure is to the system what UNKNOWN expiry is to the determination.
This module records transitions on either track and refuses to map one
track onto the other: a system-track transition is never converted into a
determination-track transition, and vice versa. A physical transition
(the system reorganizes, accumulates energy, loses connectivity, crosses a
threshold, adapts, or changes its relationships) is recorded on the system
track; a revision of the boundary, controls, or observer regime is recorded
on the determination track.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterable

from ..failures import EvidenceRef
from ..reference.return_test import ReturnTestResult


class Track(enum.Enum):
    SYSTEM = "system"
    DETERMINATION = "determination"


class SystemChangeType(enum.Enum):
    """How a physical system changes (recorded on the system track only)."""

    REORGANIZES = "reorganizes"
    ACCUMULATES_ENERGY = "accumulates-energy"
    LOSES_CONNECTIVITY = "loses-connectivity"
    CROSSES_THRESHOLD = "crosses-threshold"
    ADAPTS = "adapts"
    CHANGES_RELATIONSHIPS = "changes-relationships"


class TrackCrossingError(TypeError):
    """Raised when a transition on one track would be mapped onto the other."""


@dataclass(frozen=True)
class StateTransition:
    track: Track
    from_state: str
    to_state: str
    trigger: str
    change_type: SystemChangeType | None = None  # system track only
    evidence: tuple[EvidenceRef, ...] = ()

    def describe(self) -> str:
        change = f" ({self.change_type.value})" if self.change_type else ""
        return (
            f"[{self.track.value}] {self.from_state} -> {self.to_state}{change} "
            f"via {self.trigger}"
        )


def system_transition(
    from_state: str,
    to_state: str,
    trigger: str,
    change_type: SystemChangeType | None = None,
    evidence: tuple[EvidenceRef, ...] = (),
) -> StateTransition:
    """Record a system-track transition. Never produces a determination-track transition."""
    return StateTransition(
        track=Track.SYSTEM,
        from_state=from_state,
        to_state=to_state,
        trigger=trigger,
        change_type=change_type,
        evidence=evidence,
    )


def determination_transition(
    from_state: str,
    to_state: str,
    trigger: str,
    evidence: tuple[EvidenceRef, ...] = (),
) -> StateTransition:
    """Record a determination-track transition. Never produces a system-track transition."""
    return StateTransition(
        track=Track.DETERMINATION,
        from_state=from_state,
        to_state=to_state,
        trigger=trigger,
        change_type=None,
        evidence=evidence,
    )


def as_other_track(transition: StateTransition) -> StateTransition:
    """Deliberately forbidden.

    Mapping a system-track transition onto the determination track (or vice
    versa) is exactly the conflation this laboratory exists to prevent: a
    physical transition is not a change in experimental determination.
    """
    raise TrackCrossingError(
        f"Refusing to map a {transition.track.value}-track transition onto the "
        f"other track. A physical transition is not a change in experimental "
        f"determination, and a revision of the determination is not a change "
        f"in the physical system."
    )


def assert_single_track(transitions: Iterable[StateTransition]) -> Track:
    """Validate that a transition sequence belongs to exactly one track."""
    tracks = {t.track for t in transitions}
    if len(tracks) != 1:
        names = sorted(t.value for t in tracks)
        raise TrackCrossingError(
            f"transitions span multiple tracks: {names}"
        )
    return next(iter(tracks))


def system_track_transition_for_return(
    result: ReturnTestResult,
    change_type: SystemChangeType | None = None,
    evidence: tuple[EvidenceRef, ...] = (),
) -> StateTransition:
    """Translate a return-test outcome into the system-track transition it records.

    The transition records what the system did; it says nothing about the
    determination that produced the test.
    """
    return system_transition(
        from_state="anchored",
        to_state=result.outcome.value,
        trigger="return-to-anchor test",
        change_type=change_type,
        evidence=evidence,
    )
