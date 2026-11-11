"""UNKNOWN expiry. Later milestone.

UNKNOWN determinations carry expiry conditions: the evidence or conditions
that would warrant revisiting them. Expiry is a revision trigger, not a
negative result — an expired UNKNOWN is not a refutation.
"""

from __future__ import annotations


def unknown_expiry(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
