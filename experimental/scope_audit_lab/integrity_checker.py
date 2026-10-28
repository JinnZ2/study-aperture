#!/usr/bin/env python3
"""Read-only offline evidence-integrity checker, Python standard library only.

Resolves IDs/declared types, exact declared version bindings, and anchor-condition
coverage. Does not validate JSON Schema or establish mathematical/physical truth.
No network, subprocess, imports from submitted content, or automatic mutation.
"""

import argparse
import hashlib
import html
import json
import sys
from collections import Counter
from pathlib import Path


VERSION = "0.1.0"
CONTRACTS = {
    ("urn:scope-audit-lab:schema:math-evidence:0.1", "0.1"):
        {"equation", "assumption", "derivation", "observation", "assessment"},
    ("urn:scope-audit-lab:schema:math-physics-extensions:0.2", "0.2"):
        {"quantity_definition", "calculation", "balance_specification",
         "approximation_specification", "physics_anchor", "anchor_application"},
}
OUTCOMES = {"MET", "NOT_MET", "INDETERMINATE", "NOT_EVALUATED"}
MAX_BYTES = 16 * 1024 * 1024


def text(value):
    return isinstance(value, str) and bool(value.strip())


def pointer(path, key):
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def walk(value, path=""):
    """Iterative traversal. A reference-looking object is not trusted as valid."""
    stack = [(path, value)]
    while stack:
        path, value = stack.pop()
        yield path, value
        if isinstance(value, dict):
            stack.extend((pointer(path, k), v) for k, v in reversed(list(value.items())))
        elif isinstance(value, list):
            stack.extend((pointer(path, i), v) for i, v in reversed(list(enumerate(value))))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def declared_version(value):
    if not isinstance(value, dict):
        return None, "MISSING" if value is None else "MALFORMED"
    status = value.get("status")
    if status == "PRESENT" and text(value.get("value")):
        return value["value"], "PRESENT"
    if isinstance(status, str) and status in {"MISSING", "INVALID", "NOT_APPLICABLE"} and "value" not in value:
        return None, status
    return None, "MALFORMED"


