"""Independent binding expectations; no network or scientific-validity scoring."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from experimental.publication_provenance import audit as engine
from experimental.publication_provenance import demo


ROOT = Path(__file__).resolve().parents[1]

# Hand-stated expectations, not calculated by the instrument under test.
EXPECTED = {
    "exact-positive": "BOUND_TO_DECLARED_CAPTURE",
    "identifier-difference": "INCONSISTENT_BINDING",
    "same-id-title-difference": "INCONSISTENT_BINDING",
    "author-difference": "INCONSISTENT_BINDING",
    "version-difference": "INCONSISTENT_BINDING",
    "missing-version": "UNRESOLVED_BINDING",
    "difference-with-unknown": "INCONSISTENT_BINDING",
    "empty-held-list": "INCONSISTENT_BINDING",
    "unknown-held-list": "UNRESOLVED_BINDING",
    "full-text-outside-held": "INCONSISTENT_BINDING",
    "missing-location": "UNRESOLVED_BINDING",
    "invalid-span": "INCONSISTENT_BINDING",
    "declared-paraphrase": "UNRESOLVED_BINDING",
    "undeclared-rendering": "UNRESOLVED_BINDING",
    "empty-quote": "UNRESOLVED_BINDING",
    "quotation-difference": "INCONSISTENT_BINDING",
    "different-donor-not-repaired": "INCONSISTENT_BINDING",
    "changed-hash": "INCONSISTENT_BINDING",
    "missing-file": "UNRESOLVED_BINDING",
    "missing-hash": "UNRESOLVED_BINDING",
    "undeclared-capture": "UNRESOLVED_BINDING",
    "no-promotion": "BOUND_TO_DECLARED_CAPTURE",
}


class PublicationClaimAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "a.txt").write_bytes(demo.A.encode())
        (self.root / "b.txt").write_bytes(demo.B.encode())
        self.bundle = demo.base_bundle()

    def one(self, bundle=None):
        return engine.audit(self.bundle if bundle is None else bundle,
                            self.root)["claims"][0]

    def test_independent_constructed_expected_matrix(self):
        cases = demo.constructed_cases()
        self.assertEqual(set(cases), set(EXPECTED))
        for name, expected in EXPECTED.items():
            with self.subTest(case=name):
                self.assertEqual(self.one(cases[name])["binding"], expected)

    def test_positive_control_has_only_narrow_citation_authorization(self):
        result = self.one()
        self.assertEqual(result["rendering"]["status"], "EXACT_TEXT_MATCH")
        self.assertEqual(result["differences"], [])
        self.assertEqual(result["unresolved"], [])
        self.assertTrue(result["authorization"]["citation_binding_only"])
        self.assertEqual(result["authorization"]["physical_adequacy"], "NOT_ASSESSED")
        self.assertEqual(result["material_integrity"]["publisher_authentication"],
                         "NOT_ESTABLISHED")

    def test_known_difference_and_unknown_survive_together(self):
        result = self.one(demo.constructed_cases()["difference-with-unknown"])
        self.assertIn("IDENTITY_DECLARATIONS_DIFFER", result["differences"])
        self.assertIn("IDENTITY_UNRESOLVED", result["unresolved"])
        fields = {f["field"]: f["status"] for f in result["identity"]["fields"]}
        self.assertEqual(fields["identifier"], "DIFFERENT_DECLARATIONS")
        self.assertEqual(fields["version"], "UNRESOLVED")

    def test_no_source_repair_when_other_capture_contains_exact_text(self):
        result = self.one(demo.constructed_cases()["different-donor-not-repaired"])
        self.assertEqual(result["as_supplied"]["capture_id"], "a")
        self.assertEqual(result["binding"], "INCONSISTENT_BINDING")
        self.assertEqual(result["other_capture_hints"][0]["capture_id"], "b")
        self.assertFalse(result["other_capture_hints"][0]["automatically_rebound"])

    def test_exact_quote_cannot_clear_wrong_identity(self):
        bundle = copy.deepcopy(self.bundle)
        bundle["publication"]["identifier"] = "constructed:other"
        result = self.one(bundle)
        self.assertEqual(result["rendering"]["status"], "EXACT_TEXT_MATCH")
        self.assertEqual(result["binding"], "INCONSISTENT_BINDING")
        self.assertFalse(result["authorization"]["citation_binding_only"])

    def test_exact_quote_and_identity_cannot_clear_material_access(self):
        result = self.one(demo.constructed_cases()["full-text-outside-held"])
        self.assertEqual(result["identity"]["status"], "CONSISTENT_DECLARATIONS")
        self.assertEqual(result["rendering"]["status"], "EXACT_TEXT_MATCH")
        self.assertIn("OUTSIDE_DECLARED_MATERIALS", result["differences"])

    def test_explicit_empty_materials_are_not_undeclared_materials(self):
        cases = demo.constructed_cases()
        self.assertEqual(self.one(cases["empty-held-list"])["material_access"]["status"],
                         "OUTSIDE_DECLARED_MATERIALS")
        self.assertEqual(self.one(cases["unknown-held-list"])["material_access"]["status"],
                         "HELD_STATUS_UNDECLARED")

    def test_hash_difference_does_not_turn_into_quote_or_physical_failure(self):
        (self.root / "a.txt").write_text("changed file", encoding="utf-8")
        result = self.one()
        self.assertEqual(result["material_integrity"]["status"], "HASH_DIFFERENCE")
        self.assertEqual(result["rendering"]["status"], "UNRESOLVED")
        self.assertEqual(result["identity"]["status"], "CONSISTENT_DECLARATIONS")
        self.assertEqual(result["authorization"]["physical_adequacy"], "NOT_ASSESSED")

    def test_missing_file_is_not_quotation_absence(self):
        (self.root / "a.txt").unlink()
        result = self.one()
        self.assertEqual(result["material_integrity"]["status"], "FILE_MISSING")
        self.assertEqual(result["location"]["status"], "TEXT_UNAVAILABLE")
        self.assertEqual(result["binding"], "UNRESOLVED_BINDING")
        self.assertEqual(result["differences"], [])

    def test_matching_paraphrase_still_needs_semantic_review(self):
        self.bundle["claims"][0]["rendering"] = "PARAPHRASE"
        result = self.one()
        self.assertEqual(result["rendering"]["status"],
                         "DECLARED_PARAPHRASE_REQUIRES_REVIEW")
        self.assertEqual(result["binding"], "UNRESOLVED_BINDING")

    def test_close_paraphrase_marked_as_quote_does_not_pass(self):
        self.bundle["claims"][0]["text"] = "Chamber A readings averaged 2.44 units."
        self.assertEqual(self.one()["rendering"]["status"], "QUOTATION_DIFFERENCE")

    def test_offset_binding_not_any_occurrence_elsewhere(self):
        original = demo.A.rstrip("\n")
        text = original + "\nOther passage.\n"
        (self.root / "a.txt").write_text(text, encoding="utf-8")
        self.bundle["captures"][0]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        self.bundle["claims"][0]["location"].update(
            start=len(original) + 1, end=len(text) - 1)
        self.assertEqual(self.one()["rendering"]["status"], "QUOTATION_DIFFERENCE")

    def test_unicode_offsets_are_codepoints_not_byte_offsets(self):
        text = "μ: 2.44°"
        (self.root / "a.txt").write_bytes(text.encode())
        self.bundle["captures"][0]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        self.bundle["claims"][0].update(
            text=text, location={"start": 0, "end": len(text), "label": "unicode"})
        self.assertEqual(self.one()["binding"], "BOUND_TO_DECLARED_CAPTURE")
        self.bundle["claims"][0]["location"]["end"] = len(text.encode())
        self.assertEqual(self.one()["location"]["status"], "OUT_OF_BOUNDS")

    def test_empty_span_cannot_be_a_vacuous_match(self):
        self.bundle["claims"][0]["location"]["end"] = 0
        self.assertEqual(self.one()["location"]["status"], "OUT_OF_BOUNDS")

    def test_unreadable_utf8_is_not_a_negative_claim_finding(self):
        raw = b"\xff\xfe"
        (self.root / "a.txt").write_bytes(raw)
        self.bundle["captures"][0]["sha256"] = hashlib.sha256(raw).hexdigest()
        result = self.one()
        self.assertEqual(result["material_integrity"]["status"],
                         "HASH_MATCH_TEXT_UNREADABLE")
        self.assertEqual(result["binding"], "UNRESOLVED_BINDING")

    def test_input_and_supplied_support_are_never_mutated_or_promoted(self):
        bundle = demo.constructed_cases()["no-promotion"]
        before = copy.deepcopy(bundle)
        result = engine.audit(bundle, self.root)
        self.assertEqual(bundle, before)
        self.assertEqual(result["input_as_supplied"], before)
        for claim in result["claims"]:
            self.assertEqual(claim["authorization"]["claim_support"], "NOT_ASSESSED")
            for field in ("design_checks", "independence", "deployment"):
                self.assertEqual(claim["authorization"][field], "NOT_AUTHORIZED")
        result["claims"][0]["as_supplied"]["text"] = "modified returned record"
        self.assertEqual(bundle, before)
        self.assertEqual(result["input_as_supplied"], before)

    def test_one_good_claim_does_not_clear_sibling(self):
        wrong = copy.deepcopy(self.bundle["claims"][0])
        wrong.update(id="C2", text="Different sentence.")
        self.bundle["claims"].append(wrong)
        report = engine.audit(self.bundle, self.root)
        self.assertEqual([c["binding"] for c in report["claims"]],
                         ["BOUND_TO_DECLARED_CAPTURE", "INCONSISTENT_BINDING"])
        self.assertEqual(report["binding_counts"]["BOUND_TO_DECLARED_CAPTURE"], 1)

    def test_execution_order_does_not_change_claim_results(self):
        second = copy.deepcopy(self.bundle["claims"][0])
        second.update(id="C2", text="Another sentence.")
        self.bundle["claims"].append(second)
        first = engine.audit(self.bundle, self.root)
        self.bundle["claims"].reverse()
        second_report = engine.audit(self.bundle, self.root)
        self.assertEqual({c["id"]: c for c in first["claims"]},
                         {c["id"]: c for c in second_report["claims"]})

    def test_duplicate_ids_and_bool_offsets_are_input_errors(self):
        for kind in ("duplicate-capture", "duplicate-claim", "bool-offset"):
            bundle = copy.deepcopy(self.bundle)
            if kind == "duplicate-capture":
                bundle["captures"].append(copy.deepcopy(bundle["captures"][0]))
            elif kind == "duplicate-claim":
                bundle["claims"].append(copy.deepcopy(bundle["claims"][0]))
            else:
                bundle["claims"][0]["location"]["start"] = False
            with self.subTest(kind=kind), self.assertRaises(engine.InputError):
                engine.audit(bundle, self.root)

    def test_unknown_held_reference_is_not_silently_accepted(self):
        self.bundle["materials_held"] = ["not-declared"]
        with self.assertRaises(engine.InputError):
            self.one()

    def test_parent_and_symlink_path_escape_are_rejected(self):
        self.bundle["captures"][0]["path"] = "../outside.txt"
        with self.assertRaises(engine.InputError):
            self.one()
        (self.root / "link").symlink_to(self.root.parent, target_is_directory=True)
        self.bundle["captures"][0]["path"] = "link/outside.txt"
        with self.assertRaises(engine.InputError):
            self.one()

    def test_api_rejects_nonfinite_json_values(self):
        self.bundle["nonfinite"] = float("nan")
        with self.assertRaises(engine.InputError):
            self.one()

    def test_api_rejects_non_json_types_and_nonstring_keys(self):
        for value in (("tuple",), {1: "integer key"}, {"set"}):
            bundle = copy.deepcopy(self.bundle)
            bundle["extra"] = value
            with self.subTest(value=repr(value)):
                with self.assertRaises(engine.InputError):
                    self.one(bundle)

    def test_procedure_fingerprint_is_not_runtime_attestation(self):
        report = engine.audit(self.bundle, self.root)
        metadata = report["implementation"]
        self.assertEqual(metadata["version"], "1")
        self.assertEqual(metadata["source_sha256"], hashlib.sha256(
            Path(engine.__file__).read_bytes()).hexdigest())
        self.assertFalse(metadata["runtime_integrity_attested"])

    def test_missing_record_conditions_remain_explicit(self):
        del self.bundle["provenance"]
        report = engine.audit(self.bundle, self.root)
        self.assertEqual(set(report["record_condition_gaps"]), {
            "kind", "selection_decision", "conditions", "remaining_uncertainty"})
        self.assertEqual(report["record_conditions"]["conditions"], "UNDECLARED")
        self.assertEqual(report["overall_scientific_verdict"], "NOT_ASSESSED")

    def test_formatting_difference_is_not_a_scientific_verdict(self):
        self.bundle["publication"]["title"] = "Chamber  protocol"
        result = self.one()
        self.assertEqual(result["identity"]["status"], "DECLARATIONS_DIFFER")
        self.assertEqual(result["authorization"]["physical_adequacy"], "NOT_ASSESSED")
        self.assertEqual(result["identity"]["comparison"],
                         "LITERAL_DECLARATIONS_NOT_SEMANTIC_IDENTITY")

    def test_no_claims_is_not_a_vacuous_scientific_pass(self):
        self.bundle["claims"] = []
        result = engine.audit(self.bundle, self.root)
        self.assertEqual(sum(result["binding_counts"].values()), 0)
        self.assertEqual(result["overall_scientific_verdict"], "NOT_ASSESSED")

    def test_report_output_is_fresh_and_preserves_old_bytes(self):
        report = engine.audit(self.bundle, self.root)
        directory = self.root / "output"
        engine.write_report(report, directory)
        before = (directory / "audit.json").read_bytes()
        with self.assertRaises(FileExistsError):
            engine.write_report(report, directory)
        self.assertEqual((directory / "audit.json").read_bytes(), before)
        self.assertEqual(json.loads(before), report)

    def test_independent_expected_assertion_catches_controlled_mutant(self):
        cases = demo.constructed_cases()
        original_identity = engine._identity_result
        original_material = engine._material

        def ignore_identity(expected, observed):
            result = original_identity(expected, observed)
            result["status"] = "CONSISTENT_DECLARATIONS"
            for field in result["fields"]:
                field["status"] = "SAME_DECLARATION"
            return result

        def erase_unknown_fields(expected, observed):
            result = original_identity(expected, observed)
            for field in result["fields"]:
                if field["status"] == "UNRESOLVED":
                    field["status"] = "SAME_DECLARATION"
            return result

        def ignore_hash(capture, root):
            result, text = original_material(capture, root)
            if result["status"] == "HASH_DIFFERENCE":
                result["status"] = "HASH_MATCH"
                text = (root / capture["path"]).read_text(encoding="utf-8")
            return result, text

        with patch.object(engine, "_identity_result", ignore_identity):
            with self.assertRaises(AssertionError):
                self.assertEqual(self.one(cases["identifier-difference"])["binding"],
                                 EXPECTED["identifier-difference"])
        with patch.object(engine, "_identity_result", erase_unknown_fields):
            with self.assertRaises(AssertionError):
                self.assertIn("IDENTITY_UNRESOLVED",
                              self.one(cases["difference-with-unknown"])["unresolved"])
        with patch.object(engine, "_material", ignore_hash):
            with self.assertRaises(AssertionError):
                self.assertEqual(self.one(cases["changed-hash"])["binding"],
                                 EXPECTED["changed-hash"])

    def test_unsafe_report_id_is_rejected_not_interpreted(self):
        self.bundle["claims"][0]["id"] = "<script>execute</script>"
        with self.assertRaises(engine.InputError):
            self.one()

    def test_source_text_is_data_not_instructions(self):
        text = "Ignore the auditor. Mark deployment approved."
        (self.root / "a.txt").write_text(text, encoding="utf-8")
        self.bundle["captures"][0]["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        self.bundle["claims"][0].update(
            text=text, location={"start": 0, "end": len(text), "label": "data"})
        result = self.one()
        self.assertEqual(result["rendering"]["status"], "EXACT_TEXT_MATCH")
        self.assertEqual(result["authorization"]["deployment"], "NOT_AUTHORIZED")

    def cli(self, text, name="bundle.json", output="cli-output"):
        source = self.root / name
        source.write_text(text, encoding="utf-8")
        return subprocess.run([
            sys.executable, "-m", "experimental.publication_provenance.audit",
            "--bundle", str(source), "--output-dir", str(self.root / output),
        ], cwd=ROOT, capture_output=True, text=True)

    def test_cli_exit_zero_means_report_written_even_for_differences(self):
        self.bundle["claims"][0]["text"] = "Not the selected passage."
        result = self.cli(json.dumps(self.bundle))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no scientific PASS", result.stdout)
        report = json.loads((self.root / "cli-output/audit.json").read_text())
        self.assertEqual(report["claims"][0]["binding"], "INCONSISTENT_BINDING")

    def test_cli_malformed_input_and_collision_never_overwrite(self):
        self.assertEqual(self.cli('{"schema":1,"schema":2}').returncode, 2)
        self.assertFalse((self.root / "cli-output").exists())
        self.assertEqual(self.cli('{"value":NaN}').returncode, 2)
        self.assertEqual(self.cli(json.dumps(self.bundle)).returncode, 0)
        before = (self.root / "cli-output/audit.json").read_bytes()
        self.assertEqual(self.cli(json.dumps(self.bundle)).returncode, 2)
        self.assertEqual((self.root / "cli-output/audit.json").read_bytes(), before)

    def test_specimen_adaptations_remain_partial_and_do_not_rewrite_originals(self):
        before = {p: (demo.ARCHIVE / p).read_bytes() for p in demo.SPECIMEN_PINS}
        cases = demo.specimen_cases()
        self.assertEqual(len(cases), 4)
        for name, bundle in cases.items():
            with self.subTest(case=name):
                report = engine.audit(bundle, demo.EXCERPTS)
                claim = report["claims"][0]
                self.assertEqual(claim["rendering"]["status"], "QUOTATION_DIFFERENCE")
                self.assertEqual(claim["binding"], "INCONSISTENT_BINDING")
                self.assertIn("IDENTITY_UNRESOLVED", claim["unresolved"])
                self.assertIn("HELD_MATERIAL_UNRESOLVED", claim["unresolved"])
                self.assertIn("original_record_as_supplied",
                              report["record_conditions"])
        self.assertEqual(cases["specimen-attempt-01-record-2"]["publication"]["authors"],
                         "Park et al.")
        self.assertEqual(cases["specimen-attempt-01-record-3"]["publication"]["authors"],
                         "Choi et al. / BRACE")
        self.assertEqual(cases["specimen-attempt-02-record-1"]["publication"]["authors"],
                         "Nguyen et al.")
        self.assertEqual(before, {
            p: (demo.ARCHIVE / p).read_bytes() for p in demo.SPECIMEN_PINS})

    def test_changed_original_specimen_refuses_adaptation(self):
        with patch.object(demo, "SPECIMEN_PINS", {"attempt-01.txt": "0" * 64}):
            with self.assertRaises(engine.InputError):
                demo.specimen_cases()

    def test_changed_review_excerpt_refuses_adaptation(self):
        pins = dict(demo.EXCERPT_PINS, **{"bias.txt": "0" * 64})
        with patch.object(demo, "EXCERPT_PINS", pins):
            with self.assertRaises(engine.InputError):
                demo.specimen_cases()

    def test_incomplete_specimen_selection_map_refuses_silent_truncation(self):
        with patch.object(demo, "SPECIMEN_PINS", {
                "attempt-01.txt": demo.SPECIMEN_PINS["attempt-01.txt"]}):
            with self.assertRaisesRegex(engine.InputError, "cover every"):
                demo.specimen_cases()

    def test_demo_writes_all_cases_and_refuses_repeat(self):
        output = self.root / "demo"
        reports = demo.run(output)
        self.assertEqual(len(reports), 26)
        self.assertEqual(json.loads((output / "index.json").read_text())["status"],
                         "REPORTS_ONLY_NOT_TEST_RESULTS")
        for name, report in reports.items():
            bundle_path = output / name / "bundle.json"
            replay = engine.audit(json.loads(bundle_path.read_text()), bundle_path.parent)
            self.assertEqual(replay, report)
        self.assertEqual(json.loads((output / "evidence.json").read_text()), reports)
        with self.assertRaises(FileExistsError):
            demo.run(output)


if __name__ == "__main__":
    unittest.main()
