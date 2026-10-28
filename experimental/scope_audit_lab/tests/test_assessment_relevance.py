"""Literal assessment-link relevance, not a scientific support classifier."""

import copy
import socket
import subprocess
import unittest
from unittest.mock import patch

from test_integrity_checker import checker, codes, fixture, missing, present, record, ref


def linked(selector=None, outcome="MET"):
    rows = fixture("MET")
    subject = {"subject": ref("lab:observation", "observation"), "examined_version": present("v1")}
    subject["selector"] = present(selector) if selector is not None else missing()
    rows[2]["payload"].update(
        subjects=[subject], property="Free-form illustrative property.",
        criteria=[{"outcome": outcome}],
    )
    rows[1]["payload"]["assessment_refs"] = [ref("lab:assessment", "assessment")]
    return rows


def application_link(selector="payload.applicability_status"):
    rows = linked()
    rows[1]["payload"]["assessment_refs"] = []
    rows[2]["payload"]["subjects"] = [{
        "subject": ref("lab:application", "anchor_application"),
        "examined_version": present("v1"),
        "selector": present(selector) if selector is not None else missing(),
    }]
    rows[3]["payload"]["applicability_assessment_refs"] = [ref("lab:assessment", "assessment")]
    return rows


def relevance(rows, i=0):
    return checker.check_records(rows)["assessment_link_relevance"][i]


