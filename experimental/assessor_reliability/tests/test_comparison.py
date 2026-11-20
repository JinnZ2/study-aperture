"""CONSTRUCTED analyzer unit tests; not model or reviewer performance evidence."""
import copy
import json
import math
import unittest

from experimental.assessor_reliability.comparison import (
    agreement, compare_perturbation, compare_repeats, render_markdown,
)


def capture(run_id="run-1", parsed=None):
    """Capture-shaped synthetic metadata; no model or raw artifact is created."""
    return {
        "schema": "assessor-reliability/capture/1", "run_id": run_id,
        "case_id": "CONSTRUCTED-case", "variant_id": "base", "raw_sha256": "a" * 64,
        "parsed": copy.deepcopy(parsed) if parsed is not None else {
            "assessment": {"claims": [{"id": "C1", "support": "UNDETERMINED"}], "decisions": []},
            "evidence": [], "findings": {"scope_state": "UNRESOLVED", "qualification_state": "UNDECLARED"},
            "provenance": {"assessor_prior": "UNKNOWN_ORIGIN", "unavailable_information": []},
        },
        "parse_errors": [],
        "validation": {"schema_valid": True, "invariant_violations": [],
                       "missing_fields": [], "incompleteness": ["CONSTRUCTED unknown retained"]},
        "mechanical": {"interpretation": "NOT_ASSESSED"},
        "provenance": {
            "model": {"name": "CONSTRUCTED-NO-MODEL", "version": "fixture/1"},
            "environment": {"adapter": "CONSTRUCTED-offline", "temperature": 0},
            "prompt_sha256": "b" * 64, "instructions_sha256": "c" * 64,
            "source_package_sha256": "d" * 64, "freeze_sha256": "e" * 64,
            "execution": {"errors": [], "retries": 0, "truncated": False, "incomplete": False},
            "supplied_material": [{"source_id": "S1", "sha256": "f" * 64}],
            "retrieved_material": [], "tools": [], "assessor_prior": "UNKNOWN_ORIGIN",
        }, "constructed": True,
    }


def perturbation():
    base, variant = capture("base-run"), capture("variant-run")
    variant["variant_id"] = "qualification_addition"
    variant["provenance"]["source_package_sha256"] = "1" * 64
    variant["provenance"]["prompt_sha256"] = "2" * 64
    variant["provenance"]["supplied_material"][0]["sha256"] = "3" * 64
    variant["parsed"]["findings"]["qualification_state"] = "CONSTRUCTED narrower qualification"
    spec = {
        "base_case_id": base["case_id"], "base_variant_id": "base",
        "kind": "qualification_addition", "may_change": ["evidence"],
        "must_change": ["findings.qualification_state"], "invariant": ["findings.scope_state"],
        "unresolved_when": ["The applicability of the qualification is not established."],
        "justification": ["CONSTRUCTED qualification text was added to the source."],
        "limits": ["Exact changes are not a test of interpretation."],
    }
    return base, variant, spec


