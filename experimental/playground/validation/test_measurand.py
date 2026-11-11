"""Constructed identity challenges: equal numbers must not license unlike quantities."""

import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from unittest.mock import patch

from ..applicability.example import DECISION, support
from ..applicability.mapping import ApplicabilityState
from ..equations.adapter import EquationRegistry, OutputPort, _calculate
from ..equations.example import fixture_experiment
from ..equations.measurand import (
    IDENTITY_FIELDS, ComparisonState, IdentityState, RouteState,
    compare_substitution,
)
from ..equations.measurand_example import (
    declaration, model, plan, run_pair, run_probe,
)
from ..equations.substitution import ExperimentalDiagnostics, RunState, execute, substitute
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status


class MeasurandTests(unittest.TestCase):
    def setUp(self):
        self.experiment = fixture_experiment()
        self.identity = declaration(self.experiment)

    def pair(self, identity=None, **kwargs):
        # None here selects the standard test fixture only. Missing declarations
        # are exercised explicitly through run_pair(None, None).
        return run_pair(self.identity, self.identity if identity is None else identity,
                        **kwargs)

    def test_equal_names_units_values_do_not_establish_same_object(self):
        a, b, comparison = self.pair(replace(self.identity, object_of="another object"))
        self.assertIs(a.state, RunState.COMPUTED)
        self.assertIs(b.state, RunState.COMPUTED)
        self.assertEqual(a.outputs, b.outputs)
        self.assertEqual(a.equation.property, b.equation.property)
        self.assertIs(comparison.identity, IdentityState.MISMATCH)
        self.assertIs(comparison.state, ComparisonState.VOID)
        self.assertIsNone(comparison.point_difference)
        self.assertEqual(comparison.differing_fields, ("object_of",))
        self.assertIs(comparison.record.determination, Status.FAILED)
        self.assertIs(comparison.record.instrument, Status.OK)
        self.assertIs(comparison.record.physical, Status.UNTESTED)
        self.assertIs(a.record.physical, Status.UNTESTED)
        self.assertIs(b.record.physical, Status.UNTESTED)

    def test_each_identity_coordinate_independently_prevents_comparison(self):
        for field in IDENTITY_FIELDS:
            with self.subTest(field=field):
                a, b, c = self.pair(replace(self.identity, **{field: "different declared value"}))
                self.assertEqual(a.outputs[0].value, b.outputs[0].value)
                self.assertEqual(c.differing_fields, (field,))
                self.assertIs(c.state, ComparisonState.VOID)
                self.assertIsNone(c.point_difference)

    def test_each_missing_coordinate_is_unknown_not_equal(self):
        for field in IDENTITY_FIELDS:
            with self.subTest(field=field):
                _, _, c = self.pair(replace(self.identity, **{field: None}))
                self.assertIs(c.identity, IdentityState.UNKNOWN)
                self.assertIs(c.state, ComparisonState.WITHHELD)
                self.assertIn(f"replacement.{field}", c.unresolved)
                self.assertIsNone(c.point_difference)
                self.assertIs(c.record.physical, Status.UNTESTED)
                self.assertIs(c.record.instrument, Status.OK)

    def test_both_missing_fields_are_not_an_identity_match(self):
        unknown = replace(self.identity, normalizer=None)
        _, _, c = run_pair(unknown, unknown)
        self.assertIs(c.identity, IdentityState.UNKNOWN)
        self.assertIn("previous.normalizer", c.unresolved)
        self.assertIn("replacement.normalizer", c.unresolved)
        self.assertIsNone(c.point_difference)

    def test_legacy_missing_declarations_do_not_get_default_identity(self):
        a, b, c = run_pair(None, None)
        self.assertIs(a.state, RunState.COMPUTED)
        self.assertIs(b.state, RunState.COMPUTED)
        self.assertIs(c.identity, IdentityState.UNKNOWN)
        self.assertIs(c.route, RouteState.UNKNOWN)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)

    def test_unknown_coordinate_does_not_hide_known_mismatch(self):
        _, _, c = self.pair(replace(self.identity, normalizer=None, object_of="different"))
        self.assertIs(c.identity, IdentityState.MISMATCH)
        self.assertIs(c.state, ComparisonState.VOID)
        self.assertEqual(c.differing_fields, ("object_of",))
        self.assertIn("replacement.normalizer", c.unresolved)
        self.assertTrue(any(f.code == "MEASURAND_IDENTITY_UNKNOWN" for f in c.record.findings))

    def test_same_identity_different_declared_route_is_not_automatically_void(self):
        a, b, c = self.pair(replace(self.identity, protocol="constructed second route"))
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.route, RouteState.DIFFERENT)
        self.assertIs(c.state, ComparisonState.ELIGIBLE)
        self.assertEqual(c.point_difference, 0.0)
        for run in (a, b):
            self.assertIs(run.applicability.state, ApplicabilityState.UNKNOWN)
            self.assertIs(run.record.physical, Status.UNTESTED)
            self.assertIsNone(run.outputs[0].uncertainty)

    def test_missing_route_preserves_identity_match_but_withholds_comparison(self):
        _, _, c = self.pair(replace(self.identity, protocol=None))
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.route, RouteState.UNKNOWN)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)

    def test_output_rename_is_not_a_measurand_change(self):
        _, _, c = self.pair(output="another_symbol")
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.state, ComparisonState.ELIGIBLE)
        self.assertEqual(c.replacement_output, "another_symbol")
        self.assertEqual(c.point_difference, 0.0)

    def test_numeric_disagreement_is_not_an_identity_failure_or_physical_verdict(self):
        _, _, c = self.pair(expression="2*x", expected=(2.0, 4.0))
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.state, ComparisonState.ELIGIBLE)
        self.assertEqual(c.point_difference, 2.0)
        self.assertIs(c.record.physical, Status.UNTESTED)
        self.assertIs(c.record.instrument, Status.OK)

    def test_same_route_different_identity_still_void(self):
        _, _, c = self.pair(replace(self.identity, population="different cohort"))
        self.assertIs(c.route, RouteState.SAME)
        self.assertIs(c.state, ComparisonState.VOID)

    def test_substitution_runs_complete_harnesses_despite_identity_mismatch(self):
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calc:
            a, b, c = self.pair(replace(self.identity, normalizer="per selected member"))
        self.assertEqual(calc.call_count, 8)  # two known, one null, one nominal, per run
        self.assertEqual(a.stages, b.stages)
        self.assertEqual(b.parent_run_digest, a.digest())
        self.assertIs(c.state, ComparisonState.VOID)
        self.assertNotEqual(a.known_answer.instrument_id, b.known_answer.instrument_id)

    def test_identity_changes_content_and_description_binding_without_revision_change(self):
        original = model(self.identity)
        for field in IDENTITY_FIELDS + ("protocol",):
            changed = model(replace(self.identity, **{field: "changed declaration"}))
            with self.subTest(field=field):
                self.assertEqual(original.revision, changed.revision)
                self.assertNotEqual(original.digest(), changed.digest())
                self.assertNotEqual(original.description().digest(), changed.description().digest())

    def test_identity_decision_and_evidence_are_content_bound(self):
        changed = replace(self.identity, decision=replace(DECISION, rationale="new selection"))
        changed_ref = replace(self.identity, evidence=(
            EvidenceRef("constructed-identity", "new retained source"),))
        for identity in (changed, changed_ref):
            self.assertNotEqual(model(identity).digest(), model(self.identity).digest())

    def test_relabeling_identity_cannot_reuse_old_validation_plan(self):
        eq = model(self.identity)
        changed = model(replace(self.identity, object_of="different"))
        registry = EquationRegistry()
        registry.register(eq)
        replacement_registry = EquationRegistry()
        replacement_registry.register(changed)
        a = execute(registry, eq.equation_id, eq.revision, self.experiment,
                    plan(eq, self.experiment), DECISION)
        with patch("playground.equations.substitution._calculate") as calculate:
            b = substitute(a, replacement_registry, changed.equation_id, changed.revision,
                           plan(eq, self.experiment), DECISION)
        calculate.assert_not_called()
        self.assertIs(b.state, RunState.BLOCKED)

    def test_relabeling_identity_cannot_inherit_old_physical_assessment(self):
        eq = model(self.identity)
        changed = model(replace(self.identity, object_of="different"))
        registry = EquationRegistry()
        registry.register(eq)
        replacement_registry = EquationRegistry()
        replacement_registry.register(changed)
        assessment = support(eq.description(), self.experiment.context)
        a = execute(registry, eq.equation_id, eq.revision, self.experiment,
                    plan(eq, self.experiment), DECISION, (assessment,))
        b = substitute(a, replacement_registry, changed.equation_id, changed.revision,
                       plan(changed, self.experiment), DECISION, (assessment,))
        self.assertIs(a.applicability.state, ApplicabilityState.SUPPORTED)
        self.assertIs(b.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertIn(assessment.assessment_id, b.applicability.excluded_assessment_ids)
        self.assertIs(b.record.physical, Status.UNTESTED)

    def test_failed_known_answer_withholds_comparison_not_identity_match(self):
        _, b, c = self.pair(expression="2*x")
        self.assertIs(b.state, RunState.BLOCKED)
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIs(c.record.instrument, Status.FAILED)
        self.assertIs(c.record.physical, Status.UNTESTED)
        self.assertIsNone(c.point_difference)

    def test_context_instrument_failure_survives_identity_and_equation_change(self):
        record = FailureRecord((Finding(
            Axis.INSTRUMENT, Status.FAILED, "CONSTRUCTED_OBSERVER_FAILURE",
            "constructed failed calibration", "validation.test_measurand"),))
        snapshot = ExperimentalDiagnostics(
            self.experiment.context.digest(), record, DECISION,
            (EvidenceRef("constructed-calibration", "failed-observer-fixture"),))
        experiment = replace(self.experiment, diagnostics=(snapshot,))
        with patch("playground.equations.substitution._calculate") as calculate:
            a, b, c = self.pair(replace(self.identity, object_of="another object"),
                                experiment=experiment)
        calculate.assert_not_called()
        self.assertIs(a.state, RunState.BLOCKED)
        self.assertIs(b.state, RunState.BLOCKED)
        self.assertIs(c.state, ComparisonState.VOID)
        self.assertIsNone(c.point_difference)
        self.assertIs(c.record.instrument, Status.FAILED)
        self.assertIs(c.record.physical, Status.UNTESTED)
        self.assertEqual(b.experiment.diagnostics, (snapshot,))

    def test_failed_null_cannot_be_repaired_by_identity_declaration(self):
        eq = model(self.identity, expression="x+1")
        registry = EquationRegistry()
        base = model(self.identity)
        registry.register(base)
        registry.register(replace(eq, revision="offset"))
        a = execute(registry, base.equation_id, base.revision, self.experiment,
                    plan(base, self.experiment), DECISION)
        eq = registry.select(eq.equation_id, "offset")
        b = substitute(a, registry, eq.equation_id, eq.revision,
                       plan(eq, self.experiment, (2.0, 3.0)), DECISION)
        c = compare_substitution(a, b, "y", "y", DECISION)
        self.assertTrue(b.known_answer.validated_within_tested_cases)
        self.assertFalse(b.null.clean_within_tested_cases)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIs(c.record.instrument, Status.FAILED)

    def test_wrong_parent_is_not_licensed_by_matching_identity(self):
        a, b, _ = self.pair()
        c = compare_substitution(a, replace(b, parent_run_digest="wrong"), "y", "y", DECISION)
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIs(c.record.determination, Status.FAILED)
        self.assertIsNone(c.point_difference)

    def test_changed_experiment_is_not_licensed_by_matching_identity(self):
        a, b, _ = self.pair()
        foreign = replace(b.experiment, anchor=replace(b.experiment.anchor, label="changed"))
        c = compare_substitution(a, replace(b, experiment=foreign), "y", "y", DECISION)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)
        self.assertTrue(any(f.code == "MEASURAND_RUN_BINDING" for f in c.record.findings))

    def test_missing_or_wrong_output_mapping_is_not_guessed(self):
        a, b, _ = self.pair()
        c = compare_substitution(a, b, "unknown-output", "y", DECISION)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)
        self.assertIs(c.record.determination, Status.FAILED)

    def test_missing_harness_record_is_not_a_completed_calculation(self):
        a, b, _ = self.pair()
        c = compare_substitution(a, replace(b, known_answer=None), "y", "y", DECISION)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)

    def test_output_units_must_be_bound_even_with_matching_identity(self):
        a, b, _ = self.pair()
        b = replace(b, outputs=(replace(b.outputs[0], unit="different"),))
        c = compare_substitution(a, b, "y", "y", DECISION)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)

    def test_different_declared_units_are_not_converted_or_overridden_by_identity(self):
        base = model(self.identity)
        changed = replace(model(self.identity, revision="new-unit"), outputs=(
            OutputPort("y", "x", "another-unit", self.identity),))
        registry = EquationRegistry()
        registry.register(base)
        registry.register(changed)
        a = execute(registry, base.equation_id, base.revision, self.experiment,
                    plan(base, self.experiment), DECISION)
        changed_plan = replace(plan(changed, self.experiment),
                               output_units=(("y", "another-unit"),))
        b = substitute(a, registry, changed.equation_id, changed.revision,
                       changed_plan, DECISION)
        self.assertIs(b.state, RunState.COMPUTED)
        c = compare_substitution(a, b, "y", "y", DECISION)
        self.assertIs(c.identity, IdentityState.MATCH)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)
        self.assertTrue(any(f.code == "MEASURAND_UNIT_BINDING" for f in c.record.findings))

    def test_nonfinite_point_difference_is_instrument_not_physical_failure(self):
        base = model(self.identity, expression="-(x/2)*1e308")
        changed = model(self.identity, expression="(x/2)*1e308", revision="positive")
        registry = EquationRegistry()
        registry.register(base)
        registry.register(changed)
        a = execute(registry, base.equation_id, base.revision, self.experiment,
                    plan(base, self.experiment, (-5e307, -1e308)), DECISION)
        b = substitute(a, registry, changed.equation_id, changed.revision,
                       plan(changed, self.experiment, (5e307, 1e308)), DECISION)
        self.assertIs(a.state, RunState.COMPUTED)
        self.assertIs(b.state, RunState.COMPUTED)
        c = compare_substitution(a, b, "y", "y", DECISION)
        self.assertIs(c.state, ComparisonState.WITHHELD)
        self.assertIsNone(c.point_difference)
        self.assertIs(c.record.instrument, Status.FAILED)
        self.assertIs(c.record.physical, Status.UNTESTED)

    def test_comparison_does_not_call_numerical_engine_or_mutate_runs(self):
        a, b, _ = self.pair()
        before = (a.to_json(), b.to_json())
        with patch("playground.equations.substitution._calculate") as calculate:
            c = compare_substitution(a, b, "y", "y", DECISION)
        calculate.assert_not_called()
        self.assertEqual(before, (a.to_json(), b.to_json()))
        self.assertEqual(c.previous.digest(), a.digest())

    def test_json_retains_identity_protocol_provenance_unknowns_and_full_runs(self):
        a, b, c = self.pair(replace(self.identity, normalizer=None))
        report = c.to_dict()
        self.assertEqual(report["previous_run_digest"], a.digest())
        self.assertEqual(report["replacement_run_digest"], b.digest())
        identity = report["replacement"]["equation"]["outputs"][0]["measurand"]
        self.assertIsNone(identity["normalizer"])
        self.assertTrue(identity["decision"]["rationale"])
        self.assertTrue(identity["evidence"])
        self.assertIsNone(report["point_difference"])
        self.assertIsNone(report["replacement"]["outputs"][0]["uncertainty"])
        self.assertEqual(json.loads(json.dumps(report)), report)

    def test_declarations_and_comparison_selection_are_typed_and_immutable(self):
        for changes in ({"quantity": ""}, {"normalizer": "UNKNOWN"},
                        {"normalizer": "none"}, {"object_of": []},
                        {"decision": None}, {"evidence": []}, {"evidence": ()},
                        {"evidence": (EvidenceRef("constructed", "source", []),)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(self.identity, **changes)
        with self.assertRaises(FrozenInstanceError):
            self.identity.normalizer = "changed"
        with self.assertRaises(ValueError):
            OutputPort("y", "x", "toy-energy-unit", {"quantity": "not typed"})
        a, b, _ = self.pair()
        with self.assertRaises(ValueError):
            compare_substitution(a, b, "y", "y", None)

    def test_complete_example_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fresh"
            report = run_probe(output)
            self.assertEqual(len(report["cases"]), 15)
            saved = json.loads((output / "measurand-substitution-report.json").read_text())
            self.assertEqual(saved, report)
            self.assertIn("This does not establish",
                          (output / "measurand-substitution-report.md").read_text())
            before = (output / "measurand-substitution-report.json").read_bytes()
            with self.assertRaises(FileExistsError):
                run_probe(output)
            self.assertEqual(before, (output / "measurand-substitution-report.json").read_bytes())


class IdentityBypassDetectionTests(unittest.TestCase):
    def require_detected(self, test_name, changes):
        original = compare_substitution

        def erase_identity(previous, replacement, a, b, selection):
            result = original(previous, replacement, a, b, selection)
            return changes(result)

        result = unittest.TestResult()
        with patch(__name__ + ".compare_substitution", side_effect=erase_identity), patch(
            "playground.equations.measurand_example.compare_substitution",
            side_effect=erase_identity,
        ):
            MeasurandTests(test_name).run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertTrue(result.failures, "identity bypass was not detected")
        self.assertFalse(result.errors, "a crashed test is not successful detection")

    def test_units_and_numbers_only_mutant_is_detected_without_test_crash(self):
        self.require_detected(
            "test_equal_names_units_values_do_not_establish_same_object",
            lambda r: replace(r, identity=IdentityState.MATCH,
                              state=ComparisonState.ELIGIBLE, point_difference=0.0))

    def test_missing_identity_as_match_mutant_is_detected(self):
        self.require_detected(
            "test_both_missing_fields_are_not_an_identity_match",
            lambda r: replace(r, identity=IdentityState.MATCH,
                              state=ComparisonState.ELIGIBLE, point_difference=0.0))

    def test_protocol_change_as_quantity_change_mutant_is_detected(self):
        self.require_detected(
            "test_same_identity_different_declared_route_is_not_automatically_void",
            lambda r: replace(r, identity=IdentityState.MISMATCH,
                              state=ComparisonState.VOID, point_difference=None))

    def test_determination_mismatch_as_physical_failure_mutant_is_detected(self):
        self.require_detected(
            "test_equal_names_units_values_do_not_establish_same_object",
            lambda r: replace(r, record=r.record.with_finding(Finding(
                Axis.PHYSICAL, Status.FAILED, "PLANTED_AXIS_COLLAPSE",
                "wrongly condemn the model for unlike measurands",
                "validation.test_measurand"))))


if __name__ == "__main__":
    unittest.main()
