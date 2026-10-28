#!/usr/bin/env python3
"""Authoring-only offline JSON Schema review, not a runtime semantic validator.

External authoring dependencies: jsonschema, referencing, rfc3339-validator.
No project dependency, remote schema retrieval, or network access is required.
"""

import copy
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource


LAB = Path(__file__).resolve().parent.parent.parent
OLD = LAB / "schemas/draft-0.1/evidence.schema.json"
NEW = LAB / "schemas/draft-0.2/extensions.schema.json"
FIXTURES = LAB / "examples/schema-draft-0.2/records.json"
OLD_FIXTURES = LAB / "examples/schema-draft-0.1/records.json"
REQUIREMENTS = LAB / "requirements/scope-audit-lab-0.2.md"


def read(path):
    def invalid_constant(value):
        raise ValueError("Non-standard JSON constant: " + value)
    return json.loads(path.read_text(), parse_constant=invalid_constant)


def no_remote(uri):
    raise NoSuchResource(ref=uri)


def review():
    old, new = read(OLD), read(NEW)
    registry = Registry(retrieve=no_remote).with_resources([
        (schema["$id"], Resource.from_contents(schema)) for schema in (old, new)
    ])
    checker = FormatChecker()
    if checker.conforms("not-a-date", "date-time"):
        raise RuntimeError("Working date-time format checking is required.")
    validators = {}
    for schema in (old, new):
        Draft202012Validator.check_schema(schema)
        validators[schema["$id"]] = Draft202012Validator(
            schema, registry=registry, format_checker=checker
        )
    records = read(FIXTURES)["records"]
    original_records = read(OLD_FIXTURES)["records"]
    by_kind = {}
    for record in records:
        by_kind.setdefault(record["record_type"], record)
    record_results = []
    for collection, entries in (("new_bundle", records), ("original_bundle", original_records)):
        for record in entries:
            errors = list(validators[record["schema_id"]].iter_errors(record))
            record_results.append({
                "collection": collection, "record_id": record["record_id"],
                "schema_accepted": not errors,
                "errors": [{"path": list(e.absolute_path), "message": e.message} for e in errors],
            })

    probes = []

    def probe(identifier, description, kind, mutate, expected, boundary=None):
        record = copy.deepcopy(by_kind[kind])
        mutate(record)
        errors = list(validators[by_kind[kind]["schema_id"]].iter_errors(record))
        accepted = not errors
        entry = {
            "case_id": identifier, "description": description,
            "expected_schema_acceptance": expected, "schema_accepted": accepted,
            "expectation_matched": accepted == expected,
            "input_record": record,
            "error_paths": [list(e.absolute_path) for e in errors],
        }
        if boundary:
            entry["semantic_limit"] = boundary
        probes.append(entry)

    def set_payload(key, value):
        return lambda record: record["payload"].__setitem__(key, value)

    p = {"status": "PRESENT", "value": 0, "encoding": "json_number"}
    absent = {"status": "MISSING", "reason": "Authoring missingness probe."}
    t = lambda s: {"status": "PRESENT", "value": s}
    fake_assessment = {
        "record_id": "unresolved:assessment", "expected_type": "assessment",
        "resolution": "NOT_CHECKED",
    }
    probe("D02-01", "Unrecognized schema version is rejected.", "quantity_definition",
          lambda r: r.__setitem__("schema_version", "9.9"), False)
    probe("D02-02", "Missing dimensions remain representable.", "quantity_definition",
          set_payload("dimensions", absent), True)
    probe("D02-03", "Zero exponent denominator is rejected.", "quantity_definition",
          lambda r: r["payload"]["dimensions"]["exponents"][0].__setitem__("denominator", 0), False)
    probe("D02-04", "Six rather than seven dimension exponents are rejected.", "quantity_definition",
          lambda r: r["payload"]["dimensions"]["exponents"].pop(), False)
    probe("D02-05", "An explicit dimension-one declaration is accepted.", "quantity_definition",
          lambda r: [e.__setitem__("numerator", 0) for e in r["payload"]["dimensions"]["exponents"]], True)
    probe("D02-06", "Scalar declaration with vector shape is rejected.", "quantity_definition",
          lambda r: r["payload"]["structure"].__setitem__("component_shape", [3]), False)
    probe("D02-07", "An unsupported verified flag is rejected.", "quantity_definition",
          set_payload("verified", True), False)
    probe("D02-08", "A zero unit scale is rejected.", "quantity_definition",
          lambda r: r["payload"]["unit"].__setitem__("scale_to_reference", p), False)
    probe("D02-09", "Unexecuted calculation cannot assert a present zero result.", "calculation",
          set_payload("result", p), False)
    probe("D02-10", "Missing calculation result remains representable.", "calculation",
          lambda r: None, True)
    probe("D02-11", "Completion assertion with result is structurally accepted without execution artifacts.", "calculation",
          lambda r: r["payload"].update(execution_status="COMPLETED", result=p), True,
          "A semantic checker must distinguish unsupported completion/result assertions from recorded execution.")
    probe("D02-12", "A definitive prerequisite outcome without evidence references is rejected.", "calculation",
          lambda r: r["payload"]["prerequisites"][0].__setitem__("outcome", "MET"), False)
    probe("D02-13", "Explicit denominator extension needs a definition.", "approximation_specification",
          lambda r: r["payload"]["error"].__setitem__("zero_denominator_policy", "EXPLICIT_EXTENSION"), False)
    probe("D02-14", "A provided extension definition is structurally accepted.", "approximation_specification",
          lambda r: r["payload"]["error"].update(
              zero_denominator_policy="EXPLICIT_EXTENSION",
              extension_definition=t("At theta=0 define the ratio as its continuous extension, zero."),
          ), True, "No limit or extension proof is executed by JSON Schema.")
    probe("D02-15", "A present zero tolerance is not missing data.", "approximation_specification",
          lambda r: r["payload"]["criterion"].__setitem__("threshold", p), True)
    probe("D02-16", "In-scope status without an assessment reference is rejected.", "anchor_application",
          set_payload("applicability_status", "IN_SCOPE_FOR_STATED_CHECK"), False)
    probe("D02-17", "Unknown applicability blocks a positive law-comparison verdict.", "anchor_application",
          lambda r: r["payload"].update(
              comparison_status="CONSISTENT_WITH_STATED_CRITERIA",
              comparison_assessment_refs=[fake_assessment],
          ), False)
    probe("D02-18", "Out-of-scope status blocks a definitive law-discrepancy verdict.", "anchor_application",
          lambda r: r["payload"].update(
              applicability_status="OUTSIDE_DECLARED_SCOPE",
              applicability_assessment_refs=[fake_assessment],
              comparison_status="DISCREPANCY_RECORDED",
              comparison_assessment_refs=[fake_assessment],
          ), False)
    probe("D02-19", "A positive assertion with unresolved references can still satisfy shape.", "anchor_application",
          lambda r: r["payload"].update(
              applicability_status="IN_SCOPE_FOR_STATED_CHECK",
              applicability_assessment_refs=[fake_assessment],
              comparison_status="CONSISTENT_WITH_STATED_CRITERIA",
              comparison_assessment_refs=[fake_assessment],
          ), True,
          "Referenced evidence existence, relevance, condition coverage, and outcomes require a semantic resolver.")
    probe("D02-20", "Omitting a condition check is not detected by record shape.", "anchor_application",
          lambda r: r["payload"]["condition_checks"].pop(), True,
          "A future resolver must compare condition IDs against the exact referenced anchor version.")
    probe("D02-21", "Missing sources do not make a reference statement unrecordable.", "physics_anchor",
          lambda r: (r.__setitem__("source_refs", []), r["payload"].__setitem__("source_citations", [])), True,
          "An anchor without sources must remain source-missing, not established by its name.")
    probe("D02-22", "A complete-inventory declaration is not validated by shape.", "balance_specification",
          set_payload("term_inventory_status", "DECLARED_COMPLETE"), True,
          "Physical completeness and missing included-term values remain unverified.")
    probe("D02-23", "Typed anchor reference rejects an observation type.", "balance_specification",
          lambda r: r["payload"]["anchor"].__setitem__("expected_type", "observation"), False)
    probe("D02-24", "Missing producer is rejected.", "calculation",
          lambda r: r.pop("producer"), False)
    probe("D02-25", "Quantity-kind omission is explicit, not silently inferred.", "quantity_definition",
          set_payload("quantity_kind", absent), True)

    def uncertainty(record, value):
        record["payload"]["uncertainty"] = {
            "status": "PRESENT", "kind": "STANDARD_UNCERTAINTY",
            "description": "Synthetic structural probe only.",
            "value": {"status": "PRESENT", "value": value, "encoding": "json_number"},
            "quantity_definition": record["payload"]["result_quantity"],
            "coverage": absent, "covariance_refs": [], "dependence_assumptions": [],
            "assessment_refs": [],
        }
    probe("D02-26", "Negative standard uncertainty is rejected.", "calculation",
          lambda r: uncertainty(r, -1), False)
    probe("D02-27", "Zero standard uncertainty is representable, not permission to divide by zero.", "calculation",
          lambda r: uncertainty(r, 0), True)
    probe("D02-28", "Missingness cannot carry a hidden numerical zero.", "calculation",
          set_payload("result", {"status": "MISSING", "reason": "Missing.", "value": 0}), False)
    probe("D02-29", "Negative unit scale is rejected in this declared convention.", "quantity_definition",
          lambda r: r["payload"]["unit"].__setitem__(
              "scale_to_reference", {"status": "PRESENT", "value": -1, "encoding": "json_number"}
          ), False)
    probe("D02-30", "A recorded anchor version may remain unknown.", "anchor_application",
          set_payload("anchor_version", absent), True,
          "No version may be inferred or used to establish freshness from this missing state.")
    probe("D02-31", "Citation IDs are not resolved against source entries by shape.", "physics_anchor",
          lambda r: r["payload"]["conditions"][0].__setitem__("citation_ids", ["not-listed"]), True,
          "Cross-field citation integrity is a planned semantic check.")

    # Prove the configured registry refuses unregistered retrieval.
    remote_blocked = False
    try:
        registry.get_or_retrieve("https://example.invalid/unregistered-schema")
    except NoSuchResource:
        remote_blocked = True

    paths = [OLD, NEW, FIXTURES, OLD_FIXTURES, REQUIREMENTS, Path(__file__),
             Path(__file__).with_name("build_examples.py")]
    summary = {
        "all_record_shapes_accepted": all(r["schema_accepted"] for r in record_results),
        "all_probe_expectations_matched": all(r["expectation_matched"] for r in probes),
        "new_bundle_record_count": len(records),
        "original_bundle_record_count": len(original_records),
        "probe_count": len(probes),
        "network_retrieval_disabled": remote_blocked,
    }
    output = {
        "artifact_kind": "AUTHORING_STRUCTURAL_SCHEMA_REVIEW",
        "scope": "Record shapes and declared structural boundaries only; NOT lab acceptance tests.",
        "reviewer": {
            "python": platform.python_version(),
            "jsonschema": importlib.metadata.version("jsonschema"),
            "referencing": importlib.metadata.version("referencing"),
            "rfc3339-validator": importlib.metadata.version("rfc3339-validator"),
            "date_time_format_support_confirmed": True,
        },
        "examined_sha256": {
            str(p.relative_to(LAB)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        "summary": summary, "record_results": record_results, "probes": probes,
        "limitations": [
            "Authoring schemas, fixtures, procedures, and interpretation share an author.",
            "No reference graph, source authenticity, law applicability, equation semantics, or physical adequacy was validated.",
            "Positive authoring results do not change prototype compatibility UNKNOWN or voice DEFERRED.",
        ],
    }
    print(json.dumps(output, indent=2, allow_nan=False))
    return summary


if __name__ == "__main__":
    result = review()
    if not all((result["all_record_shapes_accepted"],
                result["all_probe_expectations_matched"],
                result["network_retrieval_disabled"])):
        raise SystemExit(1)
