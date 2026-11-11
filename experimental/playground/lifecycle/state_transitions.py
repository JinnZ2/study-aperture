"""State transitions for both tracks. Later milestone.

Two typed transition sets, one per track. A physical transition (system
reorganization, threshold crossing, connectivity loss) changes the system
track; a revision of boundary, controls, or observer regime changes the
determination track. The module refuses to map one onto the other.
"""

from __future__ import annotations


def state_transitions(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