class AssessmentRelevanceTests(unittest.TestCase):
    def test_direct_subject_version_matches_metadata_only(self):
        row = relevance(linked())
        self.assertEqual(row["link_relevance"], "METADATA_MATCH_ONLY")
        self.assertFalse(row["scientific_support_established"])
        self.assertFalse(row["property_alignment_established"])

    def test_unrelated_but_resolved_assessment_is_blocked(self):
        rows = linked()
        rows[2]["payload"]["subjects"][0]["subject"] = ref("lab:anchor", "physics_anchor")
        row = relevance(rows)
        self.assertEqual(row["assessment_resolution"], "RESOLVED")
        self.assertEqual(row["link_relevance"], "UNRELATED_SUBJECT")

    def test_same_property_wording_does_not_create_subject_identity(self):
        rows = linked()
        rows[2]["payload"]["property"] = "lab:observation is verified, correct, and passed."
        rows[2]["payload"]["subjects"][0]["subject"] = ref("lab:anchor", "physics_anchor")
        self.assertEqual(relevance(rows)["link_relevance"], "UNRELATED_SUBJECT")

    def test_examined_version_mismatch_not_relevant(self):
        rows = linked()
        rows[2]["payload"]["subjects"][0]["examined_version"] = present("v0")
        self.assertEqual(relevance(rows)["link_relevance"], "VERSION_MISMATCH")

    def test_missing_examined_version_not_guessed(self):
        rows = linked()
        rows[2]["payload"]["subjects"][0]["examined_version"] = missing()
        self.assertEqual(relevance(rows)["link_relevance"], "VERSION_UNKNOWN")

    def test_missing_owner_version_not_guessed(self):
        rows = linked()
        rows[1]["record_version"] = missing()
        self.assertEqual(relevance(rows)["link_relevance"], "VERSION_UNKNOWN")

    def test_version_strings_not_trimmed(self):
        rows = linked()
        rows[2]["payload"]["subjects"][0]["examined_version"] = present("v1 ")
        self.assertEqual(relevance(rows)["link_relevance"], "VERSION_MISMATCH")

    def test_wrong_subject_expected_type(self):
        rows = linked()
        rows[2]["payload"]["subjects"][0]["subject"]["expected_type"] = "equation"
        self.assertEqual(relevance(rows)["link_relevance"], "BLOCKED_SUBJECT_REFERENCE")

    def test_missing_assessment_not_inferred_from_resolution_assertion(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = [ref("missing", "assessment", "RESOLVED")]
        self.assertEqual(relevance(rows)["link_relevance"], "BLOCKED_ASSESSMENT_REFERENCE")

    def test_ambiguous_assessment_no_latest_wins(self):
        rows = linked()
        other = copy.deepcopy(rows[2])
        other["record_version"] = present("newer")
        rows.append(other)
        self.assertEqual(relevance(rows)["assessment_resolution"], "AMBIGUOUS")

    def test_owner_ambiguity_blocks_match(self):
        rows = linked()
        other = copy.deepcopy(rows[1])
        other["payload"]["other"] = True
        rows.append(other)
        self.assertEqual(relevance(rows)["link_relevance"], "BLOCKED_OWNER_IDENTITY")

    def test_wrong_assessment_type(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = [ref("lab:anchor", "physics_anchor")]
        self.assertEqual(relevance(rows)["link_relevance"], "WRONG_ASSESSMENT_TYPE")

    def test_self_reference_does_not_substantiate_assessment(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows[2]["payload"]["assessment_refs"] = [ref("lab:assessment", "assessment")]
        self.assertEqual(relevance(rows)["link_relevance"], "SELF_REFERENCE")

    def test_no_transitive_inheritance(self):
        rows = linked()
        intermediate = record("lab:intermediate", "assessment", {
            "subjects": copy.deepcopy(rows[2]["payload"]["subjects"]),
            "criteria": [{"outcome": "MET"}],
        })
        rows.append(intermediate)
        rows[2]["payload"]["subjects"][0]["subject"] = ref("lab:intermediate", "assessment")
        self.assertEqual(relevance(rows)["link_relevance"], "UNRELATED_SUBJECT")

    def test_application_model_subject_only_is_indirect_unknown(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows[3]["payload"]["applicability_assessment_refs"] = [ref("lab:assessment", "assessment")]
        self.assertEqual(relevance(rows)["link_relevance"], "RELATED_SUBJECT_ONLY")

    def test_application_exact_field_selector_matches(self):
        row = relevance(application_link())
        self.assertEqual(row["link_relevance"], "METADATA_MATCH_ONLY")
        self.assertEqual(row["required_selector"], "payload.applicability_status")

    def test_application_wrong_field_selector_not_substituted(self):
        self.assertEqual(relevance(application_link("payload.comparison_status"))["link_relevance"],
                         "SELECTOR_MISMATCH")

    def test_missing_application_selector_stays_unknown(self):
        self.assertEqual(relevance(application_link(None))["link_relevance"], "SELECTOR_UNKNOWN")

    def test_whole_record_selector_does_not_imply_specific_field(self):
        self.assertEqual(relevance(application_link("payload"))["link_relevance"], "SELECTOR_MISMATCH")

    def test_selector_alias_not_silently_equated(self):
        self.assertEqual(relevance(application_link("/payload/applicability_status"))["link_relevance"],
                         "SELECTOR_MISMATCH")

    def test_definitive_status_mapping_remains_unestablished(self):
        rows = application_link()
        rows[3]["payload"]["applicability_status"] = "IN_SCOPE_FOR_STATED_CHECK"
        r = checker.check_records(rows)
        self.assertIn("ASSESSMENT_VERDICT_MAPPING_UNESTABLISHED", codes(r))
        self.assertFalse(r["assessment_link_relevance"][0]["verdict_mapping_established"])

    def test_comparison_requires_its_own_selector(self):
        rows = application_link("payload.comparison_status")
        rows[3]["payload"]["comparison_assessment_refs"] = rows[3]["payload"].pop("applicability_assessment_refs")
        self.assertEqual(relevance(rows)["link_relevance"], "METADATA_MATCH_ONLY")

    def test_conflicting_duplicate_subject_versions_not_selected(self):
        rows = linked()
        other = copy.deepcopy(rows[2]["payload"]["subjects"][0])
        other["examined_version"] = present("v0")
        rows[2]["payload"]["subjects"].append(other)
        self.assertEqual(relevance(rows)["link_relevance"], "CONFLICTING_SUBJECT_BINDINGS")

    def test_identical_subject_repetition_does_not_strengthen_support(self):
        rows = linked()
        rows[2]["payload"]["subjects"] *= 2
        row = relevance(rows)
        self.assertEqual(row["link_relevance"], "METADATA_MATCH_ONLY")
        self.assertFalse(row["scientific_support_established"])

    def test_relevant_and_unrelated_links_both_retained(self):
        rows = linked()
        unrelated = record("lab:unrelated", "assessment", {
            "subjects": [{"subject": ref("lab:anchor", "physics_anchor"), "examined_version": present("v1")}],
        })
        rows.append(unrelated)
        rows[1]["payload"]["assessment_refs"].append(ref("lab:unrelated", "assessment"))
        r = checker.check_records(rows)
        self.assertEqual([x["link_relevance"] for x in r["assessment_link_relevance"]],
                         ["METADATA_MATCH_ONLY", "UNRELATED_SUBJECT"])

    def test_unevaluated_criteria_not_promoted(self):
        rows = linked(outcome="NOT_EVALUATED")
        r = checker.check_records(rows)
        self.assertEqual(r["assessment_link_relevance"][0]["recorded_criterion_outcomes"], ["NOT_EVALUATED"])
        self.assertIn("ASSESSMENT_OUTCOME_UNESTABLISHED", codes(r))

    def test_missing_criteria_reported(self):
        rows = linked()
        rows[2]["payload"].pop("criteria")
        self.assertIn("ASSESSMENT_CRITERIA_UNAVAILABLE", codes(checker.check_records(rows)))

    def test_not_met_does_not_automatically_determine_conclusion(self):
        row = relevance(linked(outcome="NOT_MET"))
        self.assertEqual(row["recorded_criterion_outcomes"], ["NOT_MET"])
        self.assertFalse(row["scientific_support_established"])

    def test_malformed_subjects_or_criteria_do_not_crash(self):
        for value in (None, {}, [], [None], [{"subject": None}]):
            with self.subTest(value=value):
                rows = linked()
                rows[2]["payload"]["subjects"] = value
                self.assertEqual(relevance(rows)["link_relevance"], "SUBJECTS_MALFORMED")
        rows = linked()
        rows[2]["payload"]["criteria"] = [{"outcome": []}]
        self.assertIn("ASSESSMENT_CRITERIA_MALFORMED", codes(checker.check_records(rows)))

    def test_uncertainty_requires_explicit_uncertainty_selector(self):
        rows = linked(selector="payload.uncertainty")
        rows[1]["payload"]["uncertainty"] = {"assessment_refs": rows[1]["payload"].pop("assessment_refs")}
        self.assertEqual(relevance(rows)["link_relevance"], "METADATA_MATCH_ONLY")

    def test_unknown_nested_context_not_guessed(self):
        rows = linked()
        rows[1]["payload"]["unrecognized"] = {"assessment_refs": rows[1]["payload"].pop("assessment_refs")}
        self.assertEqual(relevance(rows)["link_relevance"], "CONTEXT_UNESTABLISHED")

    def test_step_selector_must_name_exact_unique_step(self):
        rows = linked(selector="step_id=s1")
        rows[1]["payload"]["assessment_refs"] = []
        derivation = record("lab:derivation", "derivation", {
            "steps": [{"step_id": "s1", "assessment_refs": [ref("lab:assessment", "assessment")]}],
        })
        rows.append(derivation)
        rows[2]["payload"]["subjects"][0]["subject"] = ref("lab:derivation", "derivation")
        self.assertEqual(relevance(rows)["link_relevance"], "METADATA_MATCH_ONLY")
        rows[-1]["payload"]["steps"][0]["step_id"] = "s2"
        self.assertEqual(relevance(rows)["link_relevance"], "SELECTOR_MISMATCH")
        rows[-1]["payload"]["steps"] *= 2
        self.assertEqual(relevance(rows)["link_relevance"], "CONTEXT_UNESTABLISHED")

    def test_empty_or_malformed_assessment_lists(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = [None]
        self.assertEqual(relevance(rows)["link_relevance"], "BLOCKED_ASSESSMENT_REFERENCE")
        rows[1]["payload"]["assessment_refs"] = None
        self.assertIn("ASSESSMENT_LINK_LIST_MALFORMED", codes(checker.check_records(rows)))

    def test_no_network_execution_or_mutation(self):
        rows = linked()
        before = copy.deepcopy(rows)
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
                patch.object(subprocess, "Popen", side_effect=AssertionError("execution forbidden")):
            checker.check_records(rows)
        self.assertEqual(rows, before)

    def test_markdown_has_relevance_limits(self):
        report = checker.markdown(checker.check_records(linked()))
        self.assertIn("## Assessment-to-subject links", report)
        self.assertIn("METADATA_MATCH_ONLY is not a support verdict", report)

    def test_condition_evidence_cannot_launder_unrelated_assessment(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows[3]["payload"]["condition_checks"][0]["evidence_refs"] = [ref("lab:assessment", "assessment")]
        row = relevance(rows)
        self.assertEqual(row["link_relevance"], "RELATED_SUBJECT_ONLY")
        self.assertEqual(row["required_selector"], "condition_id=C1")

    def test_condition_selector_matches_but_does_not_establish_outcome(self):
        rows = application_link("condition_id=C1")
        rows[3]["payload"]["applicability_assessment_refs"] = []
        rows[3]["payload"]["condition_checks"][0]["evidence_refs"] = [ref("lab:assessment", "assessment")]
        r = checker.check_records(rows)
        self.assertEqual(r["assessment_link_relevance"][0]["link_relevance"], "METADATA_MATCH_ONLY")
        self.assertIn("ASSESSMENT_VERDICT_MAPPING_UNESTABLISHED", codes(r))

    def test_assessment_criterion_evidence_targets_exact_criterion(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows[2]["payload"]["criteria"][0].update(
            criterion_id="K1", evidence_refs=[ref("lab:criterion-review", "assessment")])
        rows.append(record("lab:criterion-review", "assessment", {
            "subjects": [{"subject": ref("lab:assessment", "assessment"),
                          "examined_version": present("v1"), "selector": present("criterion_id=K1")}],
            "criteria": [{"outcome": "MET"}],
        }))
        self.assertEqual(relevance(rows)["link_relevance"], "METADATA_MATCH_ONLY")

    def test_duplicate_criterion_ids_block_selector_policy(self):
        rows = application_link("condition_id=C1")
        rows[3]["payload"]["applicability_assessment_refs"] = []
        condition = rows[3]["payload"]["condition_checks"][0]
        condition["evidence_refs"] = [ref("lab:assessment", "assessment")]
        rows[3]["payload"]["condition_checks"].append(copy.deepcopy(condition))
        self.assertEqual(relevance(rows)["link_relevance"], "CONTEXT_UNESTABLISHED")

    def test_generic_observation_evidence_not_treated_as_assessment(self):
        rows = fixture("MET")
        self.assertEqual(checker.check_records(rows)["assessment_link_relevance"], [])

    def test_calculation_prerequisite_assessment_selector(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows.append(record("lab:calc", "calculation", {
            "inputs": [{"input": ref("lab:observation", "observation"), "examined_version": present("v1")}],
            "prerequisites": [{"requirement_id": "R1", "outcome": "MET",
                               "evidence_refs": [ref("lab:assessment", "assessment")]}],
        }))
        rows[2]["payload"]["subjects"] = [{
            "subject": ref("lab:calc", "calculation"), "examined_version": present("v1"),
            "selector": present("requirement_id=R1"),
        }]
        self.assertEqual(relevance(rows)["link_relevance"], "METADATA_MATCH_ONLY")

    def test_valid_criterion_self_reference_cannot_substantiate_itself(self):
        rows = linked()
        rows[1]["payload"]["assessment_refs"] = []
        rows[2]["payload"]["criteria"][0].update(
            criterion_id="self", evidence_refs=[ref("lab:assessment", "assessment")])
        self.assertEqual(relevance(rows)["link_relevance"], "SELF_REFERENCE")

    def test_current_wrong_field_binding_does_not_rescue_stale_right_field(self):
        rows = application_link()
        original = rows[2]["payload"]["subjects"][0]
        original["examined_version"] = present("v0")
        alternative = copy.deepcopy(original)
        alternative["selector"] = present("payload.comparison_status")
        alternative["examined_version"] = present("v1")
        rows[2]["payload"]["subjects"].append(alternative)
        self.assertEqual(relevance(rows)["link_relevance"], "VERSION_MISMATCH")


if __name__ == "__main__":
    unittest.main()
