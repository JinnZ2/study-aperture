"""Isolated, stdlib-only exact comparisons; agreement is not correctness.

No source, model, network, or production validator is invoked. Inputs are JSON
objects already captured by the harness. Missing fields are distinct from null.
All pair denominators include excluded pairs. CC0-1.0.
"""
from __future__ import annotations

import html
import itertools
import json
import re
from collections import Counter
from typing import Any

DEFAULT_FIELDS = ["assessment.claims", "assessment.decisions", "evidence", "findings"]
OUTCOMES = ("PASS", "FAIL", "UNSCORABLE", "NOT_ASSESSED")
_MISSING = object()
_HASH = re.compile(r"^[0-9a-fA-F]{64}$")
_UNKNOWN = {"UNDECLARED", "UNKNOWN", "UNKNOWN_ORIGIN", "NODATA", "NOTFOUND", "UNAVAILABLE"}
_EQUIVALENCE_FIELDS = (
    "model.name", "model.version", "environment", "prompt_sha256",
    "instructions_sha256", "source_package_sha256", "freeze_sha256",
    "tools", "retrieved_material", "supplied_material", "execution.retries",
    "assessor_prior",
)
LIMITATIONS = [
    "Exact field agreement is consistency, not correctness, truth, independence, or general reliability.",
    "Object key order is ignored; array order, types, text, and explicit null are preserved. No semantic equivalence is inferred.",
    "An absent selected field is UNSCORABLE, even if absent in both inputs; unknown sentinel values and null remain literal observations.",
    "Provenance equivalence checks recorded declarations, not actual model identity, hidden exposure, training origin, or reproducibility.",
    "Pairwise counts share records and are not independent trials. No aggregate reliability score, chance correction, or confidence interval is computed.",
    "Schema and invariant flags are capture metadata, not independently revalidated here; incompleteness is preserved separately from invalidity.",
    "No evidence fidelity, interpretive fidelity, appropriate uncertainty, or correctness of a transformation is established by these comparisons.",
]


def _json(value: Any) -> str:
    """Type-sensitive canonical JSON; reject non-JSON data and nonfinite floats."""
    def check(item: Any) -> None:
        if item is None or type(item) in (str, bool, int, float):
            return
        if type(item) is list:
            for child in item:
                check(child)
            return
        if type(item) is dict and all(type(key) is str for key in item):
            for child in item.values():
                check(child)
            return
        raise ValueError("input is not a plain JSON value")
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _value(obj: Any, field: str) -> Any:
    for part in field.split("."):
        if isinstance(obj, dict) and part in obj:
            obj = obj[part]
        else:
            return _MISSING
    return obj


def _shown(value: Any) -> Any:
    return {"$missing": True} if value is _MISSING else value


def _declaration(obj: Any, field: str) -> dict:
    value = _value(obj, field)
    if value is _MISSING:
        return {"present": False, "json_valid": True, "value": _shown(value)}
    try:
        _json(value)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return {"present": True, "json_valid": False, "value": None,
                "reason": "Invalid JSON declaration retained in original input, not printable as JSON."}
    return {"present": True, "json_valid": True, "value": value}


def _equal(left: Any, right: Any) -> bool:
    if left is _MISSING or right is _MISSING:
        return left is right
    return _json(left) == _json(right)


def _fields(fields: list | None, default: list | None = None) -> list[str]:
    values = list(default or []) if fields is None else fields
    if not isinstance(values, list):
        raise ValueError("fields must be a list of dotted paths")
    result = []
    for field in values:
        if not isinstance(field, str) or not field or any(
                not part or "*" in part for part in field.split(".")):
            raise ValueError("field paths must be nonempty dotted object keys; wildcards are not supported")
        if field not in result:
            result.append(field)
    return result


def _counts(outcomes: list[str]) -> dict:
    counts = {state: outcomes.count(state) for state in OUTCOMES}
    return {**counts, "denominator": len(outcomes),
            "scorable_denominator": counts["PASS"] + counts["FAIL"]}


