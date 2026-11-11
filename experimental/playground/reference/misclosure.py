"""Misclosure: the residual of the anchor -> perturbation -> return loop.

Misclosure is to the system track what UNKNOWN expiry is to the
determination track: the measured failure of a loop to close. This module
computes residuals only; classification (physical / instrument /
determination) lives in the return test, and follows the provenance of the
compared quantities, mirroring the L0 gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .anchor import AnchorState


@dataclass(frozen=True)
class Misclosure:
    quantity: str
    residual: float  # returned - anchor
    tolerance: float
    within_tolerance: bool

    @property
    def ratio(self) -> float:
        """|residual| / tolerance; greater than 1 means beyond tolerance."""
        if self.tolerance == 0.0:
            return float("inf") if self.residual != 0.0 else 0.0
        return abs(self.residual) / self.tolerance


def compute_misclosure(
    anchor: AnchorState,
    returned: Mapping[str, float],
    tolerances: Mapping[str, float],
) -> tuple[Misclosure, ...]:
    """Per-quantity residuals of the return loop. Pure computation, no classification.

    Quantities missing from the anchor or from the return observation are
    skipped here; recording that incompleteness is the return test's job.
    """
    results: list[Misclosure] = []
    for quantity in sorted(tolerances):
        anchor_value = anchor.as_dict().get(quantity)
        if anchor_value is None or quantity not in returned:
            continue
        residual = returned[quantity] - anchor_value
        tolerance = tolerances[quantity]
        results.append(
            Misclosure(
                quantity=quantity,
                residual=residual,
                tolerance=tolerance,
                within_tolerance=abs(residual) <= tolerance,
            )
        )
    return tuple(results)


def worst_ratio(misclosures: tuple[Misclosure, ...]) -> float:
    """Largest |residual|/tolerance ratio; 0.0 when there is nothing to compare."""
    return max((m.ratio for m in misclosures), default=0.0)
