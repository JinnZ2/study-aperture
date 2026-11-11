"""Reevaluation on revision edges. Later milestone.

A revision dependency (new evidence warrants revisiting a prior
experimental choice) triggers reevaluation of the affected determination.
Reevaluation reopens the determination; it does not overturn it by default.
"""

from __future__ import annotations


def reevaluation(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
