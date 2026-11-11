"""UNKNOWN expiry.

UNKNOWN determinations carry expiry conditions: the evidence or conditions
that warrant revisiting them. Expiry is a revision trigger, not a negative
result — an expired UNKNOWN is not a refutation, and there is deliberately
no REFUTED state. An expired UNKNOWN requires reevaluation; until
reevaluated, determinations that rely on it are stale (see
lifecycle.reevaluation.stale_reliance).

Expiry produces a determination-track transition and no failure findings:
the UNKNOWN was honest when issued, and its expiry is new information, not
a defect.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from typing import Mapping

from ..failures import EvidenceRef, FailureRecord
from .state_transitions import StateTransition, determination_transition


class UnknownState(enum.Enum):
    UNKNOWN = "unknown"  # open; expiry conditions recorded
    EXPIRED = "expired"  # a trigger fired; reevaluation required (not refuted)
    REEVALUATED = "reevaluated"  # revisited; superseded by a successor determination


class ExpiryTriggerKind(enum.Enum):
    NEW_EVIDENCE = "new-evidence"
    CONDITION_CHANGE = "condition-change"
    INSTRUMENT_CHANGE = "instrument-change"
    REVISION_DEPENDENCY = "revision-dependency"


@dataclass(frozen=True)
class ExpiryTrigger:
    trigger_id: str
    kind: ExpiryTriggerKind
    description: str = ""


@dataclass(frozen=True)
class UnknownDetermination:
    determination_id: str
    statement: str
    state: UnknownState = UnknownState.UNKNOWN
    scope_conditions: tuple[tuple[str, str], ...] = ()
    expiry_triggers: tuple[ExpiryTrigger, ...] = ()
    evidence: tuple[EvidenceRef, ...] = ()

    @classmethod
    def from_map(
        cls,
        determination_id: str,
        statement: str,
        scope_conditions: Mapping[str, str] | None = None,
        expiry_triggers: tuple[ExpiryTrigger, ...] = (),
        evidence: tuple[EvidenceRef, ...] = (),
    ) -> "UnknownDetermination":
        return cls(
            determination_id=determination_id,
            statement=statement,
            scope_conditions=tuple(sorted((scope_conditions or {}).items())),
            expiry_triggers=expiry_triggers,
            evidence=evidence,
        )


@dataclass(frozen=True)
class ExpiryResult:
    determination: UnknownDetermination  # the determination after the check
    expired: bool
    fired: tuple[ExpiryTrigger, ...]
    transition: StateTransition | None
    record: FailureRecord
    notes: tuple[str, ...] = ()


def check_expiry(
    unknown: UnknownDetermination, fired_trigger_ids: tuple[str, ...]
) -> ExpiryResult:
    """Fire registered expiry triggers; never issue a refutation.

    Expiry is a revision trigger. The result carries a determination-track
    transition and no failure findings: an expired UNKNOWN is not a failed
    determination, it is a determination that must be revisited.
    """
    if unknown.state is not UnknownState.UNKNOWN:
        return ExpiryResult(
            unknown,
            False,
            (),
            None,
            FailureRecord(),
            (f"determination is {unknown.state.value}, not an open UNKNOWN",),
        )

    fired = tuple(
        t for t in unknown.expiry_triggers if t.trigger_id in fired_trigger_ids
    )
    if not fired:
        return ExpiryResult(
            unknown,
            False,
            (),
            None,
            FailureRecord(),
            ("no registered expiry trigger fired",),
        )

    expired = replace(unknown, state=UnknownState.EXPIRED)
    trigger_ids = ", ".join(t.trigger_id for t in fired)
    transition = determination_transition(
        "unknown",
        "expired",
        f"expiry trigger(s): {trigger_ids}",
        evidence=unknown.evidence,
    )
    return ExpiryResult(
        expired,
        True,
        fired,
        transition,
        FailureRecord(),
        (
            f"trigger(s) fired: {trigger_ids}",
            "an expired UNKNOWN is not a refutation; reevaluation is required",
        ),
    )
