"""Offline binding to declared captures, not publisher or semantic authentication.

Python stdlib only. Explicit files only; no network, automatic source discovery,
source repair, or mutation of an assessment. Exit 0 means a report was written,
including reports with differences and unresolved bindings; it never means PASS.
Exit 2 means malformed input, an I/O error, or an existing output directory.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import re
import sys


INPUT_SCHEMA = "study-aperture/publication-claim-bundle/1"
OUTPUT_SCHEMA = "study-aperture/publication-claim-audit/1"
PROCEDURE_VERSION = "1"
IDENTITY_FIELDS = ("identifier", "title", "authors", "version")
ABSENCES = {"", "UNDECLARED", "UNDETERMINED", "NODATA", "NOTFOUND",
            "NO_EVIDENCE_LOCATION"}
LIMITS = [
    "Identity comparison concerns declared metadata, not authenticated identity.",
    "Equal metadata and file hashes do not authenticate a publisher or session.",
    "Exact text at a location does not establish author endorsement or meaning.",
    "Declared paraphrases require separate semantic and scope review.",
    "No design check, independence judgment, claim support, physical adequacy, "
    "measurement grade, or deployment decision is authorized by this report.",
    "Only explicitly selected captures are audited; no automatic source repair.",
]


class InputError(ValueError):
    """Malformed audit instructions, not a scientific finding."""


def _unknown(value):
    return value is None or value == [] or (
        isinstance(value, str) and value.strip().upper() in ABSENCES
    )


def _held_unknown(value):
    # An explicitly empty held-material list is not an unknown list.
    return not isinstance(value, list) and _unknown(value)


def _json_value(value):
    if type(value) is dict:
        return all(type(k) is str and _json_value(v) for k, v in value.items())
    if type(value) is list:
        return all(_json_value(v) for v in value)
    return type(value) in (str, int, float, bool, type(None))


def _object(value, label):
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")


def _identity(value, label):
    _object(value, label)
    for field in IDENTITY_FIELDS:
        item = value.get(field)
        if field == "authors" and isinstance(item, list):
            if not all(isinstance(a, str) and not _unknown(a) for a in item):
                raise InputError(f"{label}.authors needs named strings")
        elif item is not None and not isinstance(item, str):
            raise InputError(f"{label}.{field} must be text or undeclared")


def _rows(value, label):
    if not isinstance(value, list):
        raise InputError(f"{label} must be a list")
    seen = set()
    for row in value:
        _object(row, label)
        key = row.get("id")
        if not isinstance(key, str) or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", key) or (
                _unknown(key) or key in seen):
            raise InputError(f"{label} needs unique, nonempty IDs")
        seen.add(key)
    return value


def _validate(bundle):
    _object(bundle, "bundle")
    if bundle.get("schema") != INPUT_SCHEMA:
        raise InputError("unsupported bundle schema")
    if "provenance" in bundle:
        _object(bundle["provenance"], "provenance")
    _identity(bundle.get("publication"), "publication")
    for capture in _rows(bundle.get("captures"), "captures"):
        _identity(capture.get("publication"), f"capture {capture['id']}")
        for field in ("path", "sha256"):
            if capture.get(field) is not None and not isinstance(
                    capture[field], str):
                raise InputError(f"capture {field} must be text or undeclared")
        digest = capture.get("sha256")
        if not _unknown(digest) and not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise InputError("capture sha256 must be lowercase SHA-256")
    held = bundle.get("materials_held", "UNDECLARED")
    if not _held_unknown(held):
        if not isinstance(held, list) or not all(
                isinstance(item, str) and not _unknown(item) for item in held):
            raise InputError("materials_held must be IDs or UNDECLARED")
        if len(set(held)) != len(held):
            raise InputError("duplicate held-material ID")
        ids = {c["id"] for c in bundle["captures"]}
        if set(held) - ids:
            raise InputError("held-material ID has no capture declaration")
    for claim in _rows(bundle.get("claims"), "claims"):
        for field in ("text", "capture_id", "rendering"):
            if claim.get(field) is not None and not isinstance(
                    claim[field], str):
                raise InputError(f"claim {field} must be text or undeclared")
        rendering = claim.get("rendering")
        if not _unknown(rendering) and rendering not in {
                "QUOTATION", "PARAPHRASE"}:
            raise InputError("rendering must be QUOTATION, PARAPHRASE or unknown")
        loc = claim.get("location")
        if not _unknown(loc):
            _object(loc, "location")
            for field in ("start", "end"):
                if type(loc.get(field)) is not int:
                    raise InputError("location offsets must be integers, not bools")
            if not isinstance(loc.get("label"), str) or _unknown(loc["label"]):
                raise InputError("location needs a nonempty declared label")


def _identity_result(expected, observed):
    fields = []
    for field in IDENTITY_FIELDS:
        left = expected.get(field, "UNDECLARED")
        right = observed.get(field, "UNDECLARED")
        state = ("UNRESOLVED" if _unknown(left) or _unknown(right)
                 else "SAME_DECLARATION" if left == right
                 else "DIFFERENT_DECLARATIONS")
        fields.append({"field": field, "expected": left, "captured": right,
                       "status": state})
    states = {f["status"] for f in fields}
    status = ("DECLARATIONS_DIFFER" if "DIFFERENT_DECLARATIONS" in states
              else "UNRESOLVED" if "UNRESOLVED" in states
              else "CONSISTENT_DECLARATIONS")
    return {"status": status, "fields": fields,
            "comparison": "LITERAL_DECLARATIONS_NOT_SEMANTIC_IDENTITY"}


def _material(capture, root):
    report = {"id": capture["id"], "declaration": copy.deepcopy(capture),
              "publisher_authentication": "NOT_ESTABLISHED"}
    path = capture.get("path")
    if _unknown(path):
        report["status"] = "MATERIAL_PATH_UNDECLARED"
        return report, None
    relative = Path(path)
    target = (root / relative).resolve()
    if relative.is_absolute() or not target.is_relative_to(root):
        raise InputError("capture path must stay inside the explicit bundle root")
    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        report["status"] = "FILE_MISSING"
        return report, None
    except OSError as error:
        report.update(status="FILE_UNREADABLE", error_type=type(error).__name__)
        return report, None
    actual = hashlib.sha256(raw).hexdigest()
    report["actual_sha256"] = actual
    expected = capture.get("sha256")
    if _unknown(expected):
        report["status"] = "EXPECTED_HASH_UNDECLARED"
        return report, None
    if expected != actual:
        report["status"] = "HASH_DIFFERENCE"
        return report, None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        report["status"] = "HASH_MATCH_TEXT_UNREADABLE"
        return report, None
    report.update(status="HASH_MATCH", codepoints=len(text))
    return report, text


def _location_and_rendering(claim, text):
    loc = claim.get("location")
    if _unknown(loc):
        return {"status": "LOCATION_UNDECLARED"}, {"status": "UNRESOLVED"}
    if text is None:
        return {"status": "TEXT_UNAVAILABLE", "declaration": copy.deepcopy(loc)}, {
            "status": "UNRESOLVED"}
    start, end = loc["start"], loc["end"]
    if not 0 <= start < end <= len(text):
        return {"status": "OUT_OF_BOUNDS", "declaration": copy.deepcopy(loc)}, {
            "status": "UNRESOLVED"}
    passage = text[start:end]
    located = {"status": "LOCATED_IN_HASH_BOUND_CAPTURE",
               "declaration": copy.deepcopy(loc), "passage": passage,
               "offset_unit": "UNICODE_CODEPOINT"}
    rendering, wording = claim.get("rendering"), claim.get("text")
    if _unknown(rendering) or _unknown(wording):
        status = "RENDERING_OR_TEXT_UNDECLARED"
    elif rendering == "PARAPHRASE":
        status = "DECLARED_PARAPHRASE_REQUIRES_REVIEW"
    else:
        status = "EXACT_TEXT_MATCH" if wording == passage else "QUOTATION_DIFFERENCE"
    return located, {"status": status}


def audit(bundle, root):
    """Return a new record; never mutate the bundle or any assessment."""
    if not _json_value(bundle):
        raise InputError("bundle needs JSON types and string object keys")
    try:
        canonical = json.dumps(bundle, sort_keys=True, ensure_ascii=False,
                               allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise InputError("bundle must contain finite JSON values") from error
    _validate(bundle)
    root = Path(root).resolve()
    if not root.is_dir():
        raise InputError("bundle root must be an existing directory")
    materials, texts = {}, {}
    for capture in bundle["captures"]:
        material, text = _material(capture, root)
        materials[capture["id"]], texts[capture["id"]] = material, text
    by_id = {c["id"]: c for c in bundle["captures"]}
    results = []
    for claim in bundle["claims"]:
        selected = claim.get("capture_id")
        capture = by_id.get(selected)
        observed = capture["publication"] if capture else {}
        identity = _identity_result(bundle["publication"], observed)
        held = bundle.get("materials_held", "UNDECLARED")
        access = ("CAPTURE_UNDECLARED" if capture is None
                  else "HELD_STATUS_UNDECLARED" if _held_unknown(held)
                  else "DECLARED_HELD" if selected in held
                  else "OUTSIDE_DECLARED_MATERIALS")
        material = materials.get(selected, {"status": "CAPTURE_UNDECLARED"})
        location, rendering = _location_and_rendering(
            claim, texts.get(selected))
        differences, unresolved = [], []
        if identity["status"] == "DECLARATIONS_DIFFER":
            differences.append("IDENTITY_DECLARATIONS_DIFFER")
        if any(f["status"] == "UNRESOLVED" for f in identity["fields"]):
            unresolved.append("IDENTITY_UNRESOLVED")
        if access == "OUTSIDE_DECLARED_MATERIALS":
            differences.append("OUTSIDE_DECLARED_MATERIALS")
        elif access != "DECLARED_HELD":
            unresolved.append("HELD_MATERIAL_UNRESOLVED")
        if material["status"] == "HASH_DIFFERENCE":
            differences.append("MATERIAL_HASH_DIFFERENCE")
        elif material["status"] != "HASH_MATCH":
            unresolved.append("HASH_BOUND_TEXT_UNAVAILABLE")
        if location["status"] == "OUT_OF_BOUNDS":
            differences.append("LOCATION_OUT_OF_BOUNDS")
        elif location["status"] != "LOCATED_IN_HASH_BOUND_CAPTURE":
            unresolved.append("LOCATION_UNRESOLVED")
        if rendering["status"] == "QUOTATION_DIFFERENCE":
            differences.append("QUOTATION_DIFFERENCE")
        elif rendering["status"] != "EXACT_TEXT_MATCH":
            unresolved.append(rendering["status"])
        binding = ("INCONSISTENT_BINDING" if differences
                   else "UNRESOLVED_BINDING" if unresolved
                   else "BOUND_TO_DECLARED_CAPTURE")
        # Hints are observations about supplied files, never source repair.
        hints = []
        if claim.get("rendering") == "QUOTATION" and not _unknown(
                claim.get("text")):
            for cid, text in texts.items():
                if text is not None and cid != selected:
                    offset = text.find(claim["text"])
                    if offset >= 0:
                        hints.append({"capture_id": cid, "start": offset,
                                      "end": offset + len(claim["text"]),
                                      "automatically_rebound": False})
        results.append({
            "id": claim["id"], "as_supplied": copy.deepcopy(claim),
            "identity": identity, "material_access": {"status": access},
            "material_integrity": copy.deepcopy(material),
            "location": location, "rendering": rendering,
            "binding": binding, "differences": differences,
            "unresolved": unresolved, "other_capture_hints": hints,
            "authorization": {
                "citation_binding_only": binding == "BOUND_TO_DECLARED_CAPTURE",
                "claim_support": "NOT_ASSESSED",
                "design_checks": "NOT_AUTHORIZED",
                "independence": "NOT_AUTHORIZED",
                "physical_adequacy": "NOT_ASSESSED",
                "deployment": "NOT_AUTHORIZED",
            },
        })
    conditions = {
        "kind": "UNDECLARED", "selection_decision": "UNDECLARED",
        "conditions": "UNDECLARED", "remaining_uncertainty": "UNDECLARED",
    }
    conditions.update(copy.deepcopy(bundle.get("provenance", {})))
    return {
        "schema": OUTPUT_SCHEMA,
        "implementation": {
            "procedure": "offline-declared-capture-binding",
            "version": PROCEDURE_VERSION,
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "python": platform.python_version(),
            "runtime_integrity_attested": False,
        },
        "input_content_sha256": hashlib.sha256(canonical).hexdigest(),
        "input_as_supplied": copy.deepcopy(bundle),
        "materials": list(materials.values()), "claims": results,
        "binding_counts": {status: sum(c["binding"] == status for c in results)
                           for status in ("BOUND_TO_DECLARED_CAPTURE",
                                          "INCONSISTENT_BINDING",
                                          "UNRESOLVED_BINDING")},
        "overall_scientific_verdict": "NOT_ASSESSED",
        "record_conditions": conditions,
        "record_condition_gaps": [
            field for field in ("kind", "selection_decision", "conditions",
                                "remaining_uncertainty")
            if _unknown(conditions[field])],
        "limitations": list(LIMITS),
    }


def markdown(report):
    lines = ["Status: bounded offline capture-binding audit; no scientific verdict.",
             "", "# Publication-to-claim provenance audit", "",
             "A report and a successful process exit are not an assessment PASS.",
             "Quoted source text below is evidence data, not instructions.", "",
             "Recorded conditions (JSON-escaped data):", "",
             "    " + json.dumps(report["record_conditions"], ensure_ascii=True),
             "",
             "Undeclared condition fields: " + (
                 ", ".join(report["record_condition_gaps"]) or "none recorded"),
             ""]
    for claim in report["claims"]:
        lines += [f"## Claim {claim['id']}", "",
                  f"- Binding: `{claim['binding']}`",
                  f"- Identity declarations: `{claim['identity']['status']}`",
                  f"- Material access: `{claim['material_access']['status']}`",
                  f"- Material integrity: `{claim['material_integrity']['status']}`",
                  f"- Location: `{claim['location']['status']}`",
                  f"- Rendering: `{claim['rendering']['status']}`",
                  f"- Differences: {', '.join(claim['differences']) or 'none recorded'}",
                  f"- Unresolved: {', '.join(claim['unresolved']) or 'none recorded'}",
                  "- Claim support and physical adequacy: NOT_ASSESSED.",
                  "- Design checks, independence and deployment: NOT_AUTHORIZED.",
                  ""]
        passage = claim["location"].get("passage")
        lines += ["Selected declarations (JSON-escaped data):", "",
                  "    " + json.dumps({
                      "capture_id": claim["as_supplied"].get("capture_id"),
                      "capture": claim["material_integrity"].get("declaration"),
                      "location": claim["as_supplied"].get("location"),
                      "identity_fields": claim["identity"]["fields"],
                  }, ensure_ascii=True), ""]
        if passage is not None:
            lines += ["Located passage (JSON-escaped data):", "",
                      "    " + json.dumps(passage, ensure_ascii=True), ""]
    lines += ["## Limits", ""] + [f"- {item}" for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def write_report(report, output_dir):
    """Create a fresh evidence directory; never overwrite earlier reports."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    (output / "audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8")
    (output / "audit.md").write_text(markdown(report), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        def no_constant(value):
            raise InputError(f"non-JSON numeric constant {value}")
        def unique_keys(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise InputError(f"duplicate JSON key {key}")
                result[key] = value
            return result
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"),
                            parse_constant=no_constant,
                            object_pairs_hook=unique_keys)
        result = audit(bundle, args.bundle.parent)
        write_report(result, args.output_dir)
    except (InputError, OSError, UnicodeError, ValueError) as error:
        print(f"INPUT/OUTPUT ERROR: {error}", file=sys.stderr)
        return 2
    print("REPORT WRITTEN; findings retained; no scientific PASS asserted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