class RepeatsTests(unittest.TestCase):
    def test_exact_pair_counts_and_declared_materiality(self):
        records = [capture("r1"), capture("r2"), capture("r3")]
        records[2]["parsed"]["findings"]["scope_state"] = "CONSTRUCTED broader scope"
        report = compare_repeats(records, ["findings.scope_state"], ["findings.scope_state"])
        field = report["fields"]["findings.scope_state"]
        self.assertEqual(report["sample_size"], 3)
        self.assertEqual(report["pair_denominator"], 3)
        self.assertEqual(report["eligible_pair_count"], 3)
        self.assertEqual(field["counts"], {"PASS": 1, "FAIL": 2, "UNSCORABLE": 0,
                                        "NOT_ASSESSED": 0, "denominator": 3, "scorable_denominator": 3})
        self.assertEqual(field["material_disagreement_count"], 2)
        self.assertEqual(sorted(row["count"] for row in field["class_prevalence"]), [1, 2])
        self.assertTrue(all(row["denominator"] == 3 for row in field["class_prevalence"]))

    def test_material_fields_are_not_assumed_and_are_added_to_selection(self):
        a, b = capture("a"), capture("b")
        b["parsed"]["evidence"] = [{"quote": "CONSTRUCTED changed evidence"}]
        report = compare_repeats([a, b])
        self.assertIsNone(report["fields"]["evidence"]["material_disagreement_count"])
        report = compare_repeats([a, b], [], ["evidence"])
        self.assertEqual(list(report["fields"]), ["evidence"])
        self.assertEqual(report["fields"]["evidence"]["material_disagreement_count"], 1)

    def test_missing_and_null_remain_distinct_and_missing_is_unscorable(self):
        a, b, c = capture("a"), capture("b"), capture("c")
        a["parsed"]["findings"]["extra"] = None
        c["parsed"]["findings"]["extra"] = None
        report = compare_repeats([a, b, c], ["findings.extra"])
        row = report["fields"]["findings.extra"]
        self.assertEqual(row["missing_observations"], 1)
        self.assertEqual(row["null_observations"], 2)
        self.assertEqual(row["counts"]["PASS"], 1)
        self.assertEqual(row["counts"]["UNSCORABLE"], 2)
        comparison = report["pairs"][0]["fields"]["findings.extra"]
        self.assertEqual(comparison["left"], None)
        self.assertEqual(comparison["right"], {"$missing": True})
        self.assertFalse(comparison["exact_equal"])
        self.assertEqual(comparison["outcome"], "UNSCORABLE")

    def test_both_missing_are_not_success_or_disagreement(self):
        report = compare_repeats([capture("a"), capture("b")], ["findings.absent"])
        self.assertEqual(report["fields"]["findings.absent"]["counts"]["UNSCORABLE"], 1)
        self.assertTrue(report["pairs"][0]["fields"]["findings.absent"]["exact_equal"])
        self.assertEqual(report["fields"]["findings.absent"]["class_prevalence"], [])

    def test_literal_missing_marker_is_not_absent(self):
        a, b = capture("a"), capture("b")
        a["parsed"]["findings"]["extra"] = {"$missing": True}
        report = compare_repeats([a, b], ["findings.extra"])
        row = report["pairs"][0]["fields"]["findings.extra"]
        self.assertFalse(row["exact_equal"])
        self.assertEqual(row["missing"], {"left": False, "right": True})
        self.assertEqual(report["fields"]["findings.extra"]["present_observation_denominator"], 1)

    def test_unknown_classes_and_valid_incompleteness_are_preserved(self):
        report = compare_repeats([capture("a"), capture("b")], ["findings.qualification_state"])
        self.assertEqual(report["fields"]["findings.qualification_state"]["class_prevalence"][0]["value"], "UNDECLARED")
        self.assertEqual(report["inputs"][0]["incompleteness"], ["CONSTRUCTED unknown retained"])
        self.assertEqual(report["eligible_pair_count"], 1)
        self.assertTrue(any("not correctness" in item for item in report["limitations"]))

    def test_key_order_ignored_but_list_order_and_scalar_types_preserved(self):
        a, b = capture("a"), capture("b")
        a["parsed"]["findings"] = {"x": 1, "y": True}
        b["parsed"]["findings"] = {"y": True, "x": 1}
        report = compare_repeats([a, b], ["findings"])
        self.assertEqual(report["fields"]["findings"]["counts"]["PASS"], 1)
        b["parsed"]["findings"]["x"] = True
        self.assertEqual(compare_repeats([a, b], ["findings.x"])["fields"]["findings.x"]["counts"]["FAIL"], 1)
        b["parsed"]["findings"]["x"] = 1.0
        self.assertEqual(compare_repeats([a, b], ["findings.x"])["fields"]["findings.x"]["counts"]["FAIL"], 1)
        a["parsed"]["evidence"] = ["A", "B"]
        b["parsed"]["evidence"] = ["B", "A"]
        self.assertEqual(compare_repeats([a, b], ["evidence"])["fields"]["evidence"]["counts"]["FAIL"], 1)

    def test_every_conditioning_drift_excludes_a_repeat(self):
        changes = [
            ("model", {"name": "OTHER", "version": "fixture/1"}),
            ("model", {"name": "CONSTRUCTED-NO-MODEL", "version": "fixture/2"}),
            ("environment", {"adapter": "OTHER"}), ("prompt_sha256", "1" * 64),
            ("instructions_sha256", "1" * 64), ("source_package_sha256", "1" * 64),
            ("freeze_sha256", "1" * 64), ("tools", ["tool"]),
            ("retrieved_material", [{"source_id": "R1"}]),
            ("supplied_material", [{"source_id": "OTHER"}]),
            ("assessor_prior", "DECLARED_ORIGIN"),
            ("execution", {"errors": [], "retries": 1, "truncated": False, "incomplete": False}),
        ]
        for key, value in changes:
            with self.subTest(field=key):
                a, b = capture("a"), capture("b")
                b["provenance"][key] = value
                report = compare_repeats([a, b], ["findings.scope_state"])
                self.assertEqual(report["eligible_pair_count"], 0)
                self.assertEqual(report["fields"]["findings.scope_state"]["counts"]["UNSCORABLE"], 1)
                self.assertFalse(report["pairs"][0]["provenance"]["equivalent"])

    def test_case_and_variant_mismatches_exclude_repeats(self):
        for key in ("case_id", "variant_id"):
            with self.subTest(field=key):
                a, b = capture("a"), capture("b")
                b[key] = "other"
                self.assertEqual(compare_repeats([a, b])["eligible_pair_count"], 0)

    def test_matching_undeclared_model_versions_are_only_matching_declarations(self):
        a, b = capture("a"), capture("b")
        for item in (a, b):
            item["provenance"]["model"]["version"] = "UNDECLARED"
        report = compare_repeats([a, b])
        self.assertEqual(report["eligible_pair_count"], 1)
        provenance = report["pairs"][0]["provenance"]
        self.assertEqual(len(provenance["unknown_metadata"]), 2)
        self.assertIn("not actual equivalent conditions", provenance["limitation"])
        self.assertEqual(provenance["basis"], "EXACT_RECORDED_DECLARATIONS_ONLY")

    def test_missing_and_null_provenance_never_match_even_when_shared(self):
        for value in ("missing", None):
            with self.subTest(value=value):
                a, b = capture("a"), capture("b")
                for item in (a, b):
                    if value == "missing":
                        del item["provenance"]["instructions_sha256"]
                    else:
                        item["provenance"]["instructions_sha256"] = None
                report = compare_repeats([a, b])
                self.assertEqual(report["eligible_pair_count"], 0)
                self.assertEqual(report["fields"]["evidence"]["excluded_observations"], 2)
                self.assertEqual(report["fields"]["evidence"]["counts"]["denominator"], 1)

    def test_invalid_capture_variants_remain_in_denominators(self):
        broken = []
        for mutate in (
            lambda c: c.update(parsed=None), lambda c: c.update(parse_errors=["invalid JSON"]),
            lambda c: c["validation"].update(schema_valid=False),
            lambda c: c["validation"].update(invariant_violations=["violation"]),
            lambda c: c["validation"].update(missing_fields=["assessment"]),
            lambda c: c["provenance"]["execution"].update(errors=["provider error"]),
            lambda c: c["provenance"]["execution"].update(truncated=True),
            lambda c: c["provenance"]["execution"].update(incomplete=True),
            lambda c: c["provenance"]["execution"].update(retries=True),
            lambda c: c.update(raw_sha256="UNDECLARED"),
            lambda c: c.update(schema="other"), lambda c: c.update(provenance=None),
            lambda c: c.update(validation=None), lambda c: c.update(parse_errors=None),
            lambda c: c.update(run_id=[]), lambda c: c["parsed"].update(nonfinite=math.nan),
        ):
            item = capture("broken")
            mutate(item)
            broken.append(item)
        broken += [None, "not a capture", 5, {}]
        for index, bad in enumerate(broken):
            with self.subTest(index=index):
                report = compare_repeats([capture("a"), bad, capture("c")], ["evidence"])
                counts = report["fields"]["evidence"]["counts"]
                self.assertEqual(counts["denominator"], 3)
                self.assertEqual(counts["PASS"], 1)
                self.assertEqual(counts["UNSCORABLE"], 2)
                self.assertEqual(report["fields"]["evidence"]["excluded_observations"], 1)
                json.dumps(report, allow_nan=False)

    def test_duplicate_runs_do_not_inflate_repeat_count(self):
        report = compare_repeats([capture("same"), capture("same")])
        self.assertEqual(report["eligible_pair_count"], 0)
        self.assertEqual(report["pair_denominator"], 1)
        self.assertIn("duplicate run_id", " ".join(report["pairs"][0]["reasons"]))

    def test_empty_singleton_and_empty_fields_have_explicit_zero_denominators(self):
        for records in ([], [capture()]):
            report = compare_repeats(records)
            self.assertEqual(report["pair_denominator"], 0)
            self.assertEqual(report["fields"]["evidence"]["counts"]["scorable_denominator"], 0)
            self.assertEqual(report["status"], "MECHANICAL_COMPARISON_ONLY")
        self.assertEqual(compare_repeats([capture("a"), capture("b")], [])["fields"], {})

    def test_inputs_are_not_mutated(self):
        records = [capture("a"), capture("b")]
        before = copy.deepcopy(records)
        compare_repeats(records, ["findings.scope_state"], ["evidence"])
        self.assertEqual(records, before)

    def test_excluded_null_and_absent_provenance_remain_distinct(self):
        a, b = capture("a"), capture("b")
        a["provenance"] = None
        del b["provenance"]
        report = compare_repeats([a, b])
        declarations = [row["provenance_declaration"] for row in report["inputs"]]
        self.assertTrue(declarations[0]["present"])
        self.assertIsNone(declarations[0]["value"])
        self.assertFalse(declarations[1]["present"])
        self.assertEqual(declarations[1]["value"], {"$missing": True})
        self.assertEqual(report["eligible_pair_count"], 0)

    def test_invalid_json_metadata_is_excluded_without_invalid_report_values(self):
        bad = capture("bad")
        bad["validation"]["incompleteness"] = [math.nan]
        bad["provenance"]["environment"]["invalid"] = math.inf
        report = compare_repeats([capture("good"), bad])
        self.assertEqual(report["eligible_pair_count"], 0)
        self.assertFalse(report["inputs"][1]["provenance_declaration"]["json_valid"])
        self.assertEqual(report["inputs"][1]["incompleteness"], {"$missing": True})
        json.dumps(report, allow_nan=False)

    def test_invalid_api_field_selection_is_rejected(self):
        for fields in ("evidence", [""], ["a..b"], ["evidence.*"], [1]):
            with self.subTest(fields=fields):
                with self.assertRaises(ValueError):
                    compare_repeats([], fields)
        with self.assertRaises(ValueError):
            compare_repeats({})