def _capture_errors(capture: Any) -> list[str]:
    if not isinstance(capture, dict):
        return ["capture is not an object"]
    try:
        _json(capture)
    except (ValueError, TypeError, OverflowError, RecursionError) as exc:
        return ["capture contains invalid JSON values: " + str(exc)]
    errors = []
    if capture.get("schema") != "assessor-reliability/capture/1":
        errors.append("capture schema is absent or unsupported")
    for key in ("run_id", "case_id", "variant_id"):
        if not isinstance(capture.get(key), str) or not capture[key].strip():
            errors.append(key + " is absent or invalid")
    if not isinstance(capture.get("raw_sha256"), str) or not _HASH.fullmatch(capture["raw_sha256"]):
        errors.append("raw_sha256 is absent or invalid")
    if not isinstance(capture.get("parsed"), dict):
        errors.append("parsed output is unavailable or not an object")
    parse_errors = capture.get("parse_errors")
    if not isinstance(parse_errors, list) or parse_errors:
        errors.append("parse_errors are present or not declared as an empty list")
    validation = capture.get("validation")
    if not isinstance(validation, dict):
        errors.append("validation is absent or invalid")
    else:
        if validation.get("schema_valid") is not True:
            errors.append("capture schema validation did not pass")
        for key in ("invariant_violations", "missing_fields"):
            if not isinstance(validation.get(key), list) or validation[key]:
                errors.append("validation." + key + " are present or unavailable")
        if not isinstance(validation.get("incompleteness"), list):
            errors.append("validation.incompleteness is unavailable")
    provenance = capture.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance is absent or invalid")
        return errors
    for field in _EQUIVALENCE_FIELDS:
        value = _value(provenance, field)
        if value is _MISSING or value is None:
            errors.append("provenance." + field + " is absent or null")
            continue
        if field.endswith("sha256"):
            valid = isinstance(value, str) and bool(_HASH.fullmatch(value))
        elif field in ("model.name", "model.version"):
            valid = isinstance(value, str) and bool(value.strip())
        elif field == "environment":
            valid = isinstance(value, dict)
        elif field in ("tools", "supplied_material", "retrieved_material"):
            valid = isinstance(value, list)
            if valid and field == "tools":
                valid = all(isinstance(item, str) and bool(item.strip()) for item in value)
            elif valid:
                valid = all(isinstance(item, dict) for item in value)
        elif field == "execution.retries":
            valid = type(value) is int and value >= 0
        else:
            valid = isinstance(value, str) and bool(value.strip())
        if not valid:
            errors.append("provenance." + field + " is invalid or undeclared")
    execution = provenance.get("execution")
    if not isinstance(execution, dict):
        errors.append("execution metadata is unavailable")
    else:
        if not isinstance(execution.get("errors"), list) or execution["errors"]:
            errors.append("execution errors are present or unavailable")
        for key in ("truncated", "incomplete"):
            if execution.get(key) is not False:
                errors.append("execution." + key + " is true or unavailable")
    return errors


def _is_capture(record: Any) -> bool:
    return isinstance(record, dict) and (
        str(record.get("schema", "")).startswith("assessor-reliability/capture/")
        or {"parsed", "validation", "provenance"}.issubset(record))


def _equivalence(left: dict, right: dict, perturbation: bool = False) -> dict:
    rows = []
    fields = list(_EQUIVALENCE_FIELDS)
    if not perturbation:
        fields = ["case_id", "variant_id"] + ["provenance." + key for key in fields]
    else:
        fields = ["provenance." + key for key in fields
                  if key not in ("source_package_sha256", "supplied_material", "prompt_sha256")]
    for field in fields:
        a, b = _value(left, field), _value(right, field)
        outcome = "UNSCORABLE" if a is _MISSING or b is _MISSING or a is None or b is None else (
            "PASS" if _equal(a, b) else "FAIL")
        rows.append({"field": field, "outcome": outcome, "left": _shown(a), "right": _shown(b),
                     "left_present": a is not _MISSING, "right_present": b is not _MISSING})
    unknown_metadata = []
    for side, capture in (("left", left), ("right", right)):
        for field in ("provenance.model.name", "provenance.model.version", "provenance.environment"):
            value = _value(capture, field)
            if value == {} or (isinstance(value, str) and value.upper() in _UNKNOWN):
                unknown_metadata.append({"side": side, "field": field, "value": _shown(value)})
    permitted = []
    if perturbation:
        for field in ("provenance.source_package_sha256", "provenance.prompt_sha256", "provenance.supplied_material"):
            a, b = _value(left, field), _value(right, field)
            permitted.append({"field": field, "left": _shown(a), "right": _shown(b),
                              "changed": not _equal(a, b), "outcome": "NOT_ASSESSED",
                              "reason": "Permitted source/payload declaration difference; source change is separately checked."})
    return {"equivalent": all(row["outcome"] == "PASS" for row in rows),
            "checks": rows, "counts": _counts([row["outcome"] for row in rows]),
            "basis": "EXACT_RECORDED_DECLARATIONS_ONLY", "unknown_metadata": unknown_metadata,
            "permitted_differences": permitted,
            "limitation": "Matching UNDECLARED model metadata or an empty environment establishes only matching declarations, not actual equivalent conditions; no provider/runtime attestation is performed."}


