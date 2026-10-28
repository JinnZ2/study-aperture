#!/usr/bin/env python3
"""Optional authoring-only structural probes; NOT a lab runtime validator.

Requires the authoring reviewer's external jsonschema package. Run without
installing any project/runtime dependency, for example using an isolated
reviewer environment. Reports acceptance by JSON Schema, not equation validity.
"""

import copy
import hashlib
import importlib.metadata
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


LAB = Path(__file__).resolve().parent.parent.parent
SCHEMA = LAB / "schemas/draft-0.1/evidence.schema.json"
EXAMPLES = LAB / "examples/schema-draft-0.1/records.json"


def text(value):
    return {"status": "PRESENT", "value": value}


def symbol(name, meaning, quantity, dimensions, units):
    return {
        "symbol": name,
        "meaning": text(meaning),
        "mathematical_type": text("real scalar"),
        "domain": text("declared real scalar domain"),
        "quantity": text(quantity),
        "dimensions": text(dimensions),
        "units": text(units),
        "conventions": text("Fixture declarations, not measured properties."),
    }


def review():
    schema = json.loads(SCHEMA.read_text())
    baseline = json.loads(EXAMPLES.read_text())["records"][0]
    checker = FormatChecker()
    if checker.conforms("not-a-date", "date-time"):
        raise RuntimeError("Reviewer lacks working date-time format checking.")
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=checker)
    results = []
    for case_id, statement, symbols, domain, missing_check in (
        (
            "P-01",
            "E = m*v",
            [
                symbol("E", "energy", "energy", "M L^2 T^-2", "J"),
                symbol("m", "mass", "mass", "M", "kg"),
                symbol("v", "speed", "speed", "L T^-1", "m/s"),
            ],
            "Real scalars with the explicitly declared physical quantities.",
            "Dimensional compatibility is not evaluated by JSON Schema.",
        ),
        (
            "P-07",
            "dy/dt = 0 therefore y(t) = 0",
            [
                symbol("y", "abstract dependent variable", "abstract scalar", "1", "1"),
                symbol("t", "abstract independent variable", "abstract scalar", "1", "1"),
            ],
            "Differentiable real y on a connected real interval; no initial condition supplied.",
            "The unprovided initial condition and implication are not checked.",
        ),
    ):
        instance = copy.deepcopy(baseline)
        instance["record_id"] = "physics-review:" + case_id.lower()
        instance["record_version"] = text("authoring-physics-review-1")
        payload = instance["payload"]
        payload["exact_statement"] = statement
        payload["statement_kind"] = "THEOREM_CLAIM"
        payload["original"]["text"] = statement
        payload["original"]["source_location"] = text(
            "Synthetic equation authored by probe_schema.py; not a publication."
        )
        payload["symbols"] = symbols
        payload["scope"]["domain"] = text(domain)
        payload["scope"]["included"] = text("Structural boundary probe only.")
        payload["scope"]["excluded"] = text("No empirical interpretation established.")
        payload["scope"]["initial_conditions"] = {
            "status": "MISSING", "reason": "No condition supplied."
        }
        payload["assumption_refs"] = []
        errors = list(validator.iter_errors(instance))
        results.append({
            "case_id": case_id,
            "input_record": instance,
            "schema_accepted": not errors,
            "structural_errors": [error.message for error in errors],
            "semantic_boundary": missing_check,
            "semantic_assessment_executed": False,
        })
    return {
        "artifact_kind": "AUTHORING_STRUCTURAL_BOUNDARY_PROBES",
        "procedure": "probe_schema.py / physics-review-1",
        "reviewer": {
            "jsonschema": importlib.metadata.version("jsonschema"),
            "rfc3339-validator": importlib.metadata.version("rfc3339-validator"),
            "date_time_support_verified": True,
        },
        "examined_sha256": {
            "schema": hashlib.sha256(SCHEMA.read_bytes()).hexdigest(),
            "examples": hashlib.sha256(EXAMPLES.read_bytes()).hexdigest(),
            "procedure": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "results": results,
        "limitations": [
            "A schema-accepted record is not a mathematically valid equation.",
            "These synthetic inputs and procedures have the same author.",
            "No lab runtime validator or acceptance test is implemented.",
            "No source, evidence-graph, or physical assertion was authenticated.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, allow_nan=False))
