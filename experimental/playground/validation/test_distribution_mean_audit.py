"""Finite constructed controls, information-loss cases and diagnostic guards."""

import inspect
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

from ..applicability.mapping import ConditionBasis
from ..audits import distribution_mean_process as audit
from ..equations.adapter import EquationRegistry
from ..equations.measurand import ComparisonState
from ..equations.substitution import ExperimentalDiagnostics, RunState, execute, substitute
from ..failures import Axis, FailureRecord, Finding, Status


class DistributionMeanTests(unittest.TestCase):
    def setUp(self):
        self.broad = audit.fixture_distribution()
        self.narrow = audit.fixture_distribution(values=(1, 1), source_id="point-at-one")
        self.linear = audit.fixture_question(audit.Purpose.LINEAR)
        self.square = audit.fixture_question(audit.Purpose.SQUARE)

    def run_case(self, source=None, question=None, *, calculation=audit.Purpose.SQUARE, **kwargs):
        return audit.run_case(
            self.broad if source is None else source,
            self.square if question is None else question, calculation=calculation, **kwargs)

    def codes(self, record):
        return {f.code for f in record.findings}

    def assert_withheld(self, result):
        self.assertEqual(result["conclusion"], audit.Conclusion.WITHHELD.value)
        self.assertIsNone(result["usable_for_selected_target_in_this_case"])
        self.assertIsNone(result["audited_point_difference"])
        self.assertIsNone(result["exact_replacement_minus_reference"])

    def test_same_mean_does_not_preserve_second_moment(self):
        a, b, broad = self.run_case()
        c, d, narrow = self.run_case(self.narrow)
        self.assertEqual(broad["source_moments"]["m"], narrow["source_moments"]["m"])
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (2.0, 1.0))
        self.assertEqual((c.outputs[0].value, d.outputs[0].value), (1.0, 1.0))
        self.assertEqual(broad["conclusion"], audit.Conclusion.LOSS.value)
        self.assertEqual(narrow["conclusion"], audit.Conclusion.PRESERVED.value)
        self.assertEqual(broad["exact_replacement_minus_reference"], "-1")
        self.assertEqual(broad["source_moments"]["variance"], "1")
        self.assertEqual(narrow["source_moments"]["variance"], "0")

    def test_linear_target_has_positive_controls_for_both_sources(self):
        for source in (self.broad, self.narrow):
            with self.subTest(source=source.source_id):
                a, b, result = self.run_case(source, self.linear, calculation=audit.Purpose.LINEAR)
                self.assertEqual((a.outputs[0].value, b.outputs[0].value), (2.0, 2.0))
                self.assertEqual(result["conclusion"], audit.Conclusion.PRESERVED.value)
                self.assertTrue(result["usable_for_selected_target_in_this_case"])
                self.assertEqual(result["exact_replacement_minus_reference"], "0")
                self.assertEqual(result["universal_mean_sufficiency"], "NOT_ESTABLISHED")

    def test_arithmetic_validity_and_target_loss_remain_separate(self):
        a, b, result = self.run_case()
        self.assertEqual(result["declaration_comparison"]["state"], ComparisonState.ELIGIBLE.value)
        self.assertEqual(result["audited_point_difference"], -1.0)
        self.assertEqual(result["record"].determination, Status.FAILED)
        self.assertIn("MEAN_PURPOSE_LOSS", self.codes(result["record"]))
        self.assertEqual(result["record"].instrument, Status.OK)
        self.assertEqual(result["record"].physical, Status.UNTESTED)
        for run in (a, b):
            self.assertEqual(run.state, RunState.COMPUTED)
            self.assertEqual(run.record.instrument, Status.OK)
            self.assertNotIn("MEAN_PURPOSE_LOSS", self.codes(run.record))
            self.assertIsNone(run.outputs[0].uncertainty)
        self.assertEqual(a.equation.outputs[0].measurand.quantity,
                         b.equation.outputs[0].measurand.quantity)

    def test_complete_gated_runs_and_lineage_are_retained(self):
        a, b, _ = self.run_case()
        self.assertEqual(a.experiment, b.experiment)
        self.assertEqual(b.parent_run_digest, a.digest())
        self.assertNotEqual(a.plan.equation_digest, b.plan.equation_digest)
        for run in (a, b):
            self.assertIsNotNone(run.l0)
            self.assertIsNotNone(run.applicability)
            self.assertIsNotNone(run.known_answer)
            self.assertIsNotNone(run.null)
            self.assertTrue(run.known_answer.validated_within_tested_cases)
            self.assertTrue(run.null.clean_within_tested_cases)

    def test_unequal_weights_are_not_defaulted_to_unweighted_average(self):
        source = audit.fixture_distribution(values=(-2, 2), weights=(1, 3))
        parameters = audit.source_parameters(source)
        self.assertEqual(parameters["p"], Fraction(1, 4))
        self.assertEqual(parameters["m"], Fraction(1))
        self.assertEqual(parameters["second"], Fraction(4))
        _, _, result = self.run_case(source)
        self.assertEqual(result["exact_replacement_minus_reference"], "-3")
        self.assertEqual(result["conclusion"], audit.Conclusion.LOSS.value)

    def test_exact_target_residual_is_separate_from_floating_point_difference(self):
        source = audit.fixture_distribution(weights=(1, 2))
        a, b, result = self.run_case(source, self.linear, calculation=audit.Purpose.LINEAR)
        self.assertEqual(result["source_moments"]["m"], "4/3")
        self.assertEqual(result["exact_replacement_minus_reference"], "0")
        self.assertEqual(result["audited_point_difference"], b.outputs[0].value - a.outputs[0].value)
        self.assertEqual(result["conclusion"], audit.Conclusion.PRESERVED.value)
        self.assertIsNone(b.outputs[0].uncertainty)

    def test_zero_mean_is_not_zero_square_response(self):
        a, b, result = self.run_case(audit.fixture_distribution(values=(-1, 1)))
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (1.0, 0.0))
        self.assertEqual(result["conclusion"], audit.Conclusion.LOSS.value)
        self.assertEqual(result["property_inferences"]["physical_absence"], "NOT_ESTABLISHED")

    def test_zero_point_does_not_establish_physical_absence(self):
        a, b, result = self.run_case(audit.fixture_distribution(values=(0, 0)))
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (0.0, 0.0))
        self.assertEqual(result["conclusion"], audit.Conclusion.PRESERVED.value)
        self.assertEqual(result["physical_adequacy"], "UNTESTED")
        self.assertTrue(all(v == "NOT_ESTABLISHED" for v in result["property_inferences"].values()))

    def test_degenerate_coincidence_is_not_a_general_license(self):
        _, _, result = self.run_case(self.narrow)
        self.assertEqual(result["conclusion"], audit.Conclusion.PRESERVED.value)
        self.assertEqual(result["universal_mean_sufficiency"], "NOT_ESTABLISHED")
        self.assertIn("original atom values and weights",
                      result["information_not_carried_by_replacement"][0])

    def test_missing_scope_is_never_filled_from_known_source(self):
        for key in ("purpose", "population", "window", "domain", "conditions"):
            with self.subTest(key=key):
                a, b, result = self.run_case(question=replace(self.square, **{key: None}))
                self.assert_withheld(result)
                self.assertEqual((a.outputs, b.outputs), ((), ()))
                self.assertIsNone(getattr(result["question"], key))
                self.assertIn(key, result["scope_unresolved_or_mismatched"])
                self.assertIn("MEAN_SCOPE_UNKNOWN", self.codes(result["record"]))
                self.assertEqual(result["candidate_calculation"], audit.Purpose.SQUARE.value)

    def test_known_scope_mismatch_is_not_hidden_by_unknown_scope(self):
        question = replace(self.square, population="another population", window=None)
        _, _, result = self.run_case(question=question)
        self.assert_withheld(result)
        self.assertIn("MEAN_SCOPE_MISMATCH", self.codes(result["record"]))
        self.assertIn("MEAN_SCOPE_UNKNOWN", self.codes(result["record"]))
        self.assertEqual(result["record"].determination, Status.FAILED)

    def test_candidate_calculation_is_not_inferred_from_missing_purpose(self):
        with self.assertRaises(ValueError):
            audit.run_case(self.broad, replace(self.square, purpose=None), calculation=None)

    def test_each_known_scope_mismatch_withholds(self):
        for key, value in (
            ("population", "another population"), ("window", "another finite window"),
            ("domain", "another domain"), ("conditions", ("another protocol",)),
            ("purpose", audit.Purpose.LINEAR),
        ):
            with self.subTest(key=key):
                _, _, result = self.run_case(question=replace(self.square, **{key: value}))
                self.assert_withheld(result)
                self.assertIn("MEAN_SCOPE_MISMATCH", self.codes(result["record"]))

    def test_unknown_weight_is_not_zero_mass(self):
        _, _, unknown = self.run_case(audit.fixture_distribution(weights=(1, None)))
        _, _, empty = self.run_case(audit.fixture_distribution(weights=(0, 0)))
        self.assert_withheld(unknown)
        self.assert_withheld(empty)
        self.assertIsNone(unknown["source_moments"]["total_weight"])
        self.assertEqual(empty["source_moments"]["total_weight"], "0")
        self.assertIsNone(unknown["source_moments"]["m"])
        self.assertIsNone(empty["source_moments"]["m"])
        self.assertIn("MEAN_SOURCE_UNKNOWN", self.codes(unknown["record"]))
        self.assertIn("MEAN_EMPTY_MASS", self.codes(empty["record"]))

    def test_unknown_value_is_not_filled_with_zero(self):
        a, b, result = self.run_case(audit.fixture_distribution(values=(None, 2)))
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assert_withheld(result)
        self.assertIsNone(result["source"].atoms[0].value)

    def test_negative_and_unknown_weights_preserve_both_findings(self):
        a, b, result = self.run_case(audit.fixture_distribution(weights=(-1, None)))
        self.assertEqual((a.outputs, b.outputs), ((), ()))
        self.assertIn("MEAN_NEGATIVE_WEIGHT", self.codes(result["record"]))
        self.assertIn("MEAN_SOURCE_UNKNOWN", self.codes(result["record"]))
        self.assertEqual(result["record"].determination, Status.FAILED)
        self.assertEqual(result["source"].atoms[0].weight, -1)
        self.assert_withheld(result)

    def test_zero_weight_atom_with_positive_total_is_admissible(self):
        a, b, result = self.run_case(audit.fixture_distribution(weights=(0, 1)))
        self.assertEqual((a.outputs[0].value, b.outputs[0].value), (4.0, 4.0))
        self.assertEqual(result["conclusion"], audit.Conclusion.PRESERVED.value)

    def test_false_mean_or_probability_binding_is_not_valid_target_loss_evidence(self):
        for overrides in ({"m": 2.0}, {"p": 0.25}):
            with self.subTest(overrides=overrides):
                _, _, result = self.run_case(overrides=overrides)
                self.assertEqual(result["declaration_comparison"]["state"], ComparisonState.ELIGIBLE.value)
                self.assert_withheld(result)
                self.assertIn("MEAN_OPERAND_BINDING", self.codes(result["record"]))

    def test_changed_raw_source_with_same_normalized_moments_cannot_rebind_run(self):
        a, _, _ = self.run_case()
        altered = replace(self.broad, atoms=(audit.Atom(0, 2), audit.Atom(2, 2)))
        self.assertEqual(audit.source_parameters(altered)["m"], audit.source_parameters(self.broad)["m"])
        traced = audit.trace(a, altered, self.square, audit.Purpose.SQUARE, False)
        self.assertFalse(traced["qualified_within_constructed_scope"])
        self.assertIn("MEAN_SOURCE_BINDING", self.codes(traced["record"]))

    def test_operand_provenance_is_required_even_when_value_matches(self):
        a, _, _ = self.run_case()
        context = replace(a.experiment.context, conditions=tuple(
            replace(c, basis=ConditionBasis.SELECTED, evidence=()) if c.key == "m" else c
            for c in a.experiment.context.conditions))
        altered = replace(a, experiment=replace(a.experiment, context=context))
        traced = audit.trace(altered, self.broad, self.square, audit.Purpose.SQUARE, False)
        self.assertIn("MEAN_OPERAND_BINDING", self.codes(traced["record"]))

    def test_retained_operands_and_point_are_checked_against_exact_oracle(self):
        a, _, _ = self.run_case()
        forged = replace(a, inputs=(("x0", 0.0), ("x1", 9.0), ("p", 0.5)))
        traced = audit.trace(forged, self.broad, self.square, audit.Purpose.SQUARE, False)
        self.assertIn("MEAN_EXECUTED_INPUTS", self.codes(traced["record"]))
        forged = replace(a, outputs=(replace(a.outputs[0], value=99.0),))
        traced = audit.trace(forged, self.broad, self.square, audit.Purpose.SQUARE, False)
        self.assertIn("MEAN_POINT_ORACLE", self.codes(traced["record"]))

    def test_equivalent_but_unsupported_formula_is_withheld_not_guessed(self):
        _, _, result = self.run_case(
            question=self.linear, calculation=audit.Purpose.LINEAR, expression="m+m")
        self.assertEqual(result["declaration_comparison"]["state"], ComparisonState.ELIGIBLE.value)
        self.assert_withheld(result)
        self.assertIn("MEAN_UNSUPPORTED_PROCEDURE", self.codes(result["record"]))

    def test_missing_identity_is_not_repaired_by_local_procedure_trace(self):
        _, _, result = self.run_case(missing_identity=True)
        self.assert_withheld(result)
        self.assertTrue(all(t["qualified_within_constructed_scope"] for t in result["procedure_traces"]))

    def diagnostic_case(self, *, physical=False):
        exp = audit.experiment(self.broad, self.square)
        if physical:
            record = FailureRecord((Finding(
                Axis.PHYSICAL, Status.FAILED, "PLANTED_PHYSICAL_FINDING",
                "Constructed independent finding, not a real observation",
                "validation.test_distribution_mean_audit", audit.REFERENCE),))
            exp = replace(exp, diagnostics=(ExperimentalDiagnostics(
                exp.context.digest(), record, audit.DECISION, audit.REFERENCE),))
        first = audit.model(self.broad, self.square, exp, audit.Purpose.SQUARE, False)
        second = audit.model(self.broad, self.square, exp, audit.Purpose.SQUARE, True)
        registry = EquationRegistry()
        registry.register(first)
        registry.register(second)
        a = execute(registry, first.equation_id, first.revision, exp,
                    audit.plan(first, exp, audit.Purpose.SQUARE, False), audit.DECISION)
        plan = audit.plan(second, exp, audit.Purpose.SQUARE, True)
        if not physical:
            plan = replace(plan, known_answers=(
                replace(plan.known_answers[0], expected=(("response", 99.0),)),
            ) + plan.known_answers[1:])
        b = substitute(a, registry, second.equation_id, second.revision, plan, audit.DECISION)
        return a, b, audit.audit_pair(a, b, self.broad, self.square, audit.Purpose.SQUARE)

    def test_failed_instrument_cannot_be_overridden_by_consistent_trace(self):
        a, b, result = self.diagnostic_case()
        self.assertEqual(a.record.instrument, Status.OK)
        self.assertEqual(b.record.instrument, Status.FAILED)
        self.assertEqual(b.outputs, ())
        self.assertTrue(result["procedure_traces"][1]["qualified_within_constructed_scope"])
        self.assert_withheld(result)
        self.assertEqual(result["record"].instrument, Status.FAILED)
        self.assertEqual(result["record"].physical, Status.UNTESTED)

    def test_independent_physical_finding_is_preserved(self):
        _, _, result = self.diagnostic_case(physical=True)
        self.assert_withheld(result)
        self.assertEqual(result["physical_adequacy"], "FAILED")
        self.assertEqual(result["record"].physical, Status.FAILED)
        self.assertEqual(result["record"].instrument, Status.UNTESTED)

    def test_no_temporal_joint_or_thermodynamic_properties_are_inferred(self):
        report = audit.inspect_process()
        for case in report["cases"].values():
            self.assertEqual(case["temporal_order"], "NOT_SUPPLIED")
            self.assertEqual(case["joint_structure"], "NOT_SUPPLIED")
            self.assertTrue(all(v == "NOT_ESTABLISHED" for v in case["property_inferences"].values()))
            self.assertEqual(case["empirical_support"], "NOT_PROMOTED")

    def test_records_are_immutable_and_missing_values_explicit(self):
        with self.assertRaises(FrozenInstanceError):
            self.broad.atoms = ()
        for kwargs in ({"evidence": ()}, {"atoms": []}, {"decision": None},
                       {"population": "unknown"}, {"evidence": ("not-evidence",)}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                replace(self.broad, **kwargs)
        for atom in ((True, 1), (1, True), (0, 1.5), (11, 1)):
            with self.subTest(atom=atom), self.assertRaises(ValueError):
                audit.Atom(*atom)
        with self.assertRaises(ValueError):
            replace(self.square, purpose="square")

    def test_reports_preserve_original_records_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "fresh"
            report = audit.run_audit(destination)
            before = (destination / "distribution-to-mean-audit.json").read_bytes()
            self.assertEqual(json.loads(before), report)
            with self.assertRaises(FileExistsError):
                audit.run_audit(destination)
            self.assertEqual(before, (destination / "distribution-to-mean-audit.json").read_bytes())
            for case in report["cases"].values():
                self.assertEqual(len(case["source"]["atoms"]), 2)
                for side in ("previous", "replacement"):
                    run = case["declaration_comparison"][side]
                    for key in ("experiment", "plan", "selection", "record", "equation"):
                        self.assertIn(key, run)
            self.assertIn("This does not establish",
                          (destination / "distribution-to-mean-audit.md").read_text())


class DistributionMeanMutationTests(unittest.TestCase):
    def test_four_controlled_mutants_are_caught_by_assertion_not_crash(self):
        mutants = (
            ("mean_declared_sufficient_for_square", "audit_pair",
             'exact_error = Fraction(0) if calculation is Purpose.LINEAR else mean ** 2 - parameters["second"]',
             "exact_error = Fraction(0)", "test_same_mean_does_not_preserve_second_moment"),
            ("weights_ignored", "source_parameters", "p = Fraction(weights[0], total)",
             "p = Fraction(1, 2)", "test_unequal_weights_are_not_defaulted_to_unweighted_average"),
            ("unresolved_scope_omitted", "audit_pair", "unresolved.append(key)",
             "pass", "test_missing_scope_is_never_filled_from_known_source"),
            ("source_derivation_guard_removed", "trace",
             'add("MEAN_OPERAND_BINDING", f"{name}: operand disagrees with source derivation/provenance")',
             "pass", "test_operand_provenance_is_required_even_when_value_matches"),
        )
        for name, target, before, after, check in mutants:
            with self.subTest(mutant=name):
                original = inspect.getsource(getattr(audit, target))
                self.assertGreater(original.count(before), 0)
                namespace = dict(vars(audit))
                exec(compile(original.replace(before, after), f"<controlled-mutant:{name}>", "exec"),
                     namespace)
                result = unittest.TestResult()
                with patch.object(audit, target, namespace[target]):
                    DistributionMeanTests(check).run(result)
                self.assertEqual(result.errors, [], "a crash is not guard detection")
                self.assertGreater(len(result.failures), 0, "targeted assertions must detect the defect")


if __name__ == "__main__":
    unittest.main()