def _observation(record: Any, field: str) -> Any:
    if isinstance(record, dict):
        return _value(record, field)
    return _MISSING


def _field_pair(a: Any, b: Any, eligible: bool, reasons: list[str]) -> dict:
    missing = {"left": a is _MISSING, "right": b is _MISSING}
    exact_equal = _equal(a, b) if eligible else None
    if not eligible:
        outcome = "UNSCORABLE"
    elif any(missing.values()):
        outcome = "UNSCORABLE"
        reasons = reasons + ["selected field is absent in at least one observation"]
    else:
        outcome = "PASS" if exact_equal else "FAIL"
    return {"outcome": outcome, "exact_equal": exact_equal,
            "left": _shown(a), "right": _shown(b), "missing": missing,
            "reasons": reasons}


def _pairwise(records: list, fields: list[str], material_fields: list[str], kind: str) -> dict:
    if not isinstance(records, list):
        raise ValueError("records must be a list")
    inputs, objects = [], []
    seen = Counter(record.get("run_id") for record in records
                   if isinstance(record, dict) and isinstance(record.get("run_id"), str)
                   and (kind == "repeats" or _is_capture(record)))
    for index, record in enumerate(records):
        capture = kind == "repeats" or _is_capture(record)
        errors = _capture_errors(record) if capture else []
        if not capture:
            try:
                if not isinstance(record, dict):
                    raise ValueError("record is not an object")
                _json(record)
            except (ValueError, TypeError, OverflowError, RecursionError) as exc:
                errors.append(str(exc))
        if capture and isinstance(record, dict) and isinstance(record.get("run_id"), str) and seen.get(record["run_id"], 0) > 1:
            errors.append("duplicate run_id: separate executions are not established")
        eligible = not errors
        parsed = record.get("parsed") if capture and isinstance(record, dict) else record
        objects.append(parsed if eligible else None)
        incompleteness = _value(record, "validation.incompleteness") if capture else _MISSING
        if incompleteness is not _MISSING:
            try:
                _json(incompleteness)
            except (ValueError, TypeError, OverflowError, RecursionError):
                incompleteness = _MISSING
        inputs.append({"index": index,
                       "run_id": record.get("run_id") if isinstance(record, dict) and isinstance(record.get("run_id"), str) else None,
                       "is_capture": capture, "eligible": eligible, "reasons": errors,
                       "provenance_declaration": _declaration(record, "provenance") if capture else None,
                       "incompleteness": _shown(incompleteness)})
    pairs = []
    for i, j in itertools.combinations(range(len(records)), 2):
        reasons = ["left: " + error for error in inputs[i]["reasons"]]
        reasons += ["right: " + error for error in inputs[j]["reasons"]]
        eligible = inputs[i]["eligible"] and inputs[j]["eligible"]
        provenance = None
        if eligible and inputs[i]["is_capture"] and inputs[j]["is_capture"]:
            provenance = _equivalence(records[i], records[j])
            if not provenance["equivalent"]:
                eligible = False
                reasons += ["provenance or case mismatch: " + row["field"]
                            for row in provenance["checks"] if row["outcome"] != "PASS"]
        elif inputs[i]["is_capture"] != inputs[j]["is_capture"]:
            eligible = False
            reasons.append("mixed capture and plain-record units are not matched")
        pairs.append({"left_index": i, "right_index": j,
                      "left_run_id": inputs[i]["run_id"], "right_run_id": inputs[j]["run_id"],
                      "eligible": eligible, "reasons": reasons, "provenance": provenance,
                      "fields": {field: _field_pair(_observation(objects[i], field),
                                                    _observation(objects[j], field), eligible, reasons)
                                 for field in fields}})
    summaries = {}
    for field in fields:
        values = [_observation(obj, field) for obj, info in zip(objects, inputs) if info["eligible"]]
        present = [value for value in values if value is not _MISSING]
        classes = Counter(_json(value) for value in present)
        rows = [pair["fields"][field] for pair in pairs]
        counts = _counts([row["outcome"] for row in rows])
        summaries[field] = {
            "counts": counts, "exact_agreement_count": counts["PASS"],
            "exact_disagreement_count": counts["FAIL"],
            "declared_material": field in material_fields,
            "material_disagreement_count": counts["FAIL"] if field in material_fields else None,
            "observation_denominator": len(records),
            "eligible_observation_denominator": len(values),
            "present_observation_denominator": len(present),
            "missing_observations": sum(value is _MISSING for value in values),
            "null_observations": sum(value is None for value in present),
            "excluded_observations": sum(not info["eligible"] for info in inputs),
            "class_prevalence": [{"value": json.loads(value), "count": count,
                                  "denominator": len(records), "present_denominator": len(present)}
                                 for value, count in sorted(classes.items())],
        }
    return {"schema": "assessor-reliability/comparison/1", "kind": kind,
            "status": "MECHANICAL_COMPARISON_ONLY", "sample_size": len(records),
            "pair_denominator": len(pairs), "eligible_pair_count": sum(pair["eligible"] for pair in pairs),
            "fields": summaries, "material_fields": material_fields,
            "inputs": inputs, "pairs": pairs, "limitations": list(LIMITATIONS)}


