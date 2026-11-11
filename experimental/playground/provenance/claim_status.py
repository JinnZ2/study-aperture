"""Claim records: status without verdicts.

A claim records what was asserted, its scope, and its support state. There
is deliberately no state meaning "verified" or "refuted": those are
verdicts, and verdicts belong to determinations, not to claim records. An
integrity PASS must not silently change claim support — the evidence chain
binds reports to claims by digest without touching this record.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass


class ClaimState(enum.Enum):
    DRAFT = "draft"  # asserted, not yet entered into the record
    RECORDED = "recorded"  # entered into the evidence record
    UNKNOWN = "unknown"  # assessment unresolved; not a verdict
    RETIRED = "retired"  # withdrawn from active assessment


class SupportState(enum.Enum):
    NONE = "none"
    PARTIAL = "partial"  # some bound evidence links, within recorded scope
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    statement: str
    state: ClaimState = ClaimState.DRAFT
    support: SupportState = SupportState.NONE
    scope_conditions: tuple[str, ...] = ()
