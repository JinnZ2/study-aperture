"""Adversarial, stdlib-only tests for the narrow offline integrity checker."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LAB = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("integrity_checker", LAB / "integrity_checker.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
OLD = "urn:scope-audit-lab:schema:math-evidence:0.1"
NEW = "urn:scope-audit-lab:schema:math-physics-extensions:0.2"


def present(value):
    return {"status": "PRESENT", "value": value}


def missing():
    return {"status": "MISSING", "reason": "Not established."}


def ref(name, kind, state="NOT_CHECKED"):
    return {"record_id": name, "expected_type": kind, "resolution": state}


def record(name, kind, payload=None, version="v1"):
    new = kind in checker.CONTRACTS[(NEW, "0.2")]
    return {
        "schema_id": NEW if new else OLD, "schema_version": "0.2" if new else "0.1",
        "record_id": name, "record_type": kind,
        "record_version": present(version) if version is not None else missing(),
        "payload": payload or {},
    }


def fixture(outcome="NOT_EVALUATED"):
    anchor = record("lab:anchor", "physics_anchor", {
        "conditions": [{"condition_id": "C1", "exact_requirement": "Declared boundary.",
                        "citation_ids": ["S1"]}],
        "source_citations": [{"citation_id": "S1"}],
    })
    observation = record("lab:observation", "observation")
    assessment = record("lab:assessment", "assessment", {
        "subjects": [{"subject": ref("lab:observation", "observation"),
                      "examined_version": present("v1")}],
    })
    application = record("lab:application", "anchor_application", {
        "anchor": ref("lab:anchor", "physics_anchor"), "anchor_version": present("v1"),
        "subjects": [{"subject": ref("lab:observation", "observation"),
                      "examined_version": present("v1")}],
        "condition_checks": [{
            "requirement_id": "C1", "exact_requirement": "Declared boundary.",
            "outcome": outcome,
            "evidence_refs": [ref("lab:observation", "observation")] if outcome in {"MET", "NOT_MET"} else [],
        }],
        "unaddressed_conditions": [], "symbol_mappings": [],
        "applicability_status": "UNKNOWN", "comparison_status": "NOT_EVALUATED",
        "applicability_assessment_refs": [], "comparison_assessment_refs": [],
    })
    return [anchor, observation, assessment, application]


def codes(report):
    return {f["code"] for f in report["findings"]}


class IntegrityTests(unittest.TestCase):
    def test_reference_resolves(self):
        r = checker.check_records(fixture())
        self.assertTrue(all(x["snapshot_resolution"] == "RESOLVED" for x in r["reference_resolution"]))

    def test_false_resolved_assertion_cannot_create_target(self):
        rows = fixture()
        rows[3]["payload"]["anchor"] = ref("absent", "physics_anchor", "RESOLVED")
        r = checker.check_records(rows)
        self.assertIn("REFERENCE_UNRESOLVED", codes(r))
        self.assertIn("REFERENCE_DECLARATION_DIFFERS", codes(r))

    def test_type_mismatch(self):
        rows = fixture()
        rows[3]["payload"]["subjects"][0]["subject"]["expected_type"] = "equation"
        self.assertIn("REFERENCE_TYPE_MISMATCH", codes(checker.check_records(rows)))

    def test_duplicate_different_versions_ambiguous_not_latest(self):
        rows = fixture()
        changed = copy.deepcopy(rows[0])
        changed["record_version"] = present("v2")
        r = checker.check_records(rows + [changed])
        self.assertIn("DUPLICATE_ID_CONFLICT", codes(r))
        self.assertEqual(r["anchor_condition_coverage"][0]["anchor_reference_resolution"], "AMBIGUOUS")

    def test_duplicate_same_version_changed_content_is_ambiguous(self):
        rows = fixture()
        changed = copy.deepcopy(rows[0])
        changed["payload"]["new"] = 0
        self.assertIn("REFERENCE_AMBIGUOUS", codes(checker.check_records(rows + [changed])))

    def test_identical_reimport_retains_occurrences(self):
        rows = fixture()
        r = checker.check_records(rows + [copy.deepcopy(rows[0])])
        self.assertIn("IDENTICAL_REIMPORT", codes(r))
        self.assertNotIn("DUPLICATE_ID_CONFLICT", codes(r))
        self.assertEqual(r["summary"]["record_occurrences"], 5)

    def test_unsupported_contract_opaque_not_admitted(self):
        rows = fixture()
        rows[0]["schema_version"] = "99"
        r = checker.check_records(rows)
        self.assertIn("OPAQUE_CONTRACT", codes(r))
        self.assertIn("REFERENCE_OPAQUE_TARGET", codes(r))

    def test_version_same_is_not_content_proof(self):
        r = checker.check_records(fixture())
        self.assertTrue(all(v["binding_status"] == "SAME_DECLARED_VERSION" for v in r["version_bindings"]))
        self.assertTrue(all(v["content_state_equality_established"] is False for v in r["version_bindings"]))

    def test_subject_version_mismatch(self):
        rows = fixture()
        rows[3]["payload"]["subjects"][0]["examined_version"] = present("v0")
        self.assertIn("BINDING_DIFFERENT_DECLARED_VERSION", codes(checker.check_records(rows)))

    def test_anchor_version_mismatch_does_not_pass_bound_coverage(self):
        rows = fixture()
        rows[3]["payload"]["anchor_version"] = present("v0")
        c = checker.check_records(rows)["anchor_condition_coverage"][0]
        self.assertEqual(c["identity_coverage"], "COMPLETE")
        self.assertEqual(c["coverage_for_bound_version"], "UNESTABLISHED")

    def test_missing_examined_version(self):
        rows = fixture()
        rows[3]["payload"]["anchor_version"] = missing()
        self.assertIn("BINDING_VERSION_UNKNOWN", codes(checker.check_records(rows)))

    def test_missing_target_version(self):
        rows = fixture()
        rows[0]["record_version"] = missing()
        self.assertIn("BINDING_VERSION_UNKNOWN", codes(checker.check_records(rows)))

    def test_version_zero_string_is_present(self):
        rows = fixture()
        rows[0]["record_version"] = present("0")
        rows[3]["payload"]["anchor_version"] = present("0")
        self.assertEqual(checker.check_records(rows)["anchor_condition_coverage"][0]["anchor_binding_status"],
                         "SAME_DECLARED_VERSION")

    def test_malformed_numeric_version_not_coerced(self):
        rows = fixture()
        rows[0]["record_version"] = present(0)
        self.assertIn("VERSION_MALFORMED", codes(checker.check_records(rows)))

    def test_age_not_used_for_staleness(self):
        rows = fixture("MET")
        rows[0]["recorded_at"] = present("1900-01-01T00:00:00Z")
        r = checker.check_records(rows)
        self.assertNotIn("BINDING_DIFFERENT_DECLARED_VERSION", codes(r))
        self.assertEqual(r["summary"]["status"], "NO_GAPS_DETECTED_WITHIN_CHECKED_SCOPE")

    def test_missing_condition_reported(self):
        rows = fixture()
        rows[3]["payload"]["condition_checks"] = []
        r = checker.check_records(rows)
        self.assertIn("ANCHOR_CONDITION_UNADDRESSED", codes(r))
        self.assertEqual(r["anchor_condition_coverage"][0]["missing_conditions"], ["C1"])

    def test_extra_condition_reported(self):
        rows = fixture()
        extra = copy.deepcopy(rows[3]["payload"]["condition_checks"][0])
        extra["requirement_id"] = "other"
        rows[3]["payload"]["condition_checks"].append(extra)
        self.assertIn("ANCHOR_CHECK_NOT_IN_ANCHOR", codes(checker.check_records(rows)))

    def test_duplicate_condition_check_not_selected(self):
        rows = fixture()
        rows[3]["payload"]["condition_checks"] *= 2
        r = checker.check_records(rows)
        self.assertIn("DUPLICATE_CONDITION_ID", codes(r))
        self.assertEqual(r["anchor_condition_coverage"][0]["identity_coverage"], "INVALID")

    def test_duplicate_anchor_condition_not_selected(self):
        rows = fixture()
        rows[0]["payload"]["conditions"] *= 2
        self.assertIn("DUPLICATE_CONDITION_ID", codes(checker.check_records(rows)))

    def test_requirement_text_cannot_be_silently_changed(self):
        rows = fixture()
        rows[3]["payload"]["condition_checks"][0]["exact_requirement"] = "Different rule."
        self.assertIn("CONDITION_TEXT_MISMATCH", codes(checker.check_records(rows)))

    def test_complete_coverage_not_outcome_pass(self):
        r = checker.check_records(fixture())
        c = r["anchor_condition_coverage"][0]
        self.assertEqual(c["identity_coverage"], "COMPLETE")
        self.assertFalse(c["condition_truth_established"])
        self.assertIn("CONDITION_NOT_EVALUATED", codes(r))
        self.assertEqual(r["summary"]["status"], "INTEGRITY_GAPS_RECORDED")

    def test_unmet_criterion_record_not_declared_invalid(self):
        r = checker.check_records(fixture("NOT_MET"))
        self.assertIn("CONDITION_DECLARED_NOT_MET", codes(r))
        self.assertEqual(r["summary"]["finding_counts"]["ERROR"], 0)

    def test_positive_applicability_conflicts_with_unmet_condition(self):
        rows = fixture("NOT_MET")
        rows[3]["payload"]["applicability_status"] = "IN_SCOPE_FOR_STATED_CHECK"
        rows[3]["payload"]["applicability_assessment_refs"] = [ref("lab:assessment", "assessment")]
        self.assertIn("APPLICABILITY_CONDITION_CONFLICT", codes(checker.check_records(rows)))

    def test_positive_status_with_unevaluated_checks_not_promoted(self):
        rows = fixture()
        rows[3]["payload"]["applicability_status"] = "IN_SCOPE_FOR_STATED_CHECK"
        self.assertIn("POSITIVE_STATUS_NOT_ESTABLISHED", codes(checker.check_records(rows)))

    def test_met_without_evidence_flagged(self):
        rows = fixture("MET")
        rows[3]["payload"]["condition_checks"][0]["evidence_refs"] = []
        self.assertIn("CONDITION_EVIDENCE_MISSING", codes(checker.check_records(rows)))

    def test_outside_scope_does_not_authorize_law_verdict(self):
        rows = fixture()
        rows[3]["payload"].update(applicability_status="OUTSIDE_DECLARED_SCOPE",
                                  comparison_status="DISCREPANCY_RECORDED")
        self.assertIn("COMPARISON_APPLICABILITY_CONFLICT", codes(checker.check_records(rows)))

    def test_unknown_citation_id_reported(self):
        rows = fixture()
        rows[0]["payload"]["conditions"][0]["citation_ids"] = ["absent"]
        self.assertIn("CONDITION_CITATION_UNRESOLVED", codes(checker.check_records(rows)))

    def test_reference_cycle_does_not_recurse_graph(self):
        rows = fixture("MET")
        rows[0]["payload"]["backlink"] = ref("lab:application", "anchor_application")
        self.assertEqual(checker.check_records(rows)["summary"]["record_occurrences"], 4)

    def test_input_records_unchanged(self):
        rows = fixture()
        before = copy.deepcopy(rows)
        checker.check_records(rows)
        self.assertEqual(rows, before)

    def test_missing_input_not_zero_or_fake_reference(self):
        rows = fixture()
        rows.append(record("lab:calculation", "calculation", {
            "inputs": [{"input": missing(), "examined_version": missing()}],
        }))
        r = checker.check_records(rows)
        self.assertTrue(any(v["reference_resolution"] == "ABSENT" for v in r["version_bindings"]))
        self.assertFalse(any(v.get("value") == 0 for v in r["version_bindings"]))

    def test_input_binding_version_checked(self):
        rows = fixture()
        rows.append(record("lab:calculation", "calculation", {
            "inputs": [{"input": ref("lab:observation", "observation"), "examined_version": present("wrong")}],
        }))
        self.assertIn("BINDING_DIFFERENT_DECLARED_VERSION", codes(checker.check_records(rows)))

    def test_empty_snapshot_not_complete(self):
        self.assertIn("EMPTY_SNAPSHOT", codes(checker.check_records([])))

    def test_malformed_shapes_diagnosed_without_crash(self):
        mutations = [
            lambda r: r[0].__setitem__("record_id", []),
            lambda r: r[0].__setitem__("record_type", []),
            lambda r: r[0].__setitem__("schema_id", []),
            lambda r: r[0].__setitem__("record_version", {"status": []}),
            lambda r: r[3]["payload"].__setitem__("condition_checks", [None]),
            lambda r: r[3]["payload"]["condition_checks"][0].__setitem__("outcome", []),
            lambda r: r[3]["payload"].__setitem__("applicability_status", []),
            lambda r: r[3]["payload"].__setitem__("comparison_status", {}),
            lambda r: r[3]["payload"]["anchor"].__setitem__("resolution", []),
            lambda r: r[3]["payload"]["anchor"].pop("record_id"),
            lambda r: r[3].pop("record_id"),
            lambda r: r[3].__setitem__("payload", None),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                rows = fixture()
                mutate(rows)
                self.assertEqual(checker.check_records(rows)["summary"]["status"], "INTEGRITY_GAPS_RECORDED")

    def test_two_supported_bundles_checked(self):
        paths = [LAB / "examples/schema-draft-0.1/records.json",
                 LAB / "examples/schema-draft-0.2/records.json"]
        r = checker.Checker([checker.load_document(p) for p in paths]).run()
        self.assertEqual(r["summary"]["record_occurrences"], 19)
        self.assertIn("REFERENCE_UNRESOLVED", codes(r))
        self.assertEqual(r["anchor_condition_coverage"][0]["identity_coverage"], "COMPLETE")

    def test_no_network_or_submitted_code_execution(self):
        import socket
        rows = fixture()
        rows[0]["payload"]["url"] = "https://example.invalid/never-fetch"
        rows[0]["payload"]["code"] = "raise Exception('never-execute')"
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
                patch.object(subprocess, "Popen", side_effect=AssertionError("execution forbidden")):
            checker.check_records(rows)

    def test_markdown_keeps_unknowns_and_limits_visible(self):
        r = checker.check_records(fixture())
        m = checker.markdown(r)
        self.assertIn("CONDITION_NOT_EVALUATED", m)
        self.assertIn("not that the conditions are met", m)
        self.assertIn("not mathematical or empirical validation", m)

    def test_same_version_does_not_rescue_changed_requirement(self):
        rows = fixture("MET")
        rows[0]["payload"]["conditions"][0]["exact_requirement"] = "New requirement."
        self.assertIn("CONDITION_TEXT_MISMATCH", codes(checker.check_records(rows)))

    def test_version_strings_not_normalized(self):
        rows = fixture()
        rows[3]["payload"]["anchor_version"] = present("v1 ")
        self.assertIn("BINDING_DIFFERENT_DECLARED_VERSION", codes(checker.check_records(rows)))

    def test_declared_unaddressed_note_does_not_hide_missing_check(self):
        rows = fixture()
        rows[3]["payload"]["condition_checks"] = []
        rows[3]["payload"]["unaddressed_conditions"] = ["C1 deliberately not checked"]
        c = codes(checker.check_records(rows))
        self.assertIn("ANCHOR_CONDITION_UNADDRESSED", c)
        self.assertIn("DECLARED_UNADDRESSED_CONDITIONS", c)

    def test_unresolved_evidence_blocks_positive_status_support(self):
        rows = fixture("MET")
        app = rows[3]["payload"]
        app["condition_checks"][0]["evidence_refs"] = [ref("missing", "observation")]
        app["applicability_status"] = "IN_SCOPE_FOR_STATED_CHECK"
        app["applicability_assessment_refs"] = [ref("lab:assessment", "assessment")]
        self.assertIn("POSITIVE_STATUS_NOT_ESTABLISHED", codes(checker.check_records(rows)))

    def test_invalid_status_is_diagnostic_even_if_conditions_declared_met(self):
        rows = fixture("MET")
        rows[3]["payload"]["applicability_status"] = []
        self.assertIn("APPLICATION_STATUS_MALFORMED", codes(checker.check_records(rows)))

    def test_anchor_ref_cannot_target_an_observation(self):
        rows = fixture()
        rows[3]["payload"]["anchor"] = ref("lab:observation", "observation")
        self.assertIn("ANCHOR_REFERENCE_TYPE_INVALID", codes(checker.check_records(rows)))

    def test_duplicate_citation_ids(self):
        rows = fixture()
        rows[0]["payload"]["source_citations"] *= 2
        self.assertIn("DUPLICATE_CITATION_ID", codes(checker.check_records(rows)))

    def test_missing_version_cannot_be_rescued_by_artifact_name(self):
        rows = fixture()
        rows[3]["payload"]["anchor_version"] = missing()
        rows[3]["payload"]["artifact"] = "looks-current.txt"
        self.assertEqual(checker.check_records(rows)["anchor_condition_coverage"][0]["coverage_for_bound_version"],
                         "UNESTABLISHED")

    def test_calculation_retains_actual_zero_without_evaluation(self):
        rows = fixture("MET")
        rows.append(record("lab:calculation", "calculation", {
            "inputs": [{"input": ref("lab:observation", "observation"), "examined_version": present("v1")}],
            "result": {"status": "PRESENT", "value": 0, "encoding": "json_number"},
        }))
        before = copy.deepcopy(rows)
        checker.check_records(rows)
        self.assertEqual(rows, before)

    def test_json_pointer_escaping(self):
        rows = fixture()
        rows[1]["payload"]["a/b~"] = ref("missing", "artifact")
        resolutions = checker.check_records(rows)["reference_resolution"]
        self.assertTrue(any(r["location"]["pointer"].endswith("/payload/a~1b~0") for r in resolutions))

    def test_markdown_escapes_untrusted_html(self):
        rows = fixture()
        rows[3]["payload"]["condition_checks"] = []
        rows[0]["payload"]["conditions"][0]["condition_id"] = "<script>bad</script>"
        m = checker.markdown(checker.check_records(rows))
        self.assertNotIn("<script>", m)
        self.assertIn("&lt;script&gt;", m)

    def test_incomplete_reference_in_known_slot_not_silently_skipped(self):
        rows = fixture()
        rows[1]["source_refs"] = [{"record_id": "missing"}, None, "missing"]
        r = checker.check_records(rows)
        self.assertEqual(sum(x["snapshot_resolution"] == "MALFORMED" for x in r["reference_resolution"]), 3)
        self.assertIn("REFERENCE_MALFORMED", codes(r))
        checker.markdown(r)

    def test_reference_list_must_be_array(self):
        rows = fixture()
        rows[1]["source_refs"] = "not-an-array"
        self.assertIn("REFERENCE_LIST_MALFORMED", codes(checker.check_records(rows)))

    def test_source_slot_cannot_be_retyped_to_hide_wrong_target(self):
        rows = fixture()
        rows[1]["source_refs"] = [ref("lab:observation", "observation")]
        self.assertIn("REFERENCE_CONTEXT_TYPE_MISMATCH", codes(checker.check_records(rows)))

    def test_single_json_object_not_accepted_as_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            p.write_text('{"record_id":"a"}')
            with self.assertRaises(ValueError):
                checker.load_document(p)

    def test_duplicate_json_members_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            p.write_text('{"records":[],"records":[{}]}')
            with self.assertRaises(ValueError):
                checker.load_document(p)

    def test_nonfinite_numbers_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            for value in ("NaN", "Infinity", "-Infinity", "1e9999"):
                with self.subTest(value=value):
                    p.write_text('[{"value":' + value + '}]')
                    with self.assertRaises(ValueError):
                        checker.load_document(p)

    def test_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            p.write_text(" " * 20)
            with patch.object(checker, "MAX_BYTES", 10):
                with self.assertRaises(ValueError):
                    checker.load_document(p)

    def test_cli_exit_codes_and_no_input_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            for outcome, code in (("MET", 0), ("NOT_EVALUATED", 1)):
                p.write_text(json.dumps(fixture(outcome)))
                before = p.read_bytes()
                proc = subprocess.run([sys.executable, str(LAB / "integrity_checker.py"), str(p)],
                                      capture_output=True, text=True, check=False)
                self.assertEqual(proc.returncode, code, proc.stderr)
                self.assertEqual(p.read_bytes(), before)
                self.assertEqual(json.loads(proc.stdout)["structural_schema_validation"], "NOT_PERFORMED")
            p.write_text("{")
            proc = subprocess.run([sys.executable, str(LAB / "integrity_checker.py"), str(p)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(json.loads(proc.stderr)["status"], "INPUT_OR_OUTPUT_REJECTED")

    def test_cli_never_overwrites_existing_output_or_input(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.json"
            p.write_text(json.dumps(fixture()))
            before = p.read_bytes()
            proc = subprocess.run([sys.executable, str(LAB / "integrity_checker.py"),
                                   str(p), "--output", str(p)], capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 2)
            self.assertEqual(p.read_bytes(), before)

    def test_cli_new_markdown_output(self):
        with tempfile.TemporaryDirectory() as d:
            p, out = Path(d) / "a.json", Path(d) / "report.md"
            p.write_text(json.dumps(fixture()))
            proc = subprocess.run([sys.executable, str(LAB / "integrity_checker.py"), str(p),
                                   "--format", "markdown", "--output", str(out)],
                                  capture_output=True, text=True, check=False)
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(out.read_text().startswith("# Offline evidence-integrity report"))


if __name__ == "__main__":
    unittest.main()
