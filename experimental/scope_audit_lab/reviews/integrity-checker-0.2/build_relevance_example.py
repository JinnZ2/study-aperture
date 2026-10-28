#!/usr/bin/env python3
"""Generate one synthetic relevance demonstration, not measured evidence."""

import copy
import hashlib
import json
from pathlib import Path


LAB = Path(__file__).resolve().parents[2]
BASE = LAB / "examples/schema-draft-0.2/records.json"
VERSION = "relevance-fixture-1"


def present(value):
    return {"status": "PRESENT", "value": value}


def ref(name, kind):
    return {"record_id": "relevance-demo:" + name, "expected_type": kind,
            "resolution": "NOT_CHECKED"}


def rewrite(value):
    if isinstance(value, list):
        return [rewrite(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key == "record_id" and isinstance(item, str) and item.startswith("physics-draft:"):
            result[key] = item.replace("physics-draft:", "relevance-demo:", 1)
        elif (key in {"record_version", "examined_version", "anchor_version"} and
              isinstance(item, dict) and item.get("status") == "PRESENT"):
            result[key] = present(VERSION)
        else:
            result[key] = rewrite(item)
    return result


def build():
    bundle = rewrite(json.loads(BASE.read_text()))
    records = bundle["records"]
    by_id = {r["record_id"].split(":", 1)[1]: r for r in records}
    for record in records:
        record["producer"] = {
            "identity": present("study-aperture relevance-example authoring"),
            "kind": "PROCESS", "version": present("build_relevance_example.py / 1"),
        }
    # Correct ID/version metadata; existing assessment is still NOT_EVALUATED.
    by_id["residual"]["payload"]["assessment_refs"] = [ref("residual-assessment", "assessment")]
    # Target exists but examines the calculation, not this balance record.
    by_id["balance"]["payload"]["assessment_refs"] = [ref("residual-assessment", "assessment")]
    # Subject identity/version agree, but the selector names the wrong verdict field.
    field_assessment = copy.deepcopy(by_id["residual-assessment"])
    field_assessment["record_id"] = "relevance-demo:applicability-field-assessment"
    payload = field_assessment["payload"]
    payload["subjects"] = [{
        "subject": ref("energy-application", "anchor_application"),
        "examined_version": present(VERSION), "examined_state_artifact_refs": [],
        "selector": present("payload.applicability_status"),
    }]
    payload["property"] = "Authored applicability-field review placeholder, not an executed assessment."
    payload["dependency_refs"] = [ref("energy-anchor", "physics_anchor")]
    payload["criteria"][0].update(
        criterion_id="applicability-field-placeholder",
        exact_rule="Inspect the stated applicability property; no inspection result is asserted.",
        rationale="Synthetic unevaluated criterion; it must not substantiate another verdict field.",
    )
    by_id["energy-application"]["payload"]["comparison_assessment_refs"] = [
        ref("applicability-field-assessment", "assessment")
    ]
    records.append(field_assessment)
    bundle["bundle_kind"] = "SYNTHETIC_ASSESSMENT_RELEVANCE_DEMONSTRATION"
    bundle["derived_from_local_fixture"] = {
        "path_relative_to_lab": str(BASE.relative_to(LAB)),
        "sha256": hashlib.sha256(BASE.read_bytes()).hexdigest(),
        "method": "New namespace and fixture versions; three explicit assessment-link scenarios.",
    }
    bundle["expected_link_relevance"] = [
        {"owner_record_id": "relevance-demo:residual", "status": "METADATA_MATCH_ONLY"},
        {"owner_record_id": "relevance-demo:balance", "status": "UNRELATED_SUBJECT"},
        {"owner_record_id": "relevance-demo:energy-application", "status": "SELECTOR_MISMATCH"},
    ]
    bundle["limitations"] = [
        "Synthetic fixtures, not measurements or performed scientific assessments.",
        "Matched subject metadata does not establish property relevance, criterion validity, or support.",
        "Original example bundle is unchanged; this fixture uses different record IDs.",
    ]
    return bundle


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, allow_nan=False))
