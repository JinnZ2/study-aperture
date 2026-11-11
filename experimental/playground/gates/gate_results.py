"""Typed results returned by every gate."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from ..failures import FailureRecord


class GateOutcome(enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"
    BLOCKED = "blocked"  # an upstream failure prevented the gate from running


@dataclass(frozen=True)
class GateResult:
    """A gate's answer to its own question, plus the typed findings behind it.

    ``outcome`` is about the gate's question only. It is never a verdict
    about a model: PASS means "this checkpoint found no problem it was
    equipped to find", and the FailureRecord states which axes were actually
    examined.
    """

    gate_id: str
    outcome: GateOutcome
    record: FailureRecord = field(default_factory=FailureRecord)
    notes: tuple[str, ...] = ()

    @classmethod
    def blocked(cls, gate_id: str, reason: str) -> "GateResult":
        return cls(gate_id=gate_id, outcome=GateOutcome.BLOCKED, notes=(reason,))
