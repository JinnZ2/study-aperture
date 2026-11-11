"""Tests of CONSTRUCTED controls, not measurements of AI or reviewer behavior."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load just the owned module: no reliance on unfinished shared harness imports.
battery = _load("assessor_reliability_battery_test_target", ROOT / "experimental/assessor_reliability/battery.py")
production = _load("assessor_reliability_battery_production_validator", ROOT / "assess.py")


def _field(obj, path):
    for key in path.split("."):
        if not isinstance(obj, dict) or key not in obj:
            return {"$missing": True}
        obj = obj[key]
    return obj


class BatteryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "bundle"
        self.bundle = battery.build_battery(self.root)
        self.cases = self.bundle["cases"]
        self.bases = {c["family"]: c for c in self.cases if c["perturbation"] is None}
        self.variants = {c["perturbation"]["kind"]: c for c in self.cases if c["perturbation"] is not None}

    def test_inventory_is_exactly_fifteen_bases_and_ten_variants(self):
        self.assertEqual(self.bundle["schema"], "assessor-reliability/battery/1")
        self.assertIs(self.bundle["constructed"], True)
        self.assertEqual(len(self.cases), 25)
        self.assertEqual(set(self.bases), set(battery.FAMILIES))
        self.assertEqual(set(self.variants), set(battery.PERTURBATION_TYPES))
        self.assertEqual(len({(c["case_id"], c["variant_id"]) for c in self.cases}), 25)
        variables = self.bundle["design_variables"]
        self.assertEqual(variables["base_case_count"], 15)
        self.assertEqual(variables["perturbation_case_count"], 10)
        self.assertEqual(variables["repeat_count"], "UNDECLARED")
        self.assertEqual(variables["reviewer_count"], "UNDECLARED")
        self.assertEqual(variables["model_versions"], "UNDECLARED")

    def test_case_and_observation_contract_keys(self):
        required_case = {"schema", "case_id", "variant_id", "family", "purpose", "claim",
                         "sources", "observations", "comparison_spec", "perturbation"}
        required_observations = {"schema", "passages", "explicit_statements", "qualifications",
                                 "omissions", "introduced_conditions", "limits"}
        for case in self.cases:
            with self.subTest(case=case["case_id"], variant=case["variant_id"]):
                self.assertEqual(set(case), required_case)
                self.assertEqual(case["schema"], battery.CASE_SCHEMA)
                self.assertEqual(set(case["observations"]), required_observations)
                self.assertEqual(case["observations"]["schema"], battery.OBSERVATIONS_SCHEMA)
                self.assertIn("CONSTRUCTED", case["purpose"])
                self.assertTrue(case["observations"]["limits"])
                for source in case["sources"]:
                    self.assertEqual(set(source), {"source_id", "path", "sha256", "version", "available"})

    def test_json_is_portable_full_manifest_and_matches_return(self):
        data = (self.root / "cases.json").read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertEqual(json.loads(data.decode("utf-8", errors="strict")), self.bundle)
        self.assertNotIn(str(self.root), data.decode("utf-8"))
        for case in self.cases:
            for source in case["sources"]:
                path = Path(source["path"])
                self.assertFalse(path.is_absolute())
                self.assertNotIn("..", path.parts)
                self.assertEqual(path.parts[0], "sources")

    def test_generation_is_deterministic_across_destinations(self):
        other = Path(self.temp.name) / "other"
        second = battery.build_battery(other)
        self.assertEqual(self.bundle, second)
        first_files = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        second_files = {str(p.relative_to(other)): p.read_bytes() for p in other.rglob("*") if p.is_file()}
        self.assertEqual(first_files, second_files)

    def test_existing_output_is_refused_without_mutation(self):
        before = (self.root / "cases.json").read_bytes()
        with self.assertRaises(FileExistsError):
            battery.build_battery(self.root)
        self.assertEqual((self.root / "cases.json").read_bytes(), before)
        empty = Path(self.temp.name) / "empty"
        empty.mkdir()
        with self.assertRaises(FileExistsError):
            battery.build_battery(empty)
        self.assertEqual(list(empty.iterdir()), [])
        file = Path(self.temp.name) / "file"
        file.write_text("preserve", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            battery.build_battery(file)
        self.assertEqual(file.read_text(encoding="utf-8"), "preserve")

    def test_output_symlinks_are_refused_even_when_dangling(self):
        for target in (self.root, Path(self.temp.name) / "not-created"):
            link = Path(self.temp.name) / ("link-" + target.name)
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(FileExistsError):
                battery.build_battery(link)
        self.assertFalse((Path(self.temp.name) / "not-created").exists())

    def test_source_bytes_are_hash_bound_and_locations_are_unicode(self):
        found_nonbyte_offset = False
        for case in self.cases:
            sources = {s["source_id"]: s for s in case["sources"]}
            for source in sources.values():
                if source["available"]:
                    data = (self.root / source["path"]).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])
                    self.assertTrue(data.endswith(b"\n"))
            for passage in case["observations"]["passages"]:
                self.assertEqual(set(passage), {"source_id", "start", "end", "quote", "label"})
                source = sources[passage["source_id"]]
                self.assertIs(source["available"], True)
                text = (self.root / source["path"]).read_bytes().decode("utf-8", errors="strict")
                start, end = passage["start"], passage["end"]
                self.assertGreaterEqual(start, 0)
                self.assertGreater(end, start)
                self.assertLessEqual(end, len(text))
                self.assertEqual(text[start:end], passage["quote"])
                if len(text[:start].encode("utf-8")) != start:
                    found_nonbyte_offset = True
        self.assertTrue(found_nonbyte_offset, "Unicode controls must detect accidental byte indexing")

    def test_missing_source_is_explicit_and_never_created(self):
        case = self.bases["missing_source"]
        missing = [s for s in case["sources"] if not s["available"]]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["source_id"], "MISSING")
        self.assertEqual(missing[0]["sha256"], "UNDECLARED")
        self.assertFalse((self.root / missing[0]["path"]).exists())
        self.assertFalse(any(p["source_id"] == "MISSING" for p in case["observations"]["passages"]))
        declared = {s["path"] for c in self.cases for s in c["sources"] if s["available"]}
        actual = {str(p.relative_to(self.root)) for p in (self.root / "sources").iterdir()}
        self.assertEqual(actual, declared)

    def test_dependencies_are_predeclared_disjoint_and_reference_real_bases(self):
        case_by_key = {(c["case_id"], c["variant_id"]): c for c in self.cases}
        required = {"base_case_id", "base_variant_id", "kind", "may_change", "must_change",
                    "invariant", "unresolved_when", "justification", "limits"}
        for kind, variant in self.variants.items():
            with self.subTest(kind=kind):
                spec = variant["perturbation"]
                self.assertEqual(set(spec), required)
                base = case_by_key[(spec["base_case_id"], spec["base_variant_id"])]
                self.assertIsNone(base["perturbation"])
                self.assertEqual(base["case_id"], variant["case_id"])
                may, must, invariant = (set(spec[k]) for k in ("may_change", "must_change", "invariant"))
                self.assertTrue(must)
                self.assertLessEqual(must, may)
                self.assertFalse(may & invariant)
                self.assertEqual(may | invariant, set(battery.COMPARISON_FIELDS))
                self.assertTrue(spec["unresolved_when"])
                self.assertTrue(spec["justification"])
                self.assertTrue(spec["limits"])
                self.assertNotEqual(base["sources"], variant["sources"])

    def test_fixture_changes_follow_declared_dependencies_only(self):
        # This is an implementation consistency check, not semantic adjudication.
        for kind, variant in self.variants.items():
            with self.subTest(kind=kind):
                spec = variant["perturbation"]
                base = self.bases[variant["family"]]
                left = battery.constructed_response(base)
                right = battery.constructed_response(variant)
                for field in spec["must_change"]:
                    self.assertNotEqual(_field(left, field), _field(right, field), field)
                for field in spec["invariant"]:
                    self.assertEqual(_field(left, field), _field(right, field), field)

    def test_relevant_addition_preserves_existing_passages_and_adds_count(self):
        base = self.bases["evidence_perturbation"]["observations"]["passages"]
        variant = self.variants["relevant_addition"]["observations"]["passages"]
        self.assertEqual(variant[:-1], base)
        self.assertEqual(variant[-1]["label"], "support")
        self.assertEqual(variant[-1]["quote"], battery.CLAIM)
        self.assertGreater(variant[-1]["start"], base[-1]["end"])

    def test_location_displacement_preserves_wording_but_moves_spans(self):
        left = self.bases["clear_evidence"]["observations"]["passages"]
        right = self.variants["location_displacement"]["observations"]["passages"]
        self.assertEqual([p["quote"] for p in left], [p["quote"] for p in right])
        for a, b in zip(left, right):
            self.assertGreater(b["start"], a["start"])
            self.assertEqual(b["end"] - b["start"], a["end"] - a["start"])

    def test_metadata_change_has_new_hash_version_but_same_passage_locations(self):
        base, variant = self.bases["clear_evidence"], self.variants["metadata_change"]
        self.assertEqual(base["observations"]["passages"], variant["observations"]["passages"])
        self.assertNotEqual(base["sources"][0]["sha256"], variant["sources"][0]["sha256"])
        self.assertNotEqual(base["sources"][0]["version"], variant["sources"][0]["version"])

    def test_formatting_preserves_all_passage_wording(self):
        base, variant = self.bases["irrelevant_perturbation"], self.variants["irrelevant_formatting_change"]
        self.assertEqual([p["quote"] for p in base["observations"]["passages"]],
                         [p["quote"] for p in variant["observations"]["passages"]])
        self.assertNotEqual(base["observations"]["passages"], variant["observations"]["passages"])

    def test_repeated_control_package_is_not_a_fabricated_run(self):
        case = self.bases["repeated_assessment"]
        self.assertNotIn("run_id", case)
        self.assertEqual(battery.constructed_response(case), battery.constructed_response(case))
        self.assertEqual(self.bundle["design_variables"]["repeat_count"], "UNDECLARED")

    def test_both_fixture_modes_keep_unchanged_valid_production_record_shape(self):
        expected_envelope = {"assessment", "evidence", "findings", "provenance"}
        expected_record = {"schema", "title", "pub_type", "citation", "materials", "decision_context",
                           "claims", "tools", "decisions", "notes"}
        for case in self.cases:
            for mode in ("faithful", "faulty"):
                with self.subTest(case=case["case_id"], variant=case["variant_id"], mode=mode):
                    result = battery.constructed_response(case, mode)
                    self.assertEqual(set(result), expected_envelope)
                    self.assertEqual(set(result["assessment"]), expected_record)
                    self.assertEqual(result["assessment"]["schema"], "study-aperture/1")
                    self.assertEqual(production.check(result["assessment"]), [])
                    self.assertTrue(production.incompleteness(result["assessment"]))
                    self.assertEqual(result["assessment"]["tools"], [])
                    self.assertIn("CONSTRUCTED", result["assessment"]["notes"])
                    self.assertEqual(result["provenance"]["assessor_prior"], "CONSTRUCTED_FIXTURE_NO_MODEL_OR_PRIOR_KNOWLEDGE")
                    self.assertEqual(set(result["findings"]), {p.split(".")[1] for p in battery.FINDING_FIELDS})

    def test_faithful_evidence_copies_current_source_text_exactly(self):
        for case in self.cases:
            sources = {s["source_id"]: s for s in case["sources"]}
            for evidence in battery.constructed_response(case)["evidence"]:
                source = sources[evidence["source_id"]]
                self.assertTrue(source["available"])
                text = (self.root / source["path"]).read_text(encoding="utf-8")
                self.assertEqual(text[evidence["start"]:evidence["end"]], evidence["quote"])
                self.assertEqual(evidence["origin"], "SUPPLIED")
                self.assertEqual(evidence["rendering"], "QUOTATION")
                self.assertTrue(evidence["transformation"])
                self.assertTrue(evidence["justification"])
                self.assertEqual(evidence["claim_id"], "C1")

    def test_fixture_never_reads_source_or_interprets_it_as_code(self):
        # build already completed; fixtures use only explicit observations.
        with patch.object(Path, "open", side_effect=AssertionError("unexpected file read")):
            for case in self.cases:
                result = battery.constructed_response(case)
                self.assertIn("assessment", result)
        injected = battery.constructed_response(self.variants["instruction_injection"])
        self.assertEqual(injected["findings"]["instruction_boundary"], "SOURCE_INSTRUCTION_NOT_GOVERNING")
        self.assertEqual(injected["assessment"]["claims"][0]["support"], "SUPPORTED")
        self.assertNotIn("FABRICATED-SOURCE", {e["source_id"] for e in injected["evidence"]})

    def test_fixture_is_pure_and_rejects_unknown_modes(self):
        before = deepcopy(self.cases)
        for case in self.cases:
            a = battery.constructed_response(case)
            b = battery.constructed_response(case)
            self.assertEqual(a, b)
            a["assessment"]["claims"][0]["text"] = "changed local result"
            a["evidence"].clear()
            battery.constructed_response(case, "faulty")
        self.assertEqual(self.cases, before)
        with self.assertRaises(ValueError):
            battery.constructed_response(self.cases[0], "live-model")
        with self.assertRaises(ValueError):
            battery.constructed_response({"schema": "study-aperture/1"})
        with self.assertRaises(ValueError):
            battery.constructed_response(None)

    def test_missing_scope_conflict_and_no_count_remain_unresolved(self):
        for family in ("scope_ambiguity", "conflicting_sources", "missing_source", "changed_source", "unresolved_case"):
            with self.subTest(family=family):
                result = battery.constructed_response(self.bases[family])
                self.assertEqual(result["assessment"]["claims"][0]["support"], "UNDETERMINED")
                self.assertEqual(result["findings"]["uncertainty_state"], "UNRESOLVED")
                self.assertEqual(result["assessment"]["decisions"][0]["state"], "UNRESOLVED")
        missing = battery.constructed_response(self.bases["missing_source"])
        self.assertTrue(missing["provenance"]["unavailable_information"])
        self.assertFalse(any(e["source_id"] == "MISSING" for e in missing["evidence"]))
        no_count = battery.constructed_response(self.bases["unresolved_case"])
        self.assertNotEqual(no_count["assessment"]["claims"][0]["support"], "UNSUPPORTED")

    def test_wrong_location_fault_keeps_quote_but_invalidates_span(self):
        case = self.bases["incorrect_location"]
        good = battery.constructed_response(case)
        bad = battery.constructed_response(case, "faulty")
        self.assertEqual(good["evidence"][0]["quote"], bad["evidence"][0]["quote"])
        self.assertEqual(bad["evidence"][0]["start"], good["evidence"][0]["start"] + 1)
        source = {s["source_id"]: s for s in case["sources"]}[bad["evidence"][0]["source_id"]]
        text = (self.root / source["path"]).read_text(encoding="utf-8")
        e = bad["evidence"][0]
        self.assertNotEqual(text[e["start"]:e["end"]], e["quote"])
        self.assertEqual(production.check(bad["assessment"]), [])

    def test_qualification_loss_fault_removes_material_condition(self):
        case = self.bases["conditional_claim"]
        qualification = case["observations"]["qualifications"][0]
        good, bad = battery.constructed_response(case), battery.constructed_response(case, "faulty")
        self.assertIn(qualification, good["findings"]["qualification_state"])
        self.assertIn(qualification, [e["quote"] for e in good["evidence"]])
        self.assertNotIn(qualification, bad["findings"]["qualification_state"])
        self.assertNotIn(qualification, [e["quote"] for e in bad["evidence"]])
        self.assertEqual(good["assessment"]["claims"][0]["support"], "PARTIALLY_SUPPORTED")
        self.assertEqual(bad["assessment"]["claims"][0]["support"], "SUPPORTED")

    def test_fabricated_source_fault_is_undeclared_not_a_real_source(self):
        for case in self.cases:
            result = battery.constructed_response(case, "faulty")
            fabricated = [e for e in result["evidence"] if e["source_id"] == "FABRICATED-SOURCE"]
            self.assertEqual(len(fabricated), 1)
            self.assertNotIn("FABRICATED-SOURCE", {s["source_id"] for s in case["sources"]})
            self.assertEqual(fabricated[0]["origin"], "SUPPLIED")
            self.assertEqual(fabricated[0]["end"], len(fabricated[0]["quote"]))
            self.assertEqual(production.check(result["assessment"]), [])


if __name__ == "__main__":
    unittest.main()
