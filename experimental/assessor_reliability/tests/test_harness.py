"""CC0. Constructed controls for capture/freeze, not model reliability."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from experimental.assessor_reliability.common import dump_json, safe_path, sha256_bytes, strict_json, strict_load
from experimental.assessor_reliability import harness


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.battery_root = self.root / "battery"
        self.battery_root.mkdir()
        text = "α sample. If water is below 10 C, the device switches off.\n"
        (self.battery_root / "source.txt").write_text(text)
        self.case = {"schema": "assessor-reliability/case/1", "case_id": "conditional", "variant_id": "base",
                     "family": "Conditional claim", "purpose": "Constructed qualification control",
                     "claim": text[10:-1], "sources": [{"source_id": "S1", "path": "source.txt",
                     "sha256": sha256_bytes(text.encode()), "version": "v1", "available": True}],
                     "observations": {"schema": "assessor-reliability/observations/1", "passages": []},
                     "comparison_spec": {"fields": ["findings.uncertainty_state"], "material_fields": []}, "perturbation": None}
        dump_json(self.battery_root / "cases.json", {"schema": "assessor-reliability/battery/1", "constructed": True, "cases": [self.case]})
        self.freeze = self.root / "freeze"
        harness.freeze_battery(self.freeze, self.battery_root / "cases.json")
        self.prompt = harness.prompt_for(self.case, self.battery_root, self.freeze)
        start = text.index("If")
        self.output = {"assessment": {"schema": "study-aperture/1", "title": "Constructed source", "pub_type": "COMMENTARY",
            "citation": "S1", "materials": "Supplied synthetic source", "decision_context": "UNDECLARED",
            "claims": [{"id": "C1", "text": text[start:-1], "evidence_location": "S1:" + str(start), "support": "UNDETERMINED"}],
            "tools": [], "decisions": [{"id": "D1", "text": "Whether to act", "state": "UNRESOLVED"}], "notes": "UNDECLARED"},
            "evidence": [{"claim_id": "C1", "source_id": "S1", "start": start, "end": len(text)-1,
                          "quote": text[start:-1], "rendering": "QUOTATION", "origin": "SUPPLIED",
                          "transformation": "Verbatim extraction", "justification": "Exact supplied span"}],
            "findings": {key: "UNDECLARED" for key in harness.REQUIRED_FINDINGS},
            "provenance": {"unavailable_information": [], "assessor_prior": "UNKNOWN_ORIGIN"}}
        self.metadata = {"constructed": True, "model": {"name": "CONSTRUCTED_FIXTURE", "version": "1"},
                         "environment": {"identifier": "test"}, "assessment_date": "CONSTRUCTED_DATE",
                         "tools": [], "retrieved_material": [], "actual_prompt_sha256": self.prompt["sha256"],
                         "execution": {"errors": [], "retries": 0, "truncated": False, "incomplete": False}}

    def run_capture(self, output=None, raw=None, metadata=None, name="run"):
        raw_path = self.root / (name + ".bin")
        raw_path.write_bytes(raw if raw is not None else json.dumps(output or self.output, ensure_ascii=False).encode())
        return harness.capture(raw_path, self.case, self.battery_root, self.freeze, metadata or self.metadata, self.root / name, name)

    def test_valid_but_incomplete_is_not_failed(self):
        capture = self.run_capture()
        self.assertTrue(capture["validation"]["schema_valid"])
        self.assertTrue(capture["validation"]["incompleteness"])
        self.assertEqual(capture["mechanical"]["dimensions"]["quote_fidelity"]["PASS"], 1)
        self.assertEqual(capture["semantic_review"]["interpretation"], "NOT_ASSESSED")
        self.assertEqual(harness.read_capture(self.root / "run/capture.json"), capture)

    def test_raw_bytes_before_invalid_json(self):
        raw = b'{"assessment": 1, "assessment": 2}'
        capture = self.run_capture(raw=raw)
        self.assertEqual((self.root / "run/raw.bin").read_bytes(), raw)
        self.assertTrue(capture["parse_errors"])
        self.assertFalse(capture["validation"]["schema_valid"])

    def test_missing_field_not_defaulted(self):
        output = copy.deepcopy(self.output)
        del output["assessment"]["materials"]
        capture = self.run_capture(output)
        self.assertIn("assessment.materials", capture["validation"]["missing_fields"])
        self.assertNotIn("materials", capture["parsed"]["assessment"])

    def test_fabricated_quote_separate_from_valid_structure(self):
        output = copy.deepcopy(self.output)
        output["evidence"][0]["quote"] = "The device always switches off."
        capture = self.run_capture(output)
        self.assertTrue(capture["validation"]["schema_valid"])
        self.assertEqual(capture["mechanical"]["dimensions"]["quote_fidelity"]["FAIL"], 1)

    def test_boolean_offset_and_unhashable_source_do_not_crash(self):
        output = copy.deepcopy(self.output)
        output["evidence"][0]["start"] = True
        output["evidence"][0]["source_id"] = []
        output["evidence"][0]["claim_id"] = []
        capture = self.run_capture(output)
        self.assertFalse(capture["validation"]["schema_valid"])
        self.assertEqual(capture["mechanical"]["dimensions"]["source_identification"]["FAIL"], 1)

    def test_missing_source_explicit_not_invented(self):
        case = copy.deepcopy(self.case)
        case["sources"][0]["available"] = False
        case["sources"][0]["sha256"] = "UNDECLARED"
        materials = harness.source_material(case, self.root / "nonexistent")
        self.assertIsNone(materials[0]["text"])
        report = harness.check_evidence(self.output, materials)
        self.assertEqual(report["dimensions"]["passage_location"]["UNSCORABLE"], 1)

    def test_source_change_pauses_raw_is_preserved(self):
        (self.battery_root / "source.txt").write_text("changed")
        with self.assertRaisesRegex(ValueError, "hash/version"):
            self.run_capture()
        self.assertTrue((self.root / "run/raw.bin").is_file())
        self.assertEqual(strict_load(self.root / "run/execution-error.json")["status"], "PAUSED")

    def test_scoring_dependency_change_pauses(self):
        self.case["comparison_spec"]["fields"] = ["new.rule"]
        with self.assertRaisesRegex(ValueError, "scoring dependencies"):
            harness.prompt_for(self.case, self.battery_root, self.freeze)

    def test_wrong_actual_prompt_preserves_attempt(self):
        self.metadata["actual_prompt_sha256"] = "wrong"
        with self.assertRaisesRegex(ValueError, "actual prompt"):
            self.run_capture()
        self.assertTrue((self.root / "run/receipt.json").is_file())

    def test_output_directory_never_overwritten(self):
        self.run_capture()
        before = (self.root / "run/raw.bin").read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_capture(raw=b"different")
        self.assertEqual((self.root / "run/raw.bin").read_bytes(), before)

    def test_tampered_capture_rejected(self):
        self.run_capture()
        (self.root / "run/capture.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "artifact hash"):
            harness.read_capture(self.root / "run/capture.json")

    def test_frozen_core_tampering_rejected(self):
        (self.freeze / "method/assess.py").write_text("raise RuntimeError('do not execute')")
        with self.assertRaisesRegex(ValueError, "frozen bytes"):
            harness.verify_freeze(self.freeze)

    def test_paraphrase_not_automatically_passed(self):
        output = copy.deepcopy(self.output)
        output["evidence"][0]["rendering"] = "PARAPHRASE"
        capture = self.run_capture(output)
        self.assertEqual(capture["mechanical"]["dimensions"]["quote_fidelity"]["NOT_ASSESSED"], 1)

    def test_empty_evidence_denominator_zero(self):
        output = copy.deepcopy(self.output)
        output["evidence"] = []
        capture = self.run_capture(output)
        self.assertEqual(capture["mechanical"]["dimensions"]["quote_fidelity"]["denominator"], 0)

    def test_no_reference_payload_leak(self):
        self.assertNotIn('"observations":', self.prompt["text"])
        self.assertNotIn('"comparison_spec":', self.prompt["text"])
        self.assertNotIn('"perturbation":', self.prompt["text"])

    def test_no_nonfinite_json_or_duplicate_keys(self):
        for text in ('{"x":NaN}', '{"x":1,"x":2}'):
            with self.assertRaises(ValueError):
                strict_json(text)

    def test_no_path_escape_or_symlink_escape(self):
        for path in ("../other", "/tmp/source.txt"):
            with self.assertRaises(ValueError):
                safe_path(self.root, path)
        (self.root / "outside").symlink_to("/tmp")
        with self.assertRaises(ValueError):
            safe_path(self.root, "outside/text")


if __name__ == "__main__":
    unittest.main()
