"""Finite numeric contracts shared by diagnostic harnesses and equation adapters."""

from __future__ import annotations

import math
from typing import Mapping


def finite_number(value: object) -> bool:
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except (OverflowError, TypeError):
        return False


def pair_map(pairs: tuple[tuple[str, float], ...]) -> dict[str, float]:
    if not isinstance(pairs, tuple):
        raise ValueError("numeric records must use immutable pairs")
    result = {}
    for pair in pairs:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("expected (name, value) pairs")
        key, value = pair
        if not isinstance(key, str) or not key.strip() or key in result:
            raise ValueError("numeric names must be nonempty and unique")
        if not finite_number(value):
            raise ValueError(f"{key}: expected a finite real number, not bool/NaN/inf")
        result[key] = value
    return result


def validate_case_data(inputs: tuple, outputs: tuple, tolerances: tuple) -> None:
    pair_map(inputs)
    expected, tol = pair_map(outputs), pair_map(tolerances)
    if not expected:
        raise ValueError("a diagnostic case must assert at least one output")
    if set(expected) != set(tol):
        raise ValueError("tolerances must cover exactly the asserted outputs")
    if any(value < 0 for value in tol.values()):
        raise ValueError("tolerances must be nonnegative")


def finite_outputs(outputs: Mapping[str, float]) -> dict[str, float]:
    got = dict(outputs)
    if not got or any(not isinstance(k, str) or not k.strip() for k in got):
        raise ValueError("instrument must return named numeric outputs")
    if any(not finite_number(value) for value in got.values()):
        raise ValueError("instrument returned a non-finite or non-real output")
    return got
