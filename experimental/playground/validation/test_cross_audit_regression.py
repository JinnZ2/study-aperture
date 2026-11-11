"""Cross-audit expected outcomes, retention, independence and composition guards."""

import inspect
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from ..audits import cross_audit_regression as regression
from ..audits import denominator_process as denominator
from ..audits import distribution_mean_process as mean
from ..equations.measurand import ComparisonState, compare_substitution
from ..equations.substitution import ExperimentalDiagnostics
from ..failures import Axis, FailureRecord, Finding, Status


class CrossAuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = regression.inspect_regression()

    def codes(self, record):
        return {f["code"] for f in record["findings"]}

    def runs(self, case):
        return tuple(
            case[view]["declaration_comparison"][side]
            for view in ("denominator", "distribution_mean")
            for side in ("previous", "replacement"))

    def fresh(self, **kwargs):
        return regression.run_case(
            denominator.fixture_census(surviving=("A", "B")),
            mean.fixture_distribution(), mean.fixture_question(mean.Purpose.SQUARE),
            calculation=mean.Purpose.SQUARE, **kwargs)

    def test_independent_expected_outcome_matrix(self):
        eligible, void, withheld = (s.value for s in (
            ComparisonState.ELIGIBLE, ComparisonState.VOID, ComparisonState.WITHHELD))
        preserved, loss, unknown = (s.value for s in (
            mean.Conclusion.PRESERVED, mean.Conclusion.LOSS, mean.Conclusion.WITHHELD))
        expected = {
            "both_controls": (eligible, preserved),
            "denominator_change_mean_control": (void, preserved),
            "mean_loss_denominator_control": (eligible, loss),
            "both_findings_known": (void, loss),
            "false_shared_label_and_mean_loss": (void, loss),
            "multiple_coincidences": (void, preserved),
            "missing_window_known_policy_change": (void, unknown),
            "missing_purpose_not_inferred": (void, unknown),
            "missing_scope_and_membership": (void, unknown),
            "shared_unknown_gate_even_for_same_policy": (withheld, unknown),
            "inconsistent_mean_binding": (void, unknown),
            "independent_instrument_failure": (void, unknown),
            "independent_physical_failure": (void, unknown),
            "known_mismatch_and_unknown_scope": (void, unknown),
            "empty_survivor_denominator_and_mean_loss": (void, loss),
        }
        self.assertEqual(set(expected), set(self.report["cases"]))
        for name, wanted in expected.items():
            with self.subTest(scenario=name):
                case = self.report["cases"][name]
                self.assertEqual((case["denominator"]["audited_comparison"],
                                  case["distribution_mean"]["conclusion"]), wanted)

    def test_all_four_runs_share_context_anchor_and_ledger(self):
        for name, case in self.report["cases"].items():
            with self.subTest(scenario=name):
                shared = case["shared_experiment"]
                for run in self.runs(case):
                    self.assertEqual(run["experiment"], shared)
                    self.assertEqual(run["plan"]["context_digest"], case["shared_context_digest"])
                self.assertNotEqual(case["component_source_contexts"]["denominator"],
                                    case["shared_context_digest"])
                for view in ("denominator", "distribution_mean"):
                    previous, replacement = case[view]["procedure_traces"]
                    child = case[view]["declaration_comparison"]["replacement"]
                    self.assertEqual(child["parent_run_digest"], previous["run_digest"])
                    self.assertNotEqual(previous["run_digest"], replacement["run_digest"])

    def test_union_retains_both_finding_lists_without_reclassification(self):
        for case in self.report["cases"].values():
            expected = (case["denominator"]["record"]["findings"]
                        + case["distribution_mean"]["record"]["findings"])
            self.assertEqual(case["finding_union"]["findings"], expected)
            self.assertNotIn("MODEL_FAILED", self.codes(case["finding_union"]))
            self.assertEqual(case["physical_population_linkage"], "NOT_ESTABLISHED")
            self.assertEqual(case["joint_estimator_adequacy"], "NOT_TESTED")

    def test_two_known_findings_are_not_collapsed(self):
        case = self.report["cases"]["both_findings_known"]
        self.assertIn("DENOM_POLICY_CHANGE", self.codes(case["denominator"]["record"]))
        self.assertIn("MEAN_PURPOSE_LOSS", self.codes(case["distribution_mean"]["record"]))
        self.assertEqual(case["axis_statuses"], {
            "physical": "untested", "instrument": "ok", "determination": "failed"})
        self.assertIsNone(case["denominator"]["point_difference"])
        self.assertEqual(case["distribution_mean"]["audited_point_difference"], -1.0)

    def test_valid_mean_control_does_not_clear_denominator_mismatch(self):
        case = self.report["cases"]["denominator_change_mean_control"]
        self.assertTrue(case["distribution_mean"]["usable_for_selected_target_in_this_case"])
        self.assertIn("DENOM_POLICY_CHANGE", self.codes(case["finding_union"]))
        self.assertEqual(case["axis_statuses"]["determination"], "failed")

    def test_mean_target_loss_does_not_reclassify_valid_denominator_comparison(self):
        case = self.report["cases"]["mean_loss_denominator_control"]
        self.assertEqual(case["denominator"]["audited_comparison"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(case["denominator"]["point_difference"], 0.0)
        self.assertNotIn("MEAN_PURPOSE_LOSS", self.codes(case["denominator"]["record"]))

    def test_missing_scope_keeps_known_policy_and_withholds_mean_conclusion(self):
        case = self.report["cases"]["missing_window_known_policy_change"]
        self.assertTrue(all(not r["outputs"] for r in self.runs(case)))
        self.assertIn("DENOM_POLICY_CHANGE", self.codes(case["finding_union"]))
        self.assertIn("MEAN_SCOPE_UNKNOWN", self.codes(case["finding_union"]))
        self.assertNotIn("MEAN_PURPOSE_LOSS", self.codes(case["distribution_mean"]["record"]))
        self.assertEqual(case["distribution_mean"]["source_moments"]["variance"], "1")
        self.assertIsNone(case["distribution_mean"]["question"]["window"])
        self.assertIsNone(case["distribution_mean"]["audited_point_difference"])

    def test_unknown_purpose_is_not_inferred_from_candidate_calculation(self):
        case = self.report["cases"]["missing_purpose_not_inferred"]
        view = case["distribution_mean"]
        self.assertIsNone(view["question"]["purpose"])
        self.assertEqual(view["candidate_calculation"], mean.Purpose.SQUARE.value)
        self.assertIn("purpose", view["scope_unresolved_or_mismatched"])

    def test_unknown_membership_scope_and_known_difference_coexist(self):
        case = self.report["cases"]["missing_scope_and_membership"]
        codes = self.codes(case["finding_union"])
        self.assertTrue({"DENOM_MEMBERSHIP_UNKNOWN", "DENOM_POLICY_CHANGE", "MEAN_SCOPE_UNKNOWN"} <= codes)
        self.assertIsNone(case["denominator"]["procedure_traces"][1]["members"])
        self.assertIsNone(case["denominator"]["procedure_traces"][1]["denominator_value"])
        self.assertEqual(case["axis_statuses"]["physical"], "untested")
        self.assertEqual(case["axis_statuses"]["determination"], "failed")

    def test_consistent_local_trace_cannot_bypass_shared_unknown_gate(self):
        case = self.report["cases"]["shared_unknown_gate_even_for_same_policy"]
        self.assertTrue(all(t["qualified_within_constructed_scope"]
                            for t in case["denominator"]["procedure_traces"]))
        self.assertTrue(all(not r["outputs"] for r in self.runs(case)))
        self.assertIn("APP_UNRESOLVED", self.codes(case["denominator"]["record"]))
        self.assertIsNone(case["denominator"]["point_difference"])

    def test_false_labels_remain_diagnosed_beside_mean_loss(self):
        case = self.report["cases"]["false_shared_label_and_mean_loss"]
        self.assertEqual(case["denominator"]["declaration_comparison"]["state"],
                         ComparisonState.ELIGIBLE.value)
        self.assertTrue({"DENOM_DECLARATION_MISMATCH", "DENOM_POLICY_CHANGE", "MEAN_PURPOSE_LOSS"}
                        <= self.codes(case["finding_union"]))

    def test_multiple_numeric_coincidences_do_not_license_policy_equivalence(self):
        case = self.report["cases"]["multiple_coincidences"]
        for view in ("denominator", "distribution_mean"):
            comparison = case[view]["declaration_comparison"]
            self.assertEqual(comparison["previous"]["outputs"][0]["value"],
                             comparison["replacement"]["outputs"][0]["value"])
        self.assertFalse(case["denominator"]["interchangeability_established"])
        self.assertEqual(case["distribution_mean"]["universal_mean_sufficiency"], "NOT_ESTABLISHED")

    def test_bad_mean_binding_is_not_promoted_into_mean_target_loss(self):
        case = self.report["cases"]["inconsistent_mean_binding"]
        self.assertIn("MEAN_OPERAND_BINDING", self.codes(case["finding_union"]))
        self.assertNotIn("MEAN_PURPOSE_LOSS", self.codes(case["distribution_mean"]["record"]))
        self.assertIsNone(case["distribution_mean"]["audited_point_difference"])

    def test_instrument_failure_does_not_inherit_sibling_certificates(self):
        case = self.report["cases"]["independent_instrument_failure"]
        for side in ("previous", "replacement"):
            findings = case["denominator"]["declaration_comparison"][side]["record"]["findings"]
            self.assertFalse(any(f["axis"] == "instrument" and f["severity"] == "failed" for f in findings))
        child = case["distribution_mean"]["declaration_comparison"]["replacement"]
        self.assertEqual(child["outputs"], [])
        self.assertEqual(case["axis_statuses"]["instrument"], "failed")
        self.assertEqual(case["axis_statuses"]["physical"], "untested")
        self.assertEqual(case["denominator"]["axis_statuses"]["instrument"], "ok")

    def test_existing_physical_finding_is_preserved_independently(self):
        case = self.report["cases"]["independent_physical_failure"]
        self.assertTrue(all(not r["outputs"] for r in self.runs(case)))
        for view in ("denominator", "distribution_mean"):
            self.assertEqual(case[view]["physical_adequacy"], "FAILED")
            self.assertIn("CROSS_PLANTED_PHYSICAL_FINDING", self.codes(case[view]["record"]))
        self.assertEqual(case["axis_statuses"]["instrument"], "untested")

    def test_known_scope_mismatch_and_unknown_scope_are_both_retained(self):
        case = self.report["cases"]["known_mismatch_and_unknown_scope"]
        self.assertTrue({"DENOM_POLICY_CHANGE", "MEAN_SCOPE_MISMATCH", "MEAN_SCOPE_UNKNOWN"}
                        <= self.codes(case["finding_union"]))

    def test_empty_denominator_does_not_silence_separate_mean_loss(self):
        case = self.report["cases"]["empty_survivor_denominator_and_mean_loss"]
        self.assertIn("DENOM_EMPTY", self.codes(case["denominator"]["record"]))
        self.assertEqual(case["denominator"]["procedure_traces"][1]["denominator_value"], 0)
        self.assertEqual(case["denominator"]["declaration_comparison"]["replacement"]["outputs"], [])
        self.assertIn("MEAN_PURPOSE_LOSS", self.codes(case["distribution_mean"]["record"]))

    def test_reversed_execution_does_not_change_audit_results(self):
        forward = mean.plain(self.fresh())
        reverse = mean.plain(self.fresh(reverse_execution=True))
        self.assertNotEqual(forward.pop("execution_order"), reverse.pop("execution_order"))
        self.assertEqual(forward, reverse)

    def test_shared_context_does_not_allow_cross_chain_parentage(self):
        with patch.object(denominator, "audit_pair", wraps=denominator.audit_pair) as den_call, \
                patch.object(mean, "audit_pair", wraps=mean.audit_pair) as mean_call:
            self.fresh()
        den_a = den_call.call_args.args[0]
        mean_b = mean_call.call_args.args[1]
        comparison = compare_substitution(den_a, mean_b, "rate", "response", regression.DECISION)
        self.assertIsNone(comparison.point_difference)
        self.assertIn("MEASURAND_RUN_BINDING", {f.code for f in comparison.record.findings})

    def test_shared_composition_refuses_conflicts_and_stale_bindings(self):
        den_exp = denominator.experiment(denominator.fixture_census())
        mean_exp = mean.experiment(mean.fixture_distribution(), mean.fixture_question(mean.Purpose.SQUARE))
        context = replace(mean_exp.context, conditions=tuple(
            replace(c, value=2.5) if c.key == "energy" else c for c in mean_exp.context.conditions))
        rebound = replace(mean_exp, context=context,
                          boundary=replace(mean_exp.boundary, context_digest=context.digest()))
        with self.assertRaisesRegex(ValueError, "conflicting shared condition"):
            regression.shared_experiment(den_exp, rebound)
        with self.assertRaisesRegex(ValueError, "stale component binding"):
            regression.shared_experiment(den_exp, replace(mean_exp, context=context))
        diagnostic = ExperimentalDiagnostics("stale-context", FailureRecord(), regression.DECISION,
                                             regression.REFERENCE)
        with self.assertRaisesRegex(ValueError, "stale component binding"):
            regression.shared_experiment(den_exp, replace(mean_exp, diagnostics=(diagnostic,)))
        for boundary in (
            replace(mean_exp.boundary, quantity_units=(("energy", "wrong-unit"),)),
            replace(mean_exp.boundary, accounting=replace(
                mean_exp.boundary.accounting, declared_complete=False)),
        ):
            with self.subTest(boundary=boundary), self.assertRaisesRegex(
                    ValueError, "incompatible component reference"):
                regression.shared_experiment(den_exp, replace(mean_exp, boundary=boundary))
        old_adequacy = FailureRecord((Finding(
            Axis.PHYSICAL, Status.OK, "PLANTED_OLD_ADEQUACY",
            "Do not transport an old physical clearance into the shared context",
            "validation.test_cross_audit_regression", regression.REFERENCE),))
        diagnostic = ExperimentalDiagnostics(
            mean_exp.context.digest(), old_adequacy, regression.DECISION, regression.REFERENCE)
        with self.assertRaisesRegex(ValueError, "only source-structural diagnostics"):
            regression.shared_experiment(den_exp, replace(mean_exp, diagnostics=(diagnostic,)))

    def test_no_new_physical_or_temporal_claims_are_promoted(self):
        for name, case in self.report["cases"].items():
            if name != "independent_physical_failure":
                self.assertEqual(case["axis_statuses"]["physical"], "untested")
            self.assertEqual(case["empirical_support"], "NOT_PROMOTED")
            self.assertTrue(all(v == "NOT_ESTABLISHED"
                                for v in case["distribution_mean"]["property_inferences"].values()))

    def test_allowed_source_findings_retain_provenance_after_explicit_rebinding(self):
        case = regression.run_case(
            denominator.fixture_census(surviving=("UNENROLLED",)),
            mean.fixture_distribution(weights=(None, 1)), mean.fixture_question(mean.Purpose.SQUARE),
            calculation=mean.Purpose.SQUARE)
        self.assertTrue(all(d.context_digest == case["shared_context_digest"]
                            for d in case["shared_experiment"].diagnostics))
        for diagnostic in case["shared_experiment"].diagnostics:
            self.assertTrue(diagnostic.evidence)
            self.assertTrue(all(f.axis is Axis.DETERMINATION for f in diagnostic.record.findings))
        codes = {f.code for f in case["finding_union"].findings}
        self.assertTrue({"DENOM_FOREIGN_MEMBER", "MEAN_SOURCE_UNKNOWN"} <= codes)
        self.assertEqual(case["axis_statuses"]["physical"], "untested")

    def test_reports_keep_source_records_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "fresh"
            report = regression.run_regression(destination)
            before = (destination / "cross-audit-regression.json").read_bytes()
            self.assertEqual(json.loads(before), report)
            with self.assertRaises(FileExistsError):
                regression.run_regression(destination)
            self.assertEqual(before, (destination / "cross-audit-regression.json").read_bytes())
            self.assertIn("This does not establish",
                          (destination / "cross-audit-regression.md").read_text())


class CrossAuditMutationTests(unittest.TestCase):
    def test_three_rollup_mutants_fail_by_assertion_not_crash(self):
        target = inspect.getsource(regression.run_case)
        before = 'union = denominator_view["record"].merge(mean_view["record"])'
        self.assertEqual(target.count(before), 1)
        mutants = (
            ("denominator_only", 'union = denominator_view["record"]'),
            ("mean_only", 'union = mean_view["record"]'),
            ("all_findings_dropped", "union = FailureRecord()"),
        )
        for name, replacement in mutants:
            with self.subTest(mutant=name):
                namespace = dict(vars(regression))
                exec(compile(target.replace(before, replacement), f"<controlled-mutant:{name}>", "exec"),
                     namespace)
                with patch.object(regression, "run_case", namespace["run_case"]):
                    case = mean.plain(regression.run_case(
                        denominator.fixture_census(surviving=("A", "B")), mean.fixture_distribution(),
                        mean.fixture_question(mean.Purpose.SQUARE), calculation=mean.Purpose.SQUARE))
                expected = (case["denominator"]["record"]["findings"]
                            + case["distribution_mean"]["record"]["findings"])
                with self.assertRaises(AssertionError):
                    self.assertEqual(case["finding_union"]["findings"], expected)


if __name__ == "__main__":
    unittest.main()
