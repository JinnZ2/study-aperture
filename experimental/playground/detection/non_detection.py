"""Non-detection records. Later milestone.

A non-detection is recorded as a non-detection: a null result within tested
conditions is not absence. The record preserves what was tested and what
would have been required to detect the effect.
"""

from __future__ import annotations


def non_detection(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError("scheduled for a later milestone")