class PerturbationTests(unittest.TestCase):
    def test_legitimate_source_and_full_prompt_change_do_not_exclude(self):
        report = compare_perturbation(*perturbation())
        self.assertTrue(report["eligible"])
        self.assertEqual(report["source_change"]["status"], "DECLARED_CHANGE")
        self.assertEqual(report["fields"]["findings.qualification_state"]["rule_outcomes"]["must_change"], "PASS")
        self.assertEqual(report["fields"]["findings.scope_state"]["rule_outcomes"]["invariant"], "PASS")
        self.assertEqual(report["unplanned_changes"], [])
        changes = {row["field"]: row for row in report["provenance"]["permitted_differences"]}
        self.assertTrue(changes["provenance.prompt_sha256"]["changed"])
        self.assertEqual(changes["provenance.prompt_sha256"]["outcome"], "NOT_ASSESSED")

    def test_allowed_change_is_not_required_change(self):
        base, variant, spec = perturbation()
        report = compare_perturbation(base, variant, spec)
        self.assertEqual(report["fields"]["evidence"]["rule_outcomes"]["may_change"], "NOT_ASSESSED")
        variant["parsed"]["evidence"] = [{"quote": "CONSTRUCTED new evidence"}]
        report = compare_perturbation(base, variant, spec)
        self.assertEqual(report["fields"]["evidence"]["rule_outcomes"]["may_change"], "NOT_ASSESSED")
        self.assertEqual(report["unplanned_changes"], [])

    def test_required_change_not_made_is_a_field_rule_failure_only(self):
        base, variant, spec = perturbation()
        variant["parsed"] = copy.deepcopy(base["parsed"])
        report = compare_perturbation(base, variant, spec)
        self.assertTrue(report["eligible"])
        row = report["fields"]["findings.qualification_state"]
        self.assertEqual(row["rule_outcomes"]["must_change"], "FAIL")
        self.assertEqual(row["comparison"]["outcome"], "PASS")
        self.assertEqual(report["change_counts"]["denominator"], 0)
        self.assertEqual(report["status"], "MECHANICAL_COMPARISON_ONLY")

    def test_invariant_and_unplanned_changes_are_separate_review_flags(self):
        base, variant, spec = perturbation()
        variant["parsed"]["findings"]["scope_state"] = "CONSTRUCTED different scope"
        variant["parsed"]["assessment"]["extra"] = "CONSTRUCTED unplanned field"
        report = compare_perturbation(base, variant, spec)
        row = report["fields"]["findings.scope_state"]
        self.assertEqual(row["rule_outcomes"]["invariant"], "FAIL")
        changes = {row["field"]: row for row in report["unplanned_changes"]}
        self.assertEqual(changes["findings.scope_state"]["classification"], "INVARIANT_FIELD_CHANGE")
        self.assertEqual(changes["assessment.extra"]["classification"], "UNPLANNED_FIELD_CHANGE")
        self.assertEqual(report["change_counts"]["FAIL"], 2)
        self.assertEqual(report["change_counts"]["denominator"], 3)

    def test_parent_rules_cover_child_changes_without_false_unplanned_flags(self):
        base, variant, spec = perturbation()
        spec["must_change"] = ["findings"]
        spec["invariant"] = []
        self.assertEqual(compare_perturbation(base, variant, spec)["unplanned_changes"], [])

    def test_prose_unresolved_conditions_are_not_automatically_scored(self):
        report = compare_perturbation(*perturbation())
        self.assertEqual(report["unresolved_counts"]["NOT_ASSESSED"], 1)
        self.assertEqual(report["unresolved_counts"]["denominator"], 1)
        self.assertEqual(report["unresolved_counts"]["scorable_denominator"], 0)
        self.assertEqual(report["unresolved_conditions"][0]["outcome"], "NOT_ASSESSED")

    def test_missing_required_field_is_unscorable_not_a_change_success(self):
        base, variant, spec = perturbation()
        del variant["parsed"]["findings"]["qualification_state"]
        report = compare_perturbation(base, variant, spec)
        self.assertEqual(report["fields"]["findings.qualification_state"]["rule_outcomes"]["must_change"], "UNSCORABLE")
        self.assertEqual(report["fields"]["findings.qualification_state"]["comparison"]["missing"], {"left": False, "right": True})

    def test_explicit_null_change_is_preserved_without_meaning_inferred(self):
        base, variant, spec = perturbation()
        variant["parsed"]["findings"]["qualification_state"] = None
        report = compare_perturbation(base, variant, spec)
        row = report["fields"]["findings.qualification_state"]
        self.assertEqual(row["comparison"]["right"], None)
        self.assertEqual(row["rule_outcomes"]["must_change"], "PASS")
        self.assertTrue(any("not the appropriateness" in item for item in report["limitations"]))

    def test_instructions_environment_exposure_and_freeze_still_must_match(self):
        for key, value in (("instructions_sha256", "7" * 64), ("freeze_sha256", "7" * 64),
                           ("environment", {"adapter": "other"}), ("tools", ["other"]),
                           ("retrieved_material", [{"source_id": "R1"}])):
            with self.subTest(key=key):
                base, variant, spec = perturbation()
                variant["provenance"][key] = value
                report = compare_perturbation(base, variant, spec)
                self.assertFalse(report["eligible"])
                self.assertEqual(report["fields"]["findings.qualification_state"]["rule_outcomes"]["must_change"], "UNSCORABLE")

    def test_source_change_missing_null_or_unchanged_is_not_established(self):
        for value in ("missing", None, "d" * 64):
            with self.subTest(value=value):
                base, variant, spec = perturbation()
                if value == "missing":
                    del variant["provenance"]["source_package_sha256"]
                else:
                    variant["provenance"]["source_package_sha256"] = value
                report = compare_perturbation(base, variant, spec)
                self.assertFalse(report["eligible"])
                self.assertEqual(report["source_change"]["status"], "UNSCORABLE")

    def test_malformed_specs_and_conflicts_are_unscorable_not_repaired(self):
        for mutate in (
            lambda s: s.update(base_case_id="wrong"), lambda s: s.update(base_variant_id="wrong"),
            lambda s: s.update(kind=None), lambda s: s.update(justification=[]),
            lambda s: s.update(may_change=None), lambda s: s.update(must_change=["bad.*"]),
            lambda s: s.update(invariant=["findings"]), lambda s: s.update(unresolved_when=None),
            lambda s: s.update(limits=math.nan),
        ):
            base, variant, spec = perturbation()
            mutate(spec)
            with self.subTest(spec=repr(spec)):
                report = compare_perturbation(base, variant, spec)
                self.assertFalse(report["eligible"])
                json.dumps(report, allow_nan=False)
        self.assertFalse(compare_perturbation(capture("a"), capture("b"), None)["eligible"])

    def test_invalid_capture_and_duplicate_run_are_unscorable(self):
        base, variant, spec = perturbation()
        variant["parsed"]["bad"] = math.nan
        report = compare_perturbation(base, variant, spec)
        self.assertFalse(report["eligible"])
        json.dumps(report, allow_nan=False)
        base, variant, spec = perturbation()
        variant["run_id"] = base["run_id"]
        self.assertFalse(compare_perturbation(base, variant, spec)["eligible"])
        report = compare_perturbation(None, "invalid", {})
        self.assertFalse(report["eligible"])
        self.assertEqual(report["pair_denominator"], 1)

    def test_rule_counts_have_rule_and_pair_denominators(self):
        base, variant, spec = perturbation()
        spec["may_change"].append("findings.qualification_state")
        row = compare_perturbation(base, variant, spec)["fields"]["findings.qualification_state"]
        self.assertEqual(row["counts"]["PASS"], 1)
        self.assertEqual(row["counts"]["NOT_ASSESSED"], 1)
        self.assertEqual(row["counts"]["denominator"], 2)
        self.assertEqual(row["counts"]["scorable_denominator"], 1)
        self.assertEqual(row["pair_denominator"], 1)

    def test_no_input_mutation(self):
        args = perturbation()
        before = copy.deepcopy(args)
        compare_perturbation(*args)
        self.assertEqual(args, before)


