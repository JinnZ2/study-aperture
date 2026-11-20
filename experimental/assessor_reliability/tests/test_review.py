"""CONSTRUCTED fixtures only: these tests do not imply human participation."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

# Also runnable by discovery before parent creates the package initializer.
MODULE = Path(__file__).resolve().parents[1] / "review.py"
spec = importlib.util.spec_from_file_location("assessor_reliability_review", MODULE)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


def observations():
    return {"schema": "assessor-reliability/observations/1", "passages": [],
            "explicit_statements": ["Original source observation."], "qualifications": [],
            "omissions": [], "introduced_conditions": [], "limits": ["Constructed fixture."]}


def actor(identity):
    return {"identity": identity, "kind": "CONSTRUCTED", "expertise": ["Test fixture, not a human."],
            "access": ["Source snapshot and anonymous output."],
            "procedure": "Explicit fixture for unit testing only.", "limitations": ["Constructed."]}


def evidence(start=0):
    return [{"source_id": "source-01", "start": start, "end": start + 4, "quote": "Text"}]


def completed(identity="fixture-1", outcome="PASS", finding="qualified", dimensions=None):
    item = review._pending("packet-test", "output")
    item.update({"review_id": "review-" + identity, "status": "COMPLETED", "reviewer": actor(identity),
                 "assessment": {"statement": "Constructed assessment."}, "evidence": evidence(),
                 "reasoning": "Constructed source-grounded reasoning.",
                 "declarations": {"blindness": "DECLARED", "independence": "UNKNOWN",
                                  "cannot_mechanically_prove": True}})
    item["measurements"] = {dimension: {"outcome": outcome, "finding": finding,
                                        "reasoning": "Constructed reasoning.", "evidence": evidence()}
                            for dimension in (dimensions or ["scope"])}
    if outcome == "FAIL":
        item["failures"] = [{"failure_id": "failure-" + identity, "dimension": dimension,
                             "primary": "UNCLASSIFIED", "secondary": ["SCOPE", "INTERPRETATION"],
                             "original_observation": "Original unedited failure description.",
                             "proposed_extension": {"category": "NEW-FIXTURE-CATEGORY",
                                                    "description": "Test taxonomy extension only."}}
                            for dimension in item["measurements"]]
        # Each classified failure must have its own stable identifier.
        for index, failure in enumerate(item["failures"]):
            failure["failure_id"] += "-%d" % index
    return item


def adjudicator(dimensions=("scope",), resolved=False):
    item = actor("constructed-adjudicator")
    item["decisions"] = {dimension: {"status": "RESOLVED" if resolved else "UNRESOLVED",
                                     "reason": "Constructed reason; disagreement preserved.",
                                     "resolution": "narrow" if resolved else None,
                                     "evidence": evidence() if resolved else []}
                         for dimension in dimensions}
    return item


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.battery = self.root / "battery"
        (self.battery / "sources").mkdir(parents=True)
        self.text = "Text: résultats α\nQualification: only the sample.\n"
        data = self.text.encode("utf-8")
        (self.battery / "sources" / "text.txt").write_bytes(data)
        self.case = {"schema": "assessor-reliability/case/1", "case_id": "case-secret",
                     "variant_id": "variant-secret", "family": "expected-family-secret",
                     "purpose": "Expected answer is forbidden-secret", "claim": "A source claim.",
                     "sources": [{"source_id": "source-secret", "path": "sources/text.txt",
                                  "sha256": hashlib.sha256(data).hexdigest(), "available": True,
                                  "version": "v1"}], "observations": observations(),
                     "comparison_spec": {"expected": "comparison-secret"},
                     "perturbation": {"must_change": ["expected-output-secret"]}}
        self.capture = {"schema": "assessor-reliability/capture/1", "run_id": "run-secret",
                        "case_id": "case-secret", "variant_id": "variant-secret",
                        "parsed": {"assessment": {"claims": []}, "evidence": evidence(),
                                   "findings": {"scope": "Narrow"},
                                   "provenance": {"model": {"name": "model-secret"}},
                                   "comparison_spec": "comparison-secret",
                                   "observations": "observation-secret"},
                        "provenance": {"model": {"name": "model-secret", "version": "version-secret"}}}
        self.capture["parsed"]["evidence"][0]["source_id"] = "source-secret"
        self.capture["raw_text"] = json.dumps({**self.capture["parsed"], "run_id": "run-secret"})
        self.capture["raw_sha256"] = hashlib.sha256(self.capture["raw_text"].encode()).hexdigest()

    def generate(self, phase="reference", captures=None, name="packets"):
        output = self.root / name
        manifest = review.make_review_packets([self.case], [self.capture] if captures is None else captures,
                                              output, phase, source_root=self.battery)
        packet = json.loads((output / manifest["packets"][0]["packet_path"]).read_text())
        template = json.loads((output / manifest["packets"][0]["template_path"]).read_text())
        return output, manifest, packet, template

    def test_reference_source_only_no_expected_results(self):
        original = deepcopy(self.case)
        output, manifest, packet, template = self.generate()
        self.assertEqual(packet["sources"][0]["text"], self.text)
        self.assertEqual(packet["sources"][0]["source_id"], "source-01")
        self.assertNotIn("output", packet)
        self.assertEqual(packet["assessment_target"], self.case["claim"])
        public_text = "\n".join(p.read_text() for p in (output / "reviewer").rglob("*.json"))
        for secret in ("case-secret", "variant-secret", "expected-family-secret", "forbidden-secret",
                       "comparison-secret", "expected-output-secret", "model-secret", "run-secret"):
            self.assertNotIn(secret, public_text)
        self.assertEqual(review.validate_review(template), [])
        self.assertIsNone(template["reviewer"]["identity"])
        self.assertEqual(manifest["reviewer_records_created"], 0)
        self.assertEqual(self.case, original)
        private = json.loads((output / "coordinator" / "mapping.json").read_text())
        self.assertEqual(private["mappings"][0]["original_case"], original)
        self.assertIsNone(private["mappings"][0]["original_capture"])
        self.assertEqual((output / "coordinator").stat().st_mode & 0o777, 0o700)

    def test_output_anonymous_raw_parsed_no_expected_or_model(self):
        original = deepcopy(self.capture)
        output, _, packet, _ = self.generate("output")
        public_text = "\n".join(p.read_text() for p in (output / "reviewer").rglob("*.json"))
        for secret in ("case-secret", "variant-secret", "run-secret", "model-secret", "version-secret",
                       "source-secret", "comparison-secret", "observation-secret", "raw_sha256"):
            self.assertNotIn(secret, public_text)
        self.assertEqual(packet["output"]["parsed"]["evidence"][0]["source_id"], "source-01")
        self.assertEqual(packet["output"]["raw"]["status"], "ANONYMIZED_COPY")
        self.assertEqual(packet["sources"][0]["text"], self.text)
        private = json.loads((output / "coordinator" / "mapping.json").read_text())
        self.assertEqual(private["mappings"][0]["original_capture"], original)
        self.assertEqual(self.capture, original)

    def test_missing_raw_is_not_fabricated(self):
        self.capture.pop("raw_text")
        _, _, packet, _ = self.generate("output")
        self.assertEqual(packet["output"]["raw"]["status"], "NOT_PROVIDED")
        self.assertIsNone(packet["output"]["raw"]["text"])

    def test_unparseable_raw_redacted_and_unsafe_metadata_withheld(self):
        self.capture["raw_text"] = "NOT JSON model-secret source-secret"
        self.capture.pop("raw_sha256")
        _, _, packet, _ = self.generate("output")
        self.assertEqual(packet["output"]["raw"]["text"], "NOT JSON [MODEL] source-01")
        self.capture["raw_text"] = '{"comparison_spec": "answer", BROKEN'
        _, _, packet, _ = self.generate("output", name="second")
        self.assertEqual(packet["output"]["raw"]["status"], "WITHHELD_FOR_BLINDNESS")

    def test_missing_source_not_read_or_treated_as_corruption(self):
        self.case["sources"][0].update({"available": False, "sha256": "UNDECLARED",
                                         "path": "../../no-read"})
        manifest = review.make_review_packets([self.case], [], self.root / "missing")
        packet = json.loads((self.root / "missing" / manifest["packets"][0]["packet_path"]).read_text())
        self.assertIsNone(packet["sources"][0]["text"])
        self.assertFalse(packet["sources"][0]["available"])

    def test_root_required_and_fresh_directory(self):
        output = self.root / "packets"
        with self.assertRaisesRegex(ValueError, "source_root"):
            review.make_review_packets([self.case], [], output)
        self.assertFalse(output.exists())
        self.generate()
        before = sorted(p.relative_to(output).as_posix() for p in output.rglob("*"))
        with self.assertRaises(FileExistsError):
            review.make_review_packets([self.case], [], output, source_root=self.battery)
        self.assertEqual(before, sorted(p.relative_to(output).as_posix() for p in output.rglob("*")))

    def test_duplicate_and_invalid_ids_rejected_before_output(self):
        for cases, captures in (([self.case, self.case], []), ([self.case], [self.capture, self.capture])):
            with self.subTest(cases=len(cases), captures=len(captures)):
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    review.make_review_packets(cases, captures, self.root / "invalid", source_root=self.battery)
        self.case["case_id"] = "../unsafe"
        with self.assertRaises(ValueError):
            self.generate()
        self.assertFalse((self.root / "packets").exists())

    def test_unknown_capture_duplicate_source_and_phase(self):
        self.capture["variant_id"] = "unmatched"
        with self.assertRaisesRegex(ValueError, "match"):
            self.generate("output")
        self.capture["variant_id"] = self.case["variant_id"]
        self.case["sources"].append(deepcopy(self.case["sources"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate source"):
            self.generate()
        with self.assertRaisesRegex(ValueError, "phase"):
            review.make_review_packets([], [], self.root / "bad", "all")

    def test_hash_utf8_path_and_symlink_controls(self):
        source = self.case["sources"][0]
        original = deepcopy(source)
        source["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            self.generate()
        source.update(original)
        for path in ("../outside.txt", "/tmp/outside.txt", "sources\\text.txt"):
            source["path"] = path
            with self.assertRaises(ValueError):
                self.generate()
        external = self.root / "outside.txt"
        external.write_text(self.text)
        (self.battery / "escape.txt").symlink_to(external)
        source["path"] = "escape.txt"
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.generate()
        source.update(original)
        (self.battery / source["path"]).write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            self.generate()
        self.assertFalse((self.root / "packets").exists())

    def test_raw_hash_mismatch_rejected(self):
        self.capture["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Raw text hash"):
            self.generate("output")

    def test_known_model_in_source_defeats_blindness_without_altering_source(self):
        data = b"Text by model-secret"
        (self.battery / "sources" / "text.txt").write_bytes(data)
        self.case["sources"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        with self.assertRaisesRegex(ValueError, "blindness unsafe"):
            self.generate("output")
        self.assertFalse((self.root / "packets").exists())

    def test_random_packet_identifiers_not_stable_model_ids(self):
        _, first, _, _ = self.generate(name="first")
        _, second, _, _ = self.generate(name="second")
        self.assertNotEqual(first["packets"][0]["packet_id"], second["packets"][0]["packet_id"])

    def test_invalid_provenance_and_source_metadata_rejected(self):
        self.capture["provenance"] = None
        with self.assertRaisesRegex(ValueError, "provenance/model"):
            self.generate("output")
        self.capture["provenance"] = {}
        self.case["sources"][0]["version"] = {"comparison_spec": "hidden"}
        with self.assertRaisesRegex(ValueError, "version"):
            self.generate()

    def test_redacted_key_collisions_are_not_silently_overwritten(self):
        self.capture["parsed"] = {"run-secret": 1, "[RUN]": 2}
        with self.assertRaisesRegex(ValueError, "duplicate object keys"):
            self.generate("output")

    def test_expected_prefix_and_other_reviews_hidden(self):
        self.capture["parsed"].update({"expected_unusual_dimension": "secret-answer",
                                       "reviews": [{"identity": "other-reviewer"}]})
        self.capture["raw_text"] = json.dumps(self.capture["parsed"])
        self.capture.pop("raw_sha256")
        _, _, packet, _ = self.generate("output")
        text = json.dumps(packet)
        self.assertNotIn("secret-answer", text)
        self.assertNotIn("other-reviewer", text)

    def test_generic_model_version_variant_and_run_do_not_rewrite_evidence(self):
        text = "Text: database sample has 10 participants at version 1.\n"
        data = text.encode("utf-8")
        (self.battery / "sources" / "text.txt").write_bytes(data)
        self.case["sources"][0].update({"sha256": hashlib.sha256(data).hexdigest(), "version": "1"})
        self.case["variant_id"] = "base"
        self.case["claim"] = "The database sample has 10 participants."
        self.capture.update({"variant_id": "base", "run_id": "1"})
        self.capture["provenance"]["model"] = {"name": "CONSTRUCTED_FIXTURE", "version": "1"}
        passage = {"source_id": "source-secret", "start": 0, "end": len(text), "quote": text}
        self.capture["parsed"] = {"evidence": [passage], "findings": {"statement": "database 10"},
                                   "provenance": {"model": {"name": "CONSTRUCTED_FIXTURE", "version": "1"}}}
        self.capture["raw_text"] = json.dumps(self.capture["parsed"])
        self.capture.pop("raw_sha256")
        _, _, packet, _ = self.generate("output")
        self.assertEqual(packet["sources"][0]["text"], text)
        self.assertEqual(packet["sources"][0]["version"], "1")
        self.assertEqual(packet["assessment_target"], self.case["claim"])
        self.assertEqual(packet["output"]["parsed"]["evidence"][0]["quote"], text)
        self.assertIn("database 10", packet["output"]["raw"]["text"])
        self.assertNotIn("CONSTRUCTED_FIXTURE", json.dumps(packet))

    def test_generic_source_identifier_aliased_structurally_not_in_quotes(self):
        self.case["sources"][0]["source_id"] = "1"
        self.capture["parsed"] = {"evidence": [{"source_id": "1", "start": 0, "end": 2, "quote": "10"}]}
        self.capture["raw_text"] = json.dumps(self.capture["parsed"])
        self.capture.pop("raw_sha256")
        _, _, packet, _ = self.generate("output")
        self.assertEqual(packet["output"]["parsed"]["evidence"][0]["source_id"], "source-01")
        self.assertEqual(packet["output"]["parsed"]["evidence"][0]["quote"], "10")

    def test_retrieved_material_output_review_explicitly_unsupported(self):
        self.capture["provenance"]["retrieved_material"] = [{"source_id": "retrieved-1"}]
        with self.assertRaisesRegex(ValueError, "Unsupported staged retrieval-review"):
            self.generate("output")
        self.assertFalse((self.root / "packets").exists())
        # Reference phase supplies no AI outputs or retrieval exposure.
        _, _, packet, _ = self.generate("reference")
        self.assertNotIn("output", packet)


class ValidationTests(unittest.TestCase):
    def test_valid_completed_constructed_record(self):
        self.assertEqual(review.validate_review(completed()), [])
        self.assertEqual(review.validate_review(completed(outcome="FAIL")), [])

    def test_pending_does_not_pose_as_reviewer(self):
        item = review._pending("packet-test", "reference")
        self.assertEqual(review.validate_review(item), [])
        item["reviewer"] = actor("fake-human")
        item["reviewer"]["kind"] = "HUMAN"
        self.assertTrue(review.validate_review(item))

    def test_required_actor_reasoning_uncertainty_measurement(self):
        for key in ("identity", "kind", "expertise", "access", "procedure", "limitations"):
            item = completed()
            item["reviewer"].pop(key)
            with self.subTest(actor_field=key):
                self.assertTrue(review.validate_review(item))
        for key in ("evidence", "reasoning", "uncertainties", "disagreements", "measurements", "assessment", "declarations"):
            item = completed()
            item.pop(key)
            with self.subTest(review_field=key):
                self.assertTrue(review.validate_review(item))
        item = completed()
        item["reviewer"]["identity"] = "UNKNOWN"
        self.assertTrue(review.validate_review(item))

    def test_failure_observation_taxonomy_extension_and_duplicates(self):
        for key in ("primary", "secondary", "original_observation", "proposed_extension", "dimension", "failure_id"):
            item = completed(outcome="FAIL")
            item["failures"][0].pop(key)
            with self.subTest(field=key):
                self.assertTrue(review.validate_review(item))
        item = completed(outcome="FAIL")
        item["failures"].append(deepcopy(item["failures"][0]))
        self.assertTrue(any("duplicate failure_id" in error for error in review.validate_review(item)))
        item = completed(outcome="FAIL")
        item["failures"][0]["primary"] = "FORCED-CATEGORY"
        self.assertTrue(review.validate_review(item))
        item["failures"][0]["primary"] = "UNCLASSIFIED"
        item["failures"][0]["proposed_extension"] = None
        self.assertEqual(review.validate_review(item), [])

    def test_outcomes_evidence_offsets_and_fail_classification(self):
        for value in ("GOOD", None, [], {}):
            item = completed()
            item["measurements"]["scope"]["outcome"] = value
            self.assertTrue(review.validate_review(item))
        for value in (-1, 0.5, True):
            item = completed()
            item["evidence"][0]["start"] = value
            self.assertTrue(review.validate_review(item))
        item = completed()
        item["measurements"]["scope"]["evidence"] = []
        self.assertTrue(review.validate_review(item))
        item = completed(outcome="FAIL")
        item["failures"] = []
        self.assertTrue(review.validate_review(item))

    def test_not_assessed_and_unscorable_no_false_pass(self):
        for outcome in ("NOT_ASSESSED", "UNSCORABLE"):
            item = completed(outcome=outcome, finding=None)
            item["measurements"]["scope"]["evidence"] = []
            self.assertEqual(review.validate_review(item), [])

    def test_nonfinite_and_non_json_objects_rejected(self):
        item = completed()
        item["assessment"]["number"] = float("nan")
        self.assertTrue(review.validate_review(item))
        item["assessment"]["number"] = Path("unsafe")
        self.assertTrue(review.validate_review(item))
        self.assertTrue(review.validate_review(None))


class AdjudicationTests(unittest.TestCase):
    def test_disagreement_preserved_even_when_adjudicator_resolves(self):
        records = [completed("one"), completed("two", "FAIL", "broadened")]
        original = deepcopy(records)
        source = observations()
        output = review.adjudicate(source, records, adjudicator(resolved=True))
        self.assertEqual(output["dimensions"]["scope"]["status"], "DISAGREEMENT")
        self.assertTrue(output["dimensions"]["scope"]["unresolved"])
        self.assertEqual(output["adjudication"]["decisions"]["scope"]["status"], "RESOLVED")
        self.assertEqual(output["source_observations"], source)
        self.assertEqual(output["reviewer_assessments"], original)
        self.assertTrue(output["constructed_participants_present"])
        output["reviewer_assessments"][0]["reasoning"] = "Changed output only"
        self.assertEqual(records, original)

    def test_exact_agreement_evidence_difference_and_unresolved(self):
        records = [completed("one"), completed("two")]
        output = review.adjudicate(observations(), records, adjudicator())
        self.assertEqual(output["dimensions"]["scope"]["status"], "AGREEMENT")
        records[1]["measurements"]["scope"]["evidence"] = evidence(3)
        output = review.adjudicate(observations(), records, adjudicator())
        self.assertEqual(output["dimensions"]["scope"]["status"], "DISAGREEMENT")
        records[1]["measurements"]["scope"]["evidence"] = evidence()
        records[1]["uncertainties"] = ["Cannot establish independent scope."]
        output = review.adjudicate(observations(), records, adjudicator())
        self.assertEqual(output["dimensions"]["scope"]["status"], "UNRESOLVED")

    def test_single_reviewer_missing_dimension_and_unscorable_unresolved(self):
        output = review.adjudicate(observations(), [completed()], adjudicator())
        self.assertEqual(output["dimensions"]["scope"]["status"], "UNRESOLVED")
        records = [completed("one"), completed("two", dimensions=["origin"])]
        output = review.adjudicate(observations(), records, adjudicator(("scope", "origin")))
        self.assertEqual(output["dimensions"]["scope"]["missing_review_ids"], ["review-two"])
        self.assertEqual(output["dimensions"]["scope"]["status"], "UNRESOLVED")
        records = [completed("one", "UNSCORABLE", None), completed("two", "UNSCORABLE", None)]
        output = review.adjudicate(observations(), records, adjudicator())
        self.assertEqual(output["dimensions"]["scope"]["status"], "UNRESOLVED")

    def test_no_empty_pending_duplicate_or_unprovided_reviews(self):
        pending = review._pending("packet-test", "output")
        for records in ([], [{}], [pending], [completed(), completed()]):
            with self.subTest(records=len(records)):
                with self.assertRaises(ValueError):
                    review.adjudicate(observations(), records, adjudicator())
        second = completed()
        second["review_id"] = "new-review-id"
        with self.assertRaisesRegex(ValueError, "Duplicate reviewer identity"):
            review.adjudicate(observations(), [completed(), second], adjudicator())

    def test_adjudicator_explicit_decisions_and_provenance_required(self):
        for field in ("identity", "access", "procedure", "limitations", "expertise", "decisions"):
            item = adjudicator()
            item.pop(field)
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    review.adjudicate(observations(), [completed()], item)
        item = adjudicator(resolved=True)
        item["decisions"]["scope"]["evidence"] = []
        with self.assertRaises(ValueError):
            review.adjudicate(observations(), [completed()], item)
        with self.assertRaises(ValueError):
            review.adjudicate({}, [completed()], adjudicator())
        second = completed("two")
        second["packet_id"] = "packet-other"
        with self.assertRaisesRegex(ValueError, "same packet"):
            review.adjudicate(observations(), [completed(), second], adjudicator())


class SummaryTests(unittest.TestCase):
    def test_raw_counts_denominators_missing_and_pending(self):
        records = [completed("pass"), completed("fail", "FAIL"),
                   completed("unscorable", "UNSCORABLE", None),
                   completed("unassessed", "NOT_ASSESSED", None),
                   completed("missing", dimensions=["origin"]),
                   review._pending("packet-pending", "output")]
        report = review.summarize_reviews(records)
        self.assertEqual(report["completed_records"], 5)
        self.assertEqual(report["pending_templates"], 1)
        self.assertEqual(report["participant_kinds"], {"CONSTRUCTED": 5})
        measure = report["measurements"]["scope"]
        self.assertEqual([measure[key] for key in review.OUTCOMES], [1, 1, 1, 2])
        self.assertEqual(measure["denominator"], 5)
        self.assertEqual(measure["scorable_denominator"], 2)
        self.assertEqual(measure["missing_count"], 1)
        self.assertEqual(measure["finding_prevalence_denominator"], 4)
        self.assertEqual(sum(measure["finding_prevalence"].values()), 4)
        classification = report["failure_classification"]
        self.assertEqual(classification["primary_counts"], {"UNCLASSIFIED": 1})
        self.assertEqual(classification["primary_denominator"], 1)
        self.assertEqual(classification["secondary_denominator"], 2)
        self.assertEqual(classification["entries"][0]["failure"]["original_observation"],
                         "Original unedited failure description.")
        self.assertNotIn("score", report)

    def test_empty_and_pending_only_never_fabricate_results(self):
        for records in ([], [review._pending("packet-empty", "reference")]):
            report = review.summarize_reviews(records)
            self.assertEqual(report["completed_records"], 0)
            self.assertEqual(report["measurements"], {})
            self.assertEqual(report["completed_participant_identities"], 0)

    def test_agreement_kept_within_packet(self):
        first, second = completed("one"), completed("two", "FAIL")
        second["packet_id"] = "packet-other"
        report = review.summarize_reviews([first, second])
        self.assertEqual(len(report["within_packet_comparisons"]), 2)
        self.assertTrue(all(group["dimensions"]["scope"]["status"] == "UNRESOLVED"
                            for group in report["within_packet_comparisons"]))

    def test_duplicates_rejected_and_inputs_not_mutated(self):
        item = completed()
        original = deepcopy(item)
        review.summarize_reviews([item])
        self.assertEqual(item, original)
        with self.assertRaisesRegex(ValueError, "Duplicate review_id"):
            review.summarize_reviews([item, item])


if __name__ == "__main__":
    unittest.main()