class Checker:
    def __init__(self, documents):
        self.documents = documents
        self.entries = []
        self.index = {}
        self.findings = []
        self.references = []
        self.versions = []
        self.coverage = []

    def finding(self, severity, code, location, message, **details):
        self.findings.append({
            "severity": severity, "code": code, "location": location,
            "message": message, **details,
        })

    @staticmethod
    def location(entry, suffix=""):
        return {"input": entry["input"], "pointer": entry["path"] + suffix}

    def recognized(self, record):
        schema, version = record.get("schema_id"), record.get("schema_version")
        if not isinstance(schema, str) or not isinstance(version, str):
            return False
        kind = record.get("record_type")
        return isinstance(kind, str) and kind in CONTRACTS.get((schema, version), set())

    def build_index(self):
        for document in self.documents:
            for i, record in enumerate(document["records"]):
                entry = {
                    "input": document["name"], "path": pointer(document["base"], i),
                    "record": record,
                }
                self.entries.append(entry)
                loc = self.location(entry)
                if not isinstance(record, dict):
                    self.finding("ERROR", "RECORD_NOT_OBJECT", loc, "Record is not an object.")
                    continue
                identifier = record.get("record_id")
                kind = record.get("record_type")
                if not text(identifier) or not text(kind):
                    self.finding("ERROR", "RECORD_IDENTITY_MALFORMED", loc,
                                 "Nonblank record_id and record_type strings are required.")
                    continue
                if not self.recognized(record):
                    self.finding("UNKNOWN", "OPAQUE_CONTRACT", loc,
                                 "Unsupported contract/type; retained as opaque, not structurally validated.")
                entry["canonical"] = canonical(record)
                self.index.setdefault(identifier, []).append(entry)
        for identifier, entries in self.index.items():
            contents = {e["canonical"] for e in entries}
            if len(contents) > 1:
                self.finding("ERROR", "DUPLICATE_ID_CONFLICT", self.location(entries[0]),
                             "Conflicting records share an ID; no version or latest record is selected.",
                             record_id=identifier,
                             occurrences=[self.location(e) for e in entries])
            elif len(entries) > 1:
                self.finding("INFO", "IDENTICAL_REIMPORT", self.location(entries[0]),
                             "Identical parsed records share an ID; all input occurrences are retained.",
                             record_id=identifier,
                             occurrences=[self.location(e) for e in entries])

    def resolve(self, reference):
        if not isinstance(reference, dict):
            return "MALFORMED", None
        status = reference.get("status")
        if (isinstance(status, str) and status in {"MISSING", "INVALID", "NOT_APPLICABLE"}
                and text(reference.get("reason")) and "value" not in reference
                and "record_id" not in reference and "expected_type" not in reference):
            return "ABSENT", None
        identifier, expected = reference.get("record_id"), reference.get("expected_type")
        if not text(identifier) or not text(expected):
            return "MALFORMED", None
        entries = self.index.get(identifier, [])
        if not entries:
            return "UNRESOLVED", None
        if len({e["canonical"] for e in entries}) != 1:
            return "AMBIGUOUS", None
        target = entries[0]
        if target["record"]["record_type"] != expected:
            return "TYPE_MISMATCH", target
        if not self.recognized(target["record"]):
            return "OPAQUE_TARGET", target
        return "RESOLVED", target

    def inspect_references(self):
        typed_fields = {
            "source_refs": "source", "source_record": "source",
            "artifact_refs": "artifact", "state_artifact_refs": "artifact",
            "examined_state_artifact_refs": "artifact",
            "assumption_refs": "assumption", "introduced_assumption_refs": "assumption",
            "assessment_refs": "assessment", "applicability_assessment_refs": "assessment",
            "comparison_assessment_refs": "assessment",
            "anchor": "physics_anchor", "quantity_definition": "quantity_definition",
            "result_quantity": "quantity_definition", "balanced_quantity": "quantity_definition",
        }
        singular = {"subject", "input", "anchor", "target", "source_record",
                    "quantity_definition", "result_quantity", "balanced_quantity"}
        for entry in self.entries:
            candidates = {}
            known = isinstance(entry["record"], dict) and self.recognized(entry["record"])
            for path, value in walk(entry["record"]):
                if not isinstance(value, dict):
                    continue
                if "expected_type" in value or ("record_id" in value and "resolution" in value):
                    candidates.setdefault(path, (value, None))
                if not known:
                    continue
                for field, item in value.items():
                    field_path = pointer(path, field)
                    if field.endswith("_refs") or field == "applies_to":
                        if not isinstance(item, list):
                            self.finding("ERROR", "REFERENCE_LIST_MALFORMED", self.location(entry, field_path),
                                         "A declared reference-list slot must contain an array.")
                        else:
                            for i, reference in enumerate(item):
                                candidates[pointer(field_path, i)] = (reference, typed_fields.get(field))
                    elif field in singular or field.endswith("_ref"):
                        if self.resolve(item)[0] != "ABSENT":
                            candidates[field_path] = (item, typed_fields.get(field))
            for path, (value, context_type) in candidates.items():
                status, target = self.resolve(value)
                loc = self.location(entry, path)
                self.references.append({
                    "location": loc, "reference": value, "snapshot_resolution": status,
                    "context_expected_type": context_type,
                    "target_location": self.location(target) if target else None,
                })
                if (context_type and isinstance(value, dict) and
                        value.get("expected_type") != context_type):
                    self.finding("ERROR", "REFERENCE_CONTEXT_TYPE_MISMATCH", loc,
                                 "The recorded expected type conflicts with this supported reference slot.",
                                 context_expected_type=context_type)
                if status != "RESOLVED":
                    severity = "UNKNOWN" if status in {"UNRESOLVED", "OPAQUE_TARGET"} else "ERROR"
                    self.finding(severity, "REFERENCE_" + status, loc,
                                 "Snapshot identity/type resolution is " + status + "; content truth is not evaluated.")
                declaration = value.get("resolution") if isinstance(value, dict) else None
                if not isinstance(declaration, str) or declaration not in {"RESOLVED", "UNRESOLVED", "TYPE_MISMATCH", "NOT_CHECKED"}:
                    self.finding("ERROR", "REFERENCE_DECLARATION_MALFORMED", loc,
                                 "Recorded resolution must use the draft reference vocabulary.")
                elif declaration not in {"NOT_CHECKED", status}:
                    self.finding("INFO", "REFERENCE_DECLARATION_DIFFERS", loc,
                                 "Recorded resolution differs from this supplied snapshot; historical truth is not inferred.",
                                 declared_resolution=declaration, snapshot_resolution=status)

    def binding(self, entry, path, reference, examined):
        resolution, target = self.resolve(reference)
        expected, expected_status = declared_version(examined)
        actual, actual_status = declared_version(
            target["record"].get("record_version") if target else None
        )
        if resolution != "RESOLVED":
            status = "BLOCKED_REFERENCE"
        elif expected is None or actual is None:
            status = "VERSION_UNKNOWN"
        else:
            status = "SAME_DECLARED_VERSION" if expected == actual else "DIFFERENT_DECLARED_VERSION"
        row = {
            "location": self.location(entry, path),
            "reference": reference, "reference_resolution": resolution,
            "examined_version": examined, "examined_version_state": expected_status,
            "target_version": target["record"].get("record_version") if target else None,
            "target_version_state": actual_status, "binding_status": status,
            "content_state_equality_established": False,
        }
        self.versions.append(row)
        if "MALFORMED" in {expected_status, actual_status}:
            self.finding("ERROR", "VERSION_MALFORMED", row["location"],
                         "A version value does not use the declared text/missingness contract.")
        if status != "SAME_DECLARED_VERSION":
            self.finding("ERROR" if status == "DIFFERENT_DECLARED_VERSION" else "UNKNOWN",
                         "BINDING_" + status, row["location"],
                         "Exact declared-version binding is " + status +
                         "; chronology, relevance of changes, and physical validity are not inferred.")
        return row

    def inspect_bindings(self):
        for entry in self.entries:
            record = entry["record"]
            if "canonical" not in entry or not self.recognized(record):
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                self.finding("ERROR", "PAYLOAD_MALFORMED", self.location(entry),
                             "A payload object is required for the supported record.")
                continue
            kind = record["record_type"]
            fields = []
            if kind in {"assessment", "anchor_application"}:
                fields.append(("subjects", "subject"))
            if kind in {"calculation", "approximation_specification"}:
                fields.append(("inputs", "input"))
            for field, reference_key in fields:
                values = payload.get(field)
                if not isinstance(values, list):
                    self.finding("ERROR", "BINDING_LIST_MALFORMED", self.location(entry, "/payload/" + field),
                                 "Expected a binding list.")
                    continue
                if not values:
                    self.finding("ERROR", "BINDING_LIST_EMPTY", self.location(entry, "/payload/" + field),
                                 "At least one binding is required by this supported record type.")
                for i, value in enumerate(values):
                    path = "/payload/" + field + "/" + str(i)
                    if not isinstance(value, dict):
                        self.finding("ERROR", "BINDING_MALFORMED", self.location(entry, path),
                                     "A binding must be an object.")
                        continue
                    self.binding(entry, path, value.get(reference_key), value.get("examined_version"))

    def id_rows(self, rows, key, entry, path):
        if not isinstance(rows, list):
            self.finding("ERROR", "CONDITION_LIST_MALFORMED", self.location(entry, path),
                         "Expected a list of condition objects.")
            return {}, True
        grouped, malformed = {}, False
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or not text(row.get(key)):
                malformed = True
                self.finding("ERROR", "CONDITION_ID_MALFORMED", self.location(entry, pointer(path, i)),
                             "Expected an explicit nonblank " + key + ".")
                continue
            grouped.setdefault(row[key], []).append((i, row))
        for identifier, entries in grouped.items():
            if len(entries) != 1:
                malformed = True
                self.finding("ERROR", "DUPLICATE_CONDITION_ID", self.location(entry, path),
                             "Duplicate condition/check ID; no occurrence is selected.",
                             condition_id=identifier)
        return grouped, malformed

    def inspect_anchor(self, entry):
        payload = entry["record"].get("payload")
        if not isinstance(payload, dict):
            return
        conditions, bad = self.id_rows(payload.get("conditions"), "condition_id", entry, "/payload/conditions")
        if not conditions:
            self.finding("ERROR", "ANCHOR_CONDITIONS_EMPTY", self.location(entry),
                         "An anchor must declare at least one condition.")
        citations = payload.get("source_citations")
        if not isinstance(citations, list):
            self.finding("ERROR", "CITATION_LIST_MALFORMED", self.location(entry),
                         "Expected a source_citations list; no locator is fetched.")
            return
        ids = [c.get("citation_id") for c in citations if isinstance(c, dict)]
        if len(ids) != len(citations) or any(not text(i) for i in ids):
            self.finding("ERROR", "CITATION_ID_MALFORMED", self.location(entry),
                         "Citation IDs must be explicit nonblank strings.")
        valid_ids = [i for i in ids if text(i)]
        if len(set(valid_ids)) != len(valid_ids):
            self.finding("ERROR", "DUPLICATE_CITATION_ID", self.location(entry),
                         "Citation IDs must be unique within an anchor.")
        if not citations:
            self.finding("UNKNOWN", "ANCHOR_SOURCES_MISSING", self.location(entry),
                         "No source citations supplied; the anchor name establishes no content.")
        for rows in conditions.values():
            for i, condition in rows:
                if not text(condition.get("exact_requirement")):
                    self.finding("ERROR", "ANCHOR_REQUIREMENT_MALFORMED",
                                 self.location(entry, "/payload/conditions/" + str(i)),
                                 "Anchor conditions need exact nonblank requirement text.")
                keys = condition.get("citation_ids")
                if not isinstance(keys, list) or any(not text(k) for k in keys):
                    self.finding("ERROR", "CONDITION_CITATIONS_MALFORMED", self.location(entry),
                                 "Condition citation_ids must be a list of strings.")
                else:
                    for key in keys:
                        if key not in valid_ids:
                            self.finding("ERROR", "CONDITION_CITATION_UNRESOLVED",
                                         self.location(entry, "/payload/conditions/" + str(i)),
                                         "Condition cites an absent source entry.", citation_id=key)

    def inspect_application(self, entry):
        payload = entry["record"].get("payload")
        if not isinstance(payload, dict):
            return
        bound = self.binding(entry, "/payload/anchor", payload.get("anchor"), payload.get("anchor_version"))
        resolution, anchor_entry = self.resolve(payload.get("anchor"))
        if (isinstance(payload.get("anchor"), dict) and
                payload["anchor"].get("expected_type") != "physics_anchor"):
            self.finding("ERROR", "ANCHOR_REFERENCE_TYPE_INVALID", self.location(entry, "/payload/anchor"),
                         "An anchor application must explicitly reference a physics_anchor.")
        row = {
            "location": self.location(entry), "record_id": entry["record"]["record_id"],
            "anchor_reference_resolution": resolution,
            "anchor_binding_status": bound["binding_status"],
            "identity_coverage": "UNAVAILABLE", "coverage_for_bound_version": "UNESTABLISHED",
            "missing_conditions": [], "extra_checks": [], "condition_checks": [],
            "recorded_applicability_status": payload.get("applicability_status"),
            "recorded_comparison_status": payload.get("comparison_status"),
            "condition_truth_established": False,
            "law_applicability_or_consistency_established": False,
        }
        self.coverage.append(row)
        if resolution != "RESOLVED" or anchor_entry["record"].get("record_type") != "physics_anchor":
            self.finding("UNKNOWN", "COVERAGE_BLOCKED_ANCHOR", self.location(entry),
                         "Condition coverage requires one unambiguous supported physics_anchor target.")
            return
        ap = anchor_entry["record"].get("payload")
        if not isinstance(ap, dict):
            self.finding("ERROR", "ANCHOR_PAYLOAD_MALFORMED", self.location(anchor_entry),
                         "Referenced anchor has no payload object.")
            return
        conditions, bad_anchor = self.id_rows(ap.get("conditions"), "condition_id",
                                              anchor_entry, "/payload/conditions")
        checks, bad_checks = self.id_rows(payload.get("condition_checks"), "requirement_id",
                                         entry, "/payload/condition_checks")
        missing = [key for key in conditions if key not in checks]
        extra = [key for key in checks if key not in conditions]
        row["missing_conditions"], row["extra_checks"] = missing, extra
        invalid = bad_anchor or bad_checks or not conditions
        for key in missing:
            self.finding("UNKNOWN", "ANCHOR_CONDITION_UNADDRESSED", self.location(entry),
                         "Anchor condition has no corresponding check.", condition_id=key)
        for key in extra:
            self.finding("ERROR", "ANCHOR_CHECK_NOT_IN_ANCHOR", self.location(entry),
                         "Application checks an ID not in the available anchor version.", condition_id=key)
        for key, definitions in conditions.items():
            if len(definitions) != 1 or len(checks.get(key, [])) != 1:
                continue
            _, definition = definitions[0]
            i, check = checks[key][0]
            loc = self.location(entry, "/payload/condition_checks/" + str(i))
            outcome = check.get("outcome")
            same_text = text(definition.get("exact_requirement")) and (
                definition["exact_requirement"] == check.get("exact_requirement")
            )
            evidence = check.get("evidence_refs")
            evidence_statuses = (
                [self.resolve(r)[0] for r in evidence] if isinstance(evidence, list) else []
            )
            row["condition_checks"].append({
                "condition_id": key, "recorded_outcome": outcome,
                "exact_requirement_text_matches": same_text,
                "evidence_reference_resolutions": evidence_statuses,
                "outcome_truth_established": False,
            })
            if not same_text:
                invalid = True
                self.finding("ERROR", "CONDITION_TEXT_MISMATCH", loc,
                             "Check does not preserve the exact anchor requirement text.", condition_id=key)
            if not isinstance(outcome, str) or outcome not in OUTCOMES:
                invalid = True
                self.finding("ERROR", "CONDITION_OUTCOME_MALFORMED", loc,
                             "Outcome must use the four-state criterion vocabulary.")
            elif outcome in {"INDETERMINATE", "NOT_EVALUATED"}:
                self.finding("UNKNOWN", "CONDITION_" + outcome, loc,
                             "Recorded condition outcome remains " + outcome + ".", condition_id=key)
            elif outcome == "NOT_MET":
                self.finding("INFO", "CONDITION_DECLARED_NOT_MET", loc,
                             "Criterion failure is retained; it does not make the observation false.")
            if not isinstance(evidence, list):
                invalid = True
                self.finding("ERROR", "CONDITION_EVIDENCE_MALFORMED", loc,
                             "Expected evidence_refs list.")
            elif isinstance(outcome, str) and outcome in {"MET", "NOT_MET"} and not evidence:
                invalid = True
                self.finding("ERROR", "CONDITION_EVIDENCE_MISSING", loc,
                             "Definitive recorded condition outcome has no evidence reference.")
        row["identity_coverage"] = (
            "INVALID" if invalid else "GAPS" if missing or extra else "COMPLETE"
        )
        if bound["binding_status"] == "SAME_DECLARED_VERSION":
            row["coverage_for_bound_version"] = row["identity_coverage"]
        unaddressed = payload.get("unaddressed_conditions")
        if not isinstance(unaddressed, list) or any(not text(x) for x in unaddressed):
            self.finding("ERROR", "UNADDRESSED_DECLARATION_MALFORMED", self.location(entry),
                         "Expected a list of explicit unresolved-condition notes.")
        elif unaddressed:
            self.finding("UNKNOWN", "DECLARED_UNADDRESSED_CONDITIONS", self.location(entry),
                         "Unaddressed-condition notes retained; they do not replace coverage checks.",
                         notes=unaddressed)
        applicability = payload.get("applicability_status")
        comparison = payload.get("comparison_status")
        vocabularies = (
            ("applicability_status", {"IN_SCOPE_FOR_STATED_CHECK", "OUTSIDE_DECLARED_SCOPE", "UNKNOWN", "NOT_EVALUATED"}),
            ("comparison_status", {"CONSISTENT_WITH_STATED_CRITERIA", "DISCREPANCY_RECORDED", "INDETERMINATE", "NOT_EVALUATED"}),
        )
        for field, vocabulary in vocabularies:
            value = payload.get(field)
            if not isinstance(value, str) or value not in vocabulary:
                self.finding("ERROR", "APPLICATION_STATUS_MALFORMED", self.location(entry),
                             "Recorded status is outside the supported draft vocabulary.", field=field)
        for field, definitive in (
            ("applicability_status", {"IN_SCOPE_FOR_STATED_CHECK", "OUTSIDE_DECLARED_SCOPE"}),
            ("comparison_status", {"CONSISTENT_WITH_STATED_CRITERIA", "DISCREPANCY_RECORDED"}),
        ):
            references = payload.get(
                "applicability_assessment_refs" if field == "applicability_status" else "comparison_assessment_refs"
            )
            value = payload.get(field)
            if isinstance(value, str) and value in definitive and (not isinstance(references, list) or not references):
                self.finding("ERROR", "DEFINITIVE_STATUS_WITHOUT_ASSESSMENT", self.location(entry),
                             "A definitive recorded status lacks assessment references.", field=field)
        definitive_comparison = isinstance(comparison, str) and comparison in {"CONSISTENT_WITH_STATED_CRITERIA", "DISCREPANCY_RECORDED"}
        if definitive_comparison and applicability != "IN_SCOPE_FOR_STATED_CHECK":
            self.finding("ERROR", "COMPARISON_APPLICABILITY_CONFLICT", self.location(entry),
                         "Definitive law comparison is asserted without recorded in-scope applicability.")
        if applicability == "IN_SCOPE_FOR_STATED_CHECK" or definitive_comparison:
            unique_checks = [items[0][1] for items in checks.values() if len(items) == 1]
            if any(check.get("outcome") == "NOT_MET" for check in unique_checks):
                self.finding("ERROR", "APPLICABILITY_CONDITION_CONFLICT", self.location(entry),
                             "Positive applicability/comparison conflicts with a recorded unmet condition.")
            unresolved_evidence = any(
                status != "RESOLVED" for check in row["condition_checks"]
                for status in check["evidence_reference_resolutions"]
            )
            if (row["coverage_for_bound_version"] != "COMPLETE" or unaddressed or unresolved_evidence or
                    any(check.get("outcome") != "MET" for check in unique_checks)):
                self.finding("UNKNOWN", "POSITIVE_STATUS_NOT_ESTABLISHED", self.location(entry),
                             "Recorded positive status has incomplete/version-unbound/unevaluated conditions; no promotion occurs.")

    def run(self):
        self.build_index()
        if not self.entries:
            self.finding("UNKNOWN", "EMPTY_SNAPSHOT", {"input": "<snapshot>", "pointer": ""},
                         "No records supplied; evidence completeness is not inferred.")
        self.inspect_references()
        self.inspect_bindings()
        for entry in self.entries:
            record = entry["record"]
            if "canonical" not in entry or not self.recognized(record):
                continue
            if record["record_type"] == "physics_anchor":
                self.inspect_anchor(entry)
            elif record["record_type"] == "anchor_application":
                self.inspect_application(entry)
        counts = Counter(f["severity"] for f in self.findings)
        gaps = bool(counts["ERROR"] or counts["UNKNOWN"])
        return {
            "report_kind": "OFFLINE_EVIDENCE_INTEGRITY",
            "procedure": {"identity": "scope_audit_lab.integrity_checker", "version": VERSION},
            "inputs": [
                {k: v for k, v in d.items() if k in {"name", "sha256", "byte_count"}}
                for d in self.documents
            ],
            "summary": {
                "status": "INTEGRITY_GAPS_RECORDED" if gaps else "NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE",
                "record_occurrences": len(self.entries), "unique_record_ids": len(self.index),
                "reference_count": len(self.references), "version_binding_count": len(self.versions),
                "anchor_application_count": len(self.coverage),
                "finding_counts": {k: counts[k] for k in ("ERROR", "UNKNOWN", "INFO")},
            },
            "structural_schema_validation": "NOT_PERFORMED",
            "mathematical_or_empirical_validation": "NOT_PERFORMED",
            "prototype_0_1_compatibility": "UNKNOWN", "voice": "DEFERRED",
            "reference_resolution": self.references, "version_bindings": self.versions,
            "anchor_condition_coverage": self.coverage, "findings": self.findings,
            "limits": [
                "Resolution establishes only supplied-snapshot identity and declared type, not authenticated content.",
                "Same declared version does not prove equal content, complete dependencies, or empirical freshness.",
                "Condition coverage and recorded outcomes do not establish physical applicability or evidence relevance.",
                "No URLs/artifact paths are opened, no submitted code is executed, and inputs are not modified.",
                "Unsupported contracts remain opaque. Missing targets do not establish falsehood.",
                "No full JSON Schema validation, temporal ordering, proof checking, or scientific verdict.",
            ],
        }