def compare_repeats(captures: list, fields: list | None = None,
                    material_fields: list | None = None) -> dict:
    """Compare every unordered pair, gating on exact recorded provenance.

    Material disagreement means ONLY exact mismatch in a caller-declared
    material field. Missing selected fields do not count as disagreement.
    No material fields are assumed by default.
    """
    selected = _fields(fields, DEFAULT_FIELDS)
    material = _fields(material_fields)
    selected += [field for field in material if field not in selected]
    return _pairwise(captures, selected, material, "repeats")


def agreement(records: list, fields: list) -> dict:
    """Exact pairwise agreement of explicit same-unit records, not a truth test.

    Plain objects are compared directly, with no reviewer identity or provenance
    inferred. Capture objects are unwrapped, validated, and equivalence-gated as
    repeats. Different units/cases must be grouped by the caller before use.
    """
    report = _pairwise(records, _fields(fields), [], "agreement")
    report["limitations"].append(
        "Plain-record alignment, assessor/reviewer identity, access, and independence are caller declarations, not established here; do not pool different cases.")
    return report


def _overlap(a: str, b: str) -> bool:
    return a == b or a.startswith(b + ".") or b.startswith(a + ".")


def _covered(path: str, rules: list[str]) -> bool:
    return any(path == rule or path.startswith(rule + ".") for rule in rules)


def _changes(left: Any, right: Any, path: str = "") -> list[dict]:
    if _equal(left, right):
        return []
    if isinstance(left, dict) and isinstance(right, dict):
        result = []
        for key in sorted(set(left) | set(right)):
            location = path + "." + key if path else key
            result.extend(_changes(left.get(key, _MISSING), right.get(key, _MISSING), location))
        return result
    return [{"field": path, "left": _shown(left), "right": _shown(right),
             "left_present": left is not _MISSING, "right_present": right is not _MISSING}]


