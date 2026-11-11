"""Return-to-anchor test (system-track continuity). Later milestone.

Perturb the system, then test whether it returns to the frozen anchor
within declared tolerances. Preserves the distinction between system
persistence and configuration persistence (the continuity matrix): a system
can return to its anchor state while its configuration changed, and vice
versa. A failed return is a finding whose classification (physical vs
instrument) depends on the provenance of the compared quantities,
mirroring the L0 gate.
"""

from __future__ import annotations


def return_test(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
