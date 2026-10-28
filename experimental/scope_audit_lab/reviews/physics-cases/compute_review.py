#!/usr/bin/env python3
"""Authoring-only synthetic arithmetic, not a model or evidence validator.

Run locally with Python's standard library. JSON is written only to stdout.
No equation parser, unit conversion engine, measurement access, or root-cause
classifier is implemented here.
"""

import hashlib
import json
import math
import platform
from fractions import Fraction
from pathlib import Path


HERE = Path(__file__).resolve().parent
LAB = HERE.parent.parent


def unavailable(reason):
    return {"status": "UNAVAILABLE", "reason": reason}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review():
    # Exponent order is locally declared as mass, length, time.
    # These are hand-declared fixture expressions, not parsed equations.
    energy = (1, 2, -2)
    mass = (1, 0, 0)
    speed = (0, 1, -1)
    mv = tuple(a + b for a, b in zip(mass, speed))
    mvv = tuple(a + 2 * b for a, b in zip(mass, speed))

    # Total transfer rates are stipulated, not measured. "All transfers
    # included" is a fixture assumption, not an established property.
    p_in, p_out = 100, 120
    required_storage_rate = p_in - p_out

    angles = []
    for degrees in (0, 1, 5, 10, 14.5, 15, 30, 45, 60):
        theta = math.radians(degrees)
        sine = math.sin(theta)
        difference = abs(theta - sine)
        angles.append({
            "angle_degrees": degrees,
            "angle_radians": theta,
            "absolute_difference": difference,
            "relative_difference_denominator": "abs(sin(theta))",
            "relative_difference": (
                difference / abs(sine) if sine != 0 else
                unavailable("The defined denominator is zero; no extension was specified.")
            ),
        })

    # Inclusive threshold equality is checked exactly in error space.
    # This does not claim an exactly represented angular crossing.
    threshold = Fraction(1, 100)
    threshold_cases = []
    for label, error in (
        ("below", Fraction(999, 100000)),
        ("at", Fraction(1, 100)),
        ("above", Fraction(1001, 100000)),
    ):
        threshold_cases.append({
            "position": label,
            "error_exact": str(error),
            "threshold_exact": str(threshold),
            "rule": "error <= threshold",
            "criterion_met": error <= threshold,
        })

    # Exact mathematical identity:
    # 1/(1-e) - (1+e) = e^2/(1-e), e != 1.
    approximation = []
    for epsilon in (Fraction(-1, 10), Fraction(0), Fraction(1, 10)):
        exact = 1 / (1 - epsilon)
        approx = 1 + epsilon
        absolute = abs(exact - approx)
        relative = absolute / abs(exact)
        approximation.append({
            "epsilon_exact": str(epsilon),
            "reference_exact": str(exact),
            "approximation_exact": str(approx),
            "absolute_error_exact": str(absolute),
            "relative_error_exact": str(relative),
            "absolute_error_le_1_percent_of_one": absolute <= threshold,
            "relative_error_le_1_percent_of_reference": relative <= threshold,
        })

    # Shared-variable algebra, not an uncertainty estimator:
    # Var(Y-P) = Var(Y) + Var(P) - 2 Cov(Y,P).
    uncertainty = []
    for covariance, basis in (
        (0, "Explicit synthetic zero-covariance assumption."),
        (12, "Explicit synthetic perfect-positive-correlation assumption."),
    ):
        variance = 3**2 + 4**2 - 2 * covariance
        uncertainty.append({
            "sigma_observation": 3,
            "sigma_prediction": 4,
            "covariance": covariance,
            "assumption_basis": basis,
            "residual_variance": variance,
            "residual_standard_uncertainty": math.sqrt(variance),
        })

    return {
        "artifact_kind": "AUTHORING_REVIEW_CALCULATIONS",
        "fixture_status": "SYNTHETIC_NOT_EMPIRICAL",
        "procedure": "compute_review.py / physics-review-1",
        "python_version": platform.python_version(),
        "examined_sha256": {
            "compute_review.py": digest(Path(__file__)),
            "evidence.schema.json": digest(
                LAB / "schemas/draft-0.1/evidence.schema.json"
            ),
            "schema_example_records.json": digest(
                LAB / "examples/schema-draft-0.1/records.json"
            ),
            "requirements_0.2.md": digest(
                LAB / "requirements/scope-audit-lab-0.2.md"
            ),
        },
        "dimensions": {
            "basis_order": ["mass", "length", "time"],
            "declared_energy": energy,
            "declared_mass_times_speed": mv,
            "declared_mass_times_speed_squared": mvv,
            "energy_equals_mass_times_speed_dimensions": energy == mv,
            "energy_equals_mass_times_speed_squared_dimensions": energy == mvv,
            "dimensionless_coefficient_determined": False,
            "physical_law_established": False,
        },
        "balance": {
            "units": "W",
            "synthetic_total_power_in": p_in,
            "synthetic_total_power_out": p_out,
            "measured_storage_rate": unavailable("No storage measurement was supplied."),
            "residual_with_missing_storage": unavailable(
                "r = dE/dt - (P_in - P_out) requires a supplied storage rate."
            ),
            "required_storage_rate_for_zero_residual": required_storage_rate,
            "conditional_residual_if_storage_rate_is_minus_20": (
                -20 - (p_in - p_out)
            ),
            "conditional_residual_if_storage_rate_is_zero": 0 - (p_in - p_out),
            "cause_selected": False,
        },
        "small_angle": {
            "metric": "abs(theta - sin(theta)) / abs(sin(theta)); theta in radians",
            "not_a_period_error_estimate": True,
            "cases": angles,
            "exact_threshold_comparisons_in_error_space": threshold_cases,
            "threshold_is_user_chosen_not_a_physical_boundary": True,
        },
        "rational_approximation": {
            "formula": "F(epsilon)=1/(1-epsilon), A(epsilon)=1+epsilon",
            "reference_domain": "real epsilon != 1",
            "review_interval": "-1/10 <= epsilon <= 1/10",
            "absolute_error_bound_on_review_interval_exact": "1/90",
            "relative_error_bound_on_review_interval_exact": "1/100",
            "cases": approximation,
        },
        "uncertainty": {
            "quantity_units": "declared common scalar unit U",
            "covariance_and_variance_units": "U^2",
            "missing_covariance_result": unavailable(
                "No independence or zero-covariance assumption may be inferred."
            ),
            "conditional_examples": uncertainty,
        },
        "limitations": [
            "These calculations are author-generated synthetic fixtures.",
            "No laboratory observation, external experiment, or empirical validation.",
            "No runtime Scope Audit Lab validator or acceptance-suite implementation.",
            "Python floating-point trigonometry is not an interval proof.",
            "Exact fractions are used only for these authoring illustrations.",
            "A future numerical backend and uncertainty policy remain undecided.",
            "A zero residual establishes only arithmetic agreement under supplied assumptions.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, allow_nan=False))