def compare_perturbation(base: dict, variant: dict, spec: dict) -> dict:
    """Apply a predeclared perturbation's exact field rules, not semantic checks.

    Source-package hash must differ and linkage/justification must be declared.
    This documents a declared source change, not independent verification of it.
    The full prompt includes case/source payload and may differ with the package;
    governing instructions and other conditioning/exposure declarations must
    match. Supplied material may differ; retrieved material/tools may not.
    """
    reasons = ["base: " + reason for reason in _capture_errors(base)]
    reasons += ["variant: " + reason for reason in _capture_errors(variant)]
    rules = {name: [] for name in ("may_change", "must_change", "invariant")}
    spec_errors = []
    if not isinstance(spec, dict):
        spec_errors.append("perturbation spec is not an object")
        spec = {}
    else:
        try:
            _json(spec)
        except (ValueError, TypeError, OverflowError, RecursionError) as exc:
            spec_errors.append("perturbation spec is not JSON: " + str(exc))
            spec = {}
    for name in rules:
        try:
            if not isinstance(spec.get(name), list):
                raise ValueError("rule list is absent or not a list")
            rules[name] = _fields(spec[name])
        except ValueError as exc:
            spec_errors.append(name + ": " + str(exc))
    for name in ("kind", "base_case_id", "base_variant_id"):
        if not isinstance(spec.get(name), str) or not spec[name].strip():
            spec_errors.append(name + " is absent or invalid")
    for name in ("unresolved_when", "justification", "limits"):
        values = spec.get(name)
        if not isinstance(values, list) or not all(isinstance(value, str) and value.strip() for value in values):
            spec_errors.append(name + " must be a list of nonempty prose strings")
    if not spec.get("justification"):
        spec_errors.append("declared source change requires justification")
    for invariant in rules["invariant"]:
        if any(_overlap(invariant, field) for field in rules["may_change"] + rules["must_change"]):
            spec_errors.append("conflicting invariant and change rules: " + invariant)
    if isinstance(base, dict):
        for key in ("case_id", "variant_id"):
            if spec.get("base_" + key) != base.get(key):
                spec_errors.append("base_" + key + " does not match the capture")
    reasons += ["spec: " + error for error in spec_errors]
    provenance = None
    source_change = {"status": "UNSCORABLE", "base_sha256": None, "variant_sha256": None,
                     "basis": "DECLARED_PACKAGE_CHANGE_NOT_CONTENT_VERIFICATION"}
    if not _capture_errors(base) and not _capture_errors(variant):
        if base["run_id"] == variant["run_id"]:
            reasons.append("duplicate run_id: separate executions are not established")
        provenance = _equivalence(base, variant, perturbation=True)
        reasons += ["provenance mismatch: " + row["field"] for row in provenance["checks"]
                    if row["outcome"] != "PASS"]
        a = base["provenance"]["source_package_sha256"]
        b = variant["provenance"]["source_package_sha256"]
        source_change.update({"base_sha256": a, "variant_sha256": b,
                              "status": "DECLARED_CHANGE" if a != b and not spec_errors else "UNSCORABLE",
                              "supplied_material_changed": not _equal(base["provenance"]["supplied_material"],
                                                                       variant["provenance"]["supplied_material"])})
        if a == b:
            reasons.append("source package is unchanged; a controlled source perturbation is not established")
    eligible = not reasons
    selected = list(dict.fromkeys(DEFAULT_FIELDS + rules["may_change"] + rules["must_change"] + rules["invariant"]))
    left = base.get("parsed") if eligible else None
    right = variant.get("parsed") if eligible else None
    changes = _changes(left, right) if eligible else []
    allowed = rules["may_change"] + rules["must_change"]
    for change in changes:
        change["planned"] = _covered(change["field"], allowed)
        change["invariant_violation"] = _covered(change["field"], rules["invariant"])
        change["outcome"] = "NOT_ASSESSED" if change["planned"] else "FAIL"
        change["classification"] = "DECLARED_FIELD_CHANGE" if change["planned"] else (
            "INVARIANT_FIELD_CHANGE" if change["invariant_violation"] else "UNPLANNED_FIELD_CHANGE")
    fields_report = {}
    for field in selected:
        row = _field_pair(_observation(left, field), _observation(right, field), eligible, list(reasons))
        rule_outcomes = {}
        if row["outcome"] == "UNSCORABLE":
            for rule, values in rules.items():
                if field in values:
                    rule_outcomes[rule] = "UNSCORABLE"
        else:
            if field in rules["must_change"]:
                rule_outcomes["must_change"] = "FAIL" if row["exact_equal"] else "PASS"
            if field in rules["invariant"]:
                rule_outcomes["invariant"] = "PASS" if row["exact_equal"] else "FAIL"
            if field in rules["may_change"]:
                rule_outcomes["may_change"] = "NOT_ASSESSED"
        if not rule_outcomes:
            rule_outcomes["no_declared_rule"] = "UNSCORABLE" if row["outcome"] == "UNSCORABLE" else "NOT_ASSESSED"
        observations = [_observation(obj, field) for obj in (left, right)] if eligible else []
        present = [value for value in observations if value is not _MISSING]
        classes = Counter(_json(value) for value in present)
        fields_report[field] = {"comparison": row, "rule_outcomes": rule_outcomes,
                                "counts": _counts(list(rule_outcomes.values())),
                                "rule_denominator": len(rule_outcomes), "pair_denominator": 1,
                                "observation_denominator": 2,
                                "eligible_observation_denominator": len(observations),
                                "present_observation_denominator": len(present),
                                "missing_observations": sum(value is _MISSING for value in observations),
                                "null_observations": sum(value is None for value in present),
                                "excluded_observations": 0 if eligible else 2,
                                "class_prevalence": [{"value": json.loads(value), "count": count,
                                                      "denominator": 2, "present_denominator": len(present)}
                                                     for value, count in sorted(classes.items())]}
    unresolved = spec.get("unresolved_when", [])
    unresolved = unresolved if isinstance(unresolved, list) else []
    return {"schema": "assessor-reliability/comparison/1", "kind": "perturbation",
            "status": "MECHANICAL_COMPARISON_ONLY", "sample_size": 2, "pair_denominator": 1,
            "eligible_pair_count": int(eligible), "eligible": eligible, "reasons": reasons,
            "provenance_declarations": {"base": _declaration(base, "provenance"),
                                        "variant": _declaration(variant, "provenance")},
            "provenance": provenance, "source_change": source_change,
            "declared_rules": rules, "fields": fields_report, "changed_fields": changes,
            "unplanned_changes": [change for change in changes if not change["planned"]],
            "change_counts": _counts([change["outcome"] for change in changes]),
            "unresolved_conditions": [{"condition": condition, "outcome": "NOT_ASSESSED",
                                       "reason": "Prose expectations require explicit human evidence/interpretation review."}
                                      for condition in unresolved],
            "unresolved_counts": _counts(["NOT_ASSESSED"] * len(unresolved)),
            "justification": spec.get("justification", []), "declared_limits": spec.get("limits", []),
            "limitations": list(LIMITATIONS) + [
                "PASS/FAIL on perturbation rules refers only to exact change or invariance in declared fields, not the appropriateness or meaning of the response.",
                "Allowed change is not required change; prose unresolved conditions are NOT_ASSESSED. Any undeclared output change is flagged for review, not classified as a semantic failure.",
                "Changed paths recurse through object keys, treating arrays as ordered atomic values; dotted paths require object keys without dots and do not align evidence or claim identities.",
                "The source-package hashes and source-change justification are declarations. This analyzer neither reads source bytes nor proves the change was isolated or legitimate.",
                "No materiality judgment, aggregate sensitivity/reliability score, or correctness label is inferred from changed or unchanged output.",
            ]}


