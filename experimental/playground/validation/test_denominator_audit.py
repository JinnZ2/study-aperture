"""Constructed denominator-procedure checks; no empirical cohort conclusions."""

import json
import inspect
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch

from ..audits import denominator_process as audit
from ..applicability.mapping import ConditionBasis
from ..equations.adapter import EquationRegistry
from ..equations.measurand import ComparisonState
from ..equations.substitution import ExperimentalDiagnostics, execute, substitute
from ..failures import Axis, FailureRecord, Finding, Status


class DenominatorAuditTests(unittest.TestCase):
    def setUp(self):
        self.full = audit.fixture_census()
        self.loss = audit.fixture_census(surviving=("A", "B"), window="t1-to-t2")

    def codes(self, trace):
        return {f.code for f in trace["record"].findings}

    def assert_void(self, result):
        self.assertEqual(result["audited_comparison"], ComparisonState.VOID.value)
        self.assertIsNone(result["point_difference"])
        self.assertFalse(result["interchangeability_established"])

    def test_coincidence_does_not_establish_policy_equivalence(self):
        a, b, result = audit.run_case(self.full)
        self.assertEqual(a.outputs[0].value, 0.5)
        self.assertEqual(b.outputs[0].value, 0.5)
        self.assertTrue(result["same_members_at_this_snapshot"])
        self.assertTrue(result["selection_policies_differ"])
        self.assert_void(result)
        self.assertTrue(all(t["qualified_within_constructed_scope"]
                            for t in result["procedure_traces"]))

    def test_attrition_is_counterexample_not_a_cross_context_substitution(self):
        a, b, result = audit.run_case(self.loss)
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (0.5, 1.0))
        self.assert_void(result)
        self.assertEqual(a.experiment, b.experiment)
        self.assertEqual(b.parent_run_digest, a.digest())
        c, _, _ = audit.run_case(self.full)
        self.assertNotEqual(c.experiment.context.digest(), a.experiment.context.digest())
        self.assertEqual([t["oracle_rate"] for t in result["procedure_traces"]], ["1/2", "1"])

    def test_zero_numerator_can_hide_different_denominators(self):
        a, b, result = audit.run_case(replace(self.loss, outcome_members=()))
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (0.0, 0.0))
        self.assertFalse(result["same_members_at_this_snapshot"])
        self.assert_void(result)
        self.assertEqual(result["physical_adequacy"], "UNTESTED")

    def test_false_shared_declaration_at_coincidence_is_caught(self):
        a, b, result = audit.run_case(self.full, right_declared=audit.Policy.INITIAL)
        self.assertEqual(result["declaration_comparison"]["state"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(result["declaration_comparison"]["point_difference"], 0.0)
        self.assertIn("DENOM_DECLARATION_MISMATCH", self.codes(result["procedure_traces"][1]))
        self.assert_void(result)
        self.assertEqual((a.record.instrument, b.record.instrument), (Status.OK, Status.OK))
        self.assertEqual(result["record"].physical, Status.UNTESTED)
        self.assertEqual(result["record"].determination, Status.FAILED)

    def test_false_shared_declaration_after_attrition_preserves_original_result(self):
        _, _, result = audit.run_case(self.loss, right_declared=audit.Policy.INITIAL)
        self.assertEqual(result["declaration_comparison"]["point_difference"], 0.5)
        self.assert_void(result)

    def test_both_shared_labels_can_be_wrong_without_actual_policy_change(self):
        _, _, result = audit.run_case(
            self.loss, left_policy=audit.Policy.SURVIVING,
            left_declared=audit.Policy.INITIAL, right_declared=audit.Policy.INITIAL)
        self.assertEqual(result["declaration_comparison"]["state"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertIsNone(result["point_difference"])
        self.assertTrue(all("DENOM_DECLARATION_MISMATCH" in self.codes(t)
                            for t in result["procedure_traces"]))

    def test_same_policy_different_ratio_form_is_scoped_positive_control(self):
        a, b, result = audit.run_case(
            self.loss, right_policy=audit.Policy.INITIAL, right_declared=audit.Policy.INITIAL,
            expression="n*(1/d)")
        self.assertEqual(result["audited_comparison"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(result["point_difference"], 0.0)
        self.assertFalse(result["interchangeability_established"])
        self.assertNotEqual(a.equation.digest(), b.equation.digest())
        for run in (a, b):
            self.assertIsNotNone(run.known_answer)
            self.assertIsNotNone(run.null)
            self.assertIsNotNone(run.l0)
            self.assertIsNotNone(run.applicability)
            self.assertIsNone(run.outputs[0].uncertainty)
            self.assertEqual(run.record.physical, Status.UNTESTED)

    def test_survivor_policy_is_also_a_positive_control_not_a_ranked_inferior(self):
        _, _, result = audit.run_case(
            self.loss, left_policy=audit.Policy.SURVIVING,
            left_declared=audit.Policy.SURVIVING, expression="n*(1/d)")
        self.assertEqual(result["audited_comparison"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(result["point_difference"], 0.0)

    def test_missing_membership_remains_unknown_not_zero(self):
        a, b, result = audit.run_case(
            audit.fixture_census(surviving=None), left_policy=audit.Policy.SURVIVING,
            left_declared=audit.Policy.SURVIVING)
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        for trace in result["procedure_traces"]:
            self.assertIsNone(trace["members"])
            self.assertIsNone(trace["denominator_value"])
            self.assertIn("DENOM_MEMBERSHIP_UNKNOWN", self.codes(trace))
            self.assertFalse(trace["qualified_within_constructed_scope"])

    def test_trace_consistency_cannot_bypass_broader_unknown_context_gate(self):
        a, b, result = audit.run_case(
            audit.fixture_census(surviving=None), right_policy=audit.Policy.INITIAL,
            right_declared=audit.Policy.INITIAL)
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertTrue(all(t["qualified_within_constructed_scope"]
                            for t in result["procedure_traces"]))
        self.assertIn("APP_UNRESOLVED", {f.code for f in a.record.findings})
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertIsNone(result["point_difference"])

    def test_explicit_zero_denominator_is_undefined_not_zero_rate(self):
        a, b, result = audit.run_case(
            audit.fixture_census(surviving=(), outcomes=()),
            left_policy=audit.Policy.SURVIVING, left_declared=audit.Policy.SURVIVING)
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertIsNone(result["point_difference"])
        for trace in result["procedure_traces"]:
            self.assertEqual(trace["members"], ())
            self.assertEqual(trace["denominator_value"], 0)
            self.assertIn("DENOM_EMPTY", self.codes(trace))
            self.assertIsNone(trace["oracle_rate"])

    def test_explicit_zero_initial_enrollment_is_also_undefined(self):
        census = replace(self.full, enrolled=(), surviving=(), outcome_members=())
        a, b, result = audit.run_case(
            census, right_policy=audit.Policy.INITIAL, right_declared=audit.Policy.INITIAL)
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertTrue(all("DENOM_EMPTY" in self.codes(t) for t in result["procedure_traces"]))

    def test_known_policy_difference_is_not_masked_by_unknown_membership(self):
        _, _, result = audit.run_case(audit.fixture_census(surviving=None))
        self.assert_void(result)
        self.assertIn("DENOM_MEMBERSHIP_UNKNOWN", self.codes(result["procedure_traces"][1]))
        self.assertEqual(result["record"].determination, Status.FAILED)

    def test_missing_declaration_is_not_treated_as_matching(self):
        _, _, result = audit.run_case(
            self.loss, right_policy=audit.Policy.INITIAL, right_declared=None)
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertIn("DENOM_DECLARATION_UNKNOWN", self.codes(result["procedure_traces"][1]))

    def test_equal_count_does_not_license_unenrolled_replacement_members(self):
        census = audit.fixture_census(surviving=("A", "B", "X", "Y"))
        a, b, result = audit.run_case(census)
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertEqual(len(census.enrolled), len(census.surviving))
        self.assertFalse(result["same_members_at_this_snapshot"])
        self.assertIn("DENOM_FOREIGN_MEMBER", self.codes(result["procedure_traces"][1]))
        self.assertEqual(result["census"].surviving, ("A", "B", "X", "Y"))

    def test_duplicate_ids_are_preserved_but_not_double_counted_as_valid_members(self):
        a, b, result = audit.run_case(audit.fixture_census(surviving=("A", "A")))
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertIn("DENOM_DUPLICATE_MEMBER", self.codes(result["procedure_traces"][1]))
        self.assertEqual(result["census"].surviving, ("A", "A"))

    def test_count_claim_is_checked_against_membership_not_just_its_digest_label(self):
        a, b, result = audit.run_case(
            self.loss, right_declared=audit.Policy.INITIAL, count_overrides={"surviving_count": 4})
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (0.5, 0.5))
        self.assertIn("DENOM_VALUE_MISMATCH", self.codes(result["procedure_traces"][1]))
        self.assert_void(result)

    def test_census_mutation_with_unchanged_count_cannot_rebind_existing_run(self):
        a, _, _ = audit.run_case(self.full)
        altered = replace(self.full, enrolled=("A", "B", "C", "E"),
                          surviving=("A", "B", "C", "E"))
        self.assertNotEqual(altered.digest(), self.full.digest())
        trace = audit.trace_denominator(a, altered)
        self.assertIn("DENOM_SOURCE_BINDING", self.codes(trace))
        self.assertIn("DENOM_OPERAND_PROVENANCE", self.codes(trace))

    def test_procedure_outside_closed_contract_is_withheld_even_with_shared_labels(self):
        _, _, result = audit.run_case(
            self.loss, right_policy=audit.Policy.INITIAL, right_declared=audit.Policy.INITIAL,
            expression="n/(d+1)")
        self.assertIn("DENOM_UNSUPPORTED_PROCEDURE", self.codes(result["procedure_traces"][1]))
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertIsNone(result["point_difference"])

    def test_failed_known_answer_cannot_be_overridden_by_consistent_procedure(self):
        exp = audit.experiment(self.full)
        first = audit.model(self.full, exp, audit.Policy.INITIAL, audit.Policy.INITIAL,
                            revision="first")
        second = replace(first, revision="second")
        registry = EquationRegistry()
        registry.register(first)
        registry.register(second)
        a = execute(registry, first.equation_id, first.revision,
                    exp, audit.plan(first, exp), audit.DECISION)
        good = audit.plan(second, exp)
        bad_case = replace(good.known_answers[0], expected=(("rate", 99.0),))
        bad = replace(good, known_answers=(bad_case,) + good.known_answers[1:])
        b = substitute(a, registry, second.equation_id, second.revision, bad, audit.DECISION)
        result = audit.audit_pair(a, b, self.full)
        self.assertEqual(a.record.instrument, Status.OK)
        self.assertEqual(b.record.instrument, Status.FAILED)
        self.assertEqual(b.outputs, ())
        self.assertTrue(result["procedure_traces"][1]["qualified_within_constructed_scope"])
        self.assertEqual(result["audited_comparison"], ComparisonState.WITHHELD.value)
        self.assertEqual(result["record"].instrument, Status.FAILED)
        self.assertEqual(result["record"].physical, Status.UNTESTED)
        self.assertIsNone(result["point_difference"])

    def test_existing_physical_finding_is_retained_not_relabelled_untested(self):
        exp = audit.experiment(self.full)
        physical = Finding(
            Axis.PHYSICAL, Status.FAILED, "PLANTED_PHYSICAL_FINDING",
            "Constructed independent physical-axis finding, not a real observation",
            "validation.test_denominator_audit", audit.evidence(self.full))
        exp = replace(exp, diagnostics=(ExperimentalDiagnostics(
            exp.context.digest(), FailureRecord((physical,)), audit.DECISION,
            audit.evidence(self.full)),))
        first = audit.model(self.full, exp, audit.Policy.INITIAL, audit.Policy.INITIAL,
                            revision="first")
        second = replace(first, revision="second")
        registry = EquationRegistry()
        registry.register(first)
        registry.register(second)
        a = execute(registry, first.equation_id, first.revision,
                    exp, audit.plan(first, exp), audit.DECISION)
        b = substitute(a, registry, second.equation_id, second.revision,
                       audit.plan(second, exp), audit.DECISION)
        result = audit.audit_pair(a, b, self.full)
        self.assertEqual(result["record"].physical, Status.FAILED)
        self.assertEqual(result["physical_adequacy"], "FAILED")
        self.assertEqual(result["record"].instrument, Status.UNTESTED)
        self.assertIsNone(result["point_difference"])

    def test_missing_provenance_on_operand_cannot_be_laundered_by_matching_count(self):
        a, _, _ = audit.run_case(self.full)
        context = replace(a.experiment.context, conditions=tuple(
            replace(c, evidence=(), basis=ConditionBasis.SELECTED)
            if c.key == "enrolled_count" else c
            for c in a.experiment.context.conditions))
        altered = replace(a, experiment=replace(a.experiment, context=context))
        self.assertIn("DENOM_OPERAND_PROVENANCE",
                      self.codes(audit.trace_denominator(altered, self.full)))

    def test_retained_executed_operands_and_point_are_checked(self):
        a, _, _ = audit.run_case(self.full)
        forged = replace(a, inputs=(("n", 2.0), ("d", 2.0)))
        self.assertIn("DENOM_EXECUTED_INPUTS", self.codes(audit.trace_denominator(forged, self.full)))
        forged = replace(a, outputs=(replace(a.outputs[0], value=9.0),))
        self.assertIn("DENOM_POINT_ORACLE", self.codes(audit.trace_denominator(forged, self.full)))

    def test_census_is_immutable_and_evidence_is_required(self):
        with self.assertRaises(FrozenInstanceError):
            self.full.surviving = ()
        for changes in ({"evidence": ()}, {"surviving": ["A"]}, {"enrolled": None},
                        {"decision": None}, {"evidence": ("not-evidence",)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.full, **changes)

    def test_output_preserves_both_runs_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "fresh"
            report = audit.run_audit(destination)
            before = (destination / "denominator-change-audit.json").read_bytes()
            with self.assertRaises(FileExistsError):
                audit.run_audit(destination)
            self.assertEqual(before, (destination / "denominator-change-audit.json").read_bytes())
            self.assertEqual(json.loads(before), report)
            for case in report["cases"].values():
                self.assertEqual(case["empirical_support"], "NOT_PROMOTED")
                self.assertEqual(case["record"]["findings"], audit.plain(case["record"])["findings"])
                for side in ("previous", "replacement"):
                    run = case["declaration_comparison"][side]
                    self.assertIn("plan", run)
                    self.assertIn("experiment", run)
                    self.assertIn("selection", run)
                    self.assertIn("record", run)
            self.assertIn("This does not establish",
                          (destination / "denominator-change-audit.md").read_text())


class DenominatorGuardMutationTests(unittest.TestCase):
    def test_four_controlled_guard_mutants_fail_by_assertion_not_crash(self):
        mutants = (
            (
                "policy_change_ignored", "audit_pair",
                'known_change = (left["policy"] is not None and right["policy"] is not None\n'
                '                    and left["policy"] != right["policy"])',
                "known_change = False",
                "test_false_shared_declaration_at_coincidence_is_caught",
            ),
            (
                "false_declaration_accepted", "trace_denominator",
                "elif declaration.normalizer != policy.value:",
                "elif False:",
                "test_both_shared_labels_can_be_wrong_without_actual_policy_change",
            ),
            (
                "cardinality_guard_removed", "trace_denominator",
                "if members is not None and actual_value != len(members):",
                "if False:",
                "test_count_claim_is_checked_against_membership_not_just_its_digest_label",
            ),
            (
                "unknown_count_defaulted_to_zero", "trace_denominator",
                "actual_value = None if condition is None else condition.value",
                "actual_value = 0 if condition is None or condition.value is None else condition.value",
                "test_missing_membership_remains_unknown_not_zero",
            ),
        )
        for name, target, before, after, check in mutants:
            with self.subTest(mutant=name):
                original = inspect.getsource(getattr(audit, target))
                self.assertEqual(original.count(before), 1, "mutation must touch exactly its intended guard")
                namespace = dict(vars(audit))
                exec(compile(original.replace(before, after), f"<controlled-mutant:{name}>", "exec"),
                     namespace)
                result = unittest.TestResult()
                with patch.object(audit, target, namespace[target]):
                    DenominatorAuditTests(check).run(result)
                self.assertEqual(result.errors, [], "a crash is not successful mutant detection")
                self.assertEqual(len(result.failures), 1, "the guard test must detect the planted defect")


if __name__ == "__main__":
    unittest.main()
