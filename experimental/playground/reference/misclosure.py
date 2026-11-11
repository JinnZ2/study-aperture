"""Misclosure calculation for the return loop. Later milestone.

The residual of the anchor -> perturbation -> return loop. Misclosure
beyond tolerance is a finding, and its classification (physical vs
instrument vs determination) depends on the provenance of the compared
quantities, mirroring the L0 gate. Misclosure is to the system track what
UNKNOWN expiry is to the determination track.
"""

from __future__ import annotations


def misclosure(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