def render_markdown(report: dict) -> str:
    """Status-first readable summary plus lossless JSON audit appendix."""
    _json(report)
    def cell(value: Any) -> str:
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    lines = ["Status: Mechanical comparison only; correctness, truth, and general assessor reliability are not established.",
             "", "# Assessor comparison", "", "Kind: " + cell(report.get("kind", "UNDECLARED")),
             "", "Input sample size: " + cell(report.get("sample_size", "UNDECLARED")) + ".",
             "Pair denominator: " + cell(report.get("pair_denominator", "UNDECLARED")) + ".",
             "Eligible pairs: " + cell(report.get("eligible_pair_count", "UNDECLARED")) + ".", "",
             "## Per-field counts", "",
             "| Field | PASS | FAIL | UNSCORABLE | NOT_ASSESSED | Denominator | Scorable denominator | Missing observations | Null observations | Excluded observations |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for field, detail in report.get("fields", {}).items():
        counts = detail.get("counts", {})
        row = [field] + [counts.get(state, "UNDECLARED") for state in OUTCOMES]
        row += [counts.get("denominator", "UNDECLARED"), counts.get("scorable_denominator", "UNDECLARED")]
        row += [detail.get(key, "See audit appendix") for key in (
            "missing_observations", "null_observations", "excluded_observations")]
        lines.append("| " + " | ".join(cell(item) for item in row) + " |")
    if report.get("kind") == "perturbation":
        lines += ["", "Perturbation field denominators count declared rule evaluations (not assessors or experiments).",
                  "Allowed changes and prose unresolved expectations are NOT_ASSESSED; change flags are mechanical review prompts."]
    else:
        lines += ["", "Counts are unordered record pairs per field; observation/prevalence denominators are records, not pairs.",
                  "Material disagreement is an exact mismatch only in an explicitly declared material field; it is not a semantic judgment."]
    lines += ["", "## Limitations", ""]
    lines += ["- " + cell(limit) for limit in report.get("limitations", [])]
    lines += ["", "## Complete audit record", "",
              "This appendix preserves provenance checks, excluded inputs, field presence, class prevalence, unknowns, and unresolved conditions.", ""]
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    runs = [len(match.group()) for match in re.finditer(r"`+", payload)]
    fence = "`" * max(3, max(runs, default=0) + 1)
    lines += [fence + "json", payload, fence, ""]
    return "\n".join(lines)
