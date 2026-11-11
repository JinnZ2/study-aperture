"""Anchor and reference configuration.

The anchor is the frozen reference state of the system track. Once frozen,
its digest is the binding: any change produces a different anchor — a new
reference state, not a correction of the old one. The determination track
has its own reference lifecycle (lifecycle.unknown_expiry); the two tracks
are deliberately separate.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class AnchorState:
    label: str
    quantities: tuple[tuple[str, float], ...] = ()
    conditions: tuple[str, ...] = ()

    @classmethod
    def from_maps(
        cls,
        label: str,
        quantities: dict[str, float],
        conditions: tuple[str, ...] = (),
    ) -> "AnchorState":
        return cls(
            label=label,
            quantities=tuple(sorted(quantities.items())),
            conditions=tuple(conditions),
        )

    def as_dict(self) -> dict[str, float]:
        return dict(self.quantities)

    def value(self, quantity: str) -> float:
        return self.as_dict()[quantity]  # KeyError is the honest failure

    def digest(self) -> str:
        payload = ";".join(
            ["label:" + self.label]
            + [f"{k}={v!r}" for k, v in self.quantities]
            + ["cond:" + c for c in self.conditions]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def same_anchor(a: AnchorState, b: AnchorState) -> bool:
    """True only if the digests match. False means the reference changed; it does not say how or why."""
    return a.digest() == b.digest()