class AgreementAndRenderingTests(unittest.TestCase):
    def test_plain_records_exact_agreement_and_prevalence(self):
        report = agreement([{"state": "UNRESOLVED"}, {"state": "UNRESOLVED"}, {"state": "UNDECLARED"}], ["state"])
        self.assertEqual(report["fields"]["state"]["counts"]["PASS"], 1)
        self.assertEqual(report["fields"]["state"]["counts"]["FAIL"], 2)
        self.assertEqual(report["fields"]["state"]["observation_denominator"], 3)
        self.assertEqual(report["material_fields"], [])
        self.assertTrue(any("do not pool different cases" in item for item in report["limitations"]))

    def test_plain_invalid_missing_and_null_observations_are_separate(self):
        report = agreement([{"state": None}, {}, None, {"state": "UNKNOWN_ORIGIN"}], ["state"])
        row = report["fields"]["state"]
        self.assertEqual(row["counts"]["denominator"], 6)
        self.assertEqual(row["counts"]["scorable_denominator"], 1)
        self.assertEqual(row["counts"]["FAIL"], 1)
        self.assertEqual(row["missing_observations"], 1)
        self.assertEqual(row["null_observations"], 1)
        self.assertEqual(row["excluded_observations"], 1)
        self.assertEqual(row["counts"]["UNSCORABLE"], 5)

    def test_capture_agreement_is_equivalence_gated(self):
        a, b = capture("a"), capture("b")
        b["provenance"]["model"]["name"] = "OTHER"
        self.assertEqual(agreement([a, b], ["evidence"])["fields"]["evidence"]["counts"]["UNSCORABLE"], 1)
        self.assertEqual(agreement([a, {"evidence": []}], ["evidence"])["eligible_pair_count"], 0)

    def test_markdown_is_status_first_and_preserves_full_audit_record(self):
        report = compare_repeats([capture("a"), capture("b")], ["findings.qualification_state", "absent"])
        markdown = render_markdown(report)
        self.assertTrue(markdown.startswith("Status:"))
        self.assertIn("Scorable denominator", markdown)
        self.assertIn("UNSCORABLE", markdown)
        self.assertIn('"value": "UNDECLARED"', markdown)
        self.assertIn('"$missing": true', markdown)
        payload = markdown.split("```json\n", 1)[1].rsplit("\n```", 1)[0]
        self.assertEqual(json.loads(payload), report)
        self.assertTrue(markdown.endswith("\n"))
        self.assertEqual(markdown, render_markdown(report))

    def test_markdown_protects_tables_and_code_fence_without_changing_data(self):
        report = agreement([{"danger|<x>": "```\nCONSTRUCTED"}], ["danger|<x>"])
        markdown = render_markdown(report)
        self.assertIn("danger&#124;&lt;x&gt;", markdown)
        self.assertIn("````json", markdown)
        payload = markdown.split("````json\n", 1)[1].rsplit("\n````", 1)[0]
        self.assertEqual(json.loads(payload), report)

    def test_perturbation_markdown_keeps_unresolved_conditions_and_denominators(self):
        report = compare_perturbation(*perturbation())
        markdown = render_markdown(report)
        self.assertIn("declared rule evaluations", markdown)
        self.assertIn("The applicability of the qualification is not established.", markdown)
        self.assertIn("DECLARED_CHANGE", markdown)
        self.assertIn("NOT_ASSESSED", markdown)

    def test_reports_do_not_invent_scores_statistics_or_confidence_intervals(self):
        report = compare_repeats([capture("a"), capture("b")])
        for key in ("score", "reliability_score", "kappa", "confidence_interval", "correctness"):
            self.assertNotIn(key, report)
        self.assertEqual(report["status"], "MECHANICAL_COMPARISON_ONLY")


if __name__ == "__main__":
    unittest.main()