def check_records(records):
    """In-memory API for locally supplied records, not authenticated ingestion."""
    return Checker([{"name": "<memory>", "base": "", "records": records}]).run()


def load_document(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Input exceeds the 16 MiB per-file limit: " + str(path))

    def no_duplicates(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("Duplicate JSON member: " + key)
            obj[key] = value
        return obj

    def no_nonfinite(value):
        raise ValueError("Non-finite JSON constant: " + value)

    def finite_float(value):
        import math
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("Out-of-range JSON number: " + value)
        return result

    document = json.loads(raw, object_pairs_hook=no_duplicates,
                          parse_constant=no_nonfinite, parse_float=finite_float)
    if isinstance(document, list):
        records, base = document, ""
    elif isinstance(document, dict) and isinstance(document.get("records"), list):
        records, base = document["records"], "/records"
    else:
        raise ValueError("Expected a record array or an object containing a records array: " + str(path))
    return {
        "name": str(path), "base": base, "records": records,
        "sha256": hashlib.sha256(raw).hexdigest(), "byte_count": len(raw),
    }


def markdown(report):
    def safe(value):
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=True)
        return html.escape(value).replace("|", "\\|").replace("\n", "\\n").replace("\r", "\\r")
    summary = report["summary"]
    lines = [
        "# Offline evidence-integrity report", "",
        "Status: " + summary["status"] + ". This is not mathematical or empirical validation.",
        "Structural JSON Schema validation was not performed; all condition outcomes remain recorded assertions.", "",
        "## Snapshot", "",
        "| Input | SHA-256 |", "|---|---|",
    ]
    lines.extend("| " + safe(i["name"]) + " | " +
                 i.get("sha256", "NOT_CAPTURED: in-memory records") + " |"
                 for i in report["inputs"])
    lines.extend([
        "", "## Reference resolution", "",
        "| Reference | Expected type | Snapshot result | Location |", "|---|---|---|---|",
    ])
    lines.extend(
        "| " + safe(r["reference"].get("record_id") if isinstance(r["reference"], dict) else r["reference"]) + " | " +
        safe(r["reference"].get("expected_type") if isinstance(r["reference"], dict) else None) + " | " + r["snapshot_resolution"] +
        " | " + safe(r["location"]) + " |" for r in report["reference_resolution"]
    )
    lines.extend([
        "", "## Anchor-condition coverage", "",
        "| Application | Available-condition identity coverage | Coverage for bound version |",
        "|---|---|---|",
    ])
    lines.extend("| " + safe(c["record_id"]) + " | " + c["identity_coverage"] +
                 " | " + c["coverage_for_bound_version"] + " |"
                 for c in report["anchor_condition_coverage"])
    lines.extend([
        "", "Complete coverage means every condition has one matching check, not that the conditions are met.",
        "", "### Recorded condition outcomes", "",
        "| Application / condition | Recorded outcome | Evidence-link resolutions |",
        "|---|---|---|",
    ])
    lines.extend(
        "| " + safe(c["record_id"] + " / " + k["condition_id"]) + " | " +
        safe(k["recorded_outcome"]) + " | " + safe(k["evidence_reference_resolutions"]) + " |"
        for c in report["anchor_condition_coverage"] for k in c["condition_checks"]
    )
    lines.extend([
        "", "## Version bindings", "",
        "| Location | Examined version | Target version | Binding |", "|---|---|---|---|",
    ])
    lines.extend("| " + safe(v["location"]) + " | " + safe(v["examined_version"]) +
                 " | " + safe(v["target_version"]) + " | " + v["binding_status"] + " |"
                 for v in report["version_bindings"])
    lines.extend(["", "## Integrity findings", ""])
    if not report["findings"]:
        lines.append("No gaps detected within checked scope; no scientific conclusion follows.")
    for finding in report["findings"]:
        details = {k: v for k, v in finding.items()
                   if k not in {"severity", "code", "location", "message"}}
        lines.append("- **" + finding["severity"] + " / " + finding["code"] + "**: " +
                     safe(finding["location"]) + ": " + safe(finding["message"]) +
                     (" " + safe(details) if details else ""))
    lines.extend(["", "## Verification limits", ""])
    lines.extend("- " + item for item in report["limits"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", nargs="+", help="Local JSON bundles; all form one explicit snapshot.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", help="New output file only; an existing file is never overwritten.")
    args = parser.parse_args(argv)
    try:
        documents = [load_document(path) for path in args.bundles]
        report = Checker(documents).run()
        output = (json.dumps(report, indent=2, allow_nan=False) + "\n"
                  if args.format == "json" else markdown(report))
        if args.output:
            with Path(args.output).open("x", encoding="utf-8") as stream:
                stream.write(output)
        else:
            sys.stdout.write(output)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        print(json.dumps({"status": "INPUT_OR_OUTPUT_REJECTED", "error": str(exc)}), file=sys.stderr)
        return 2
    return 0 if report["summary"]["status"] == "NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
