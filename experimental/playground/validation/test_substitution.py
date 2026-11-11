"""Planted bypass attempts and controls for gated equation substitution."""

import json
import unittest
from dataclasses import replace
from unittest.mock import patch

from ..applicability.example import DECISION, support
from ..applicability.mapping import (
    ApplicabilityState, ConditionBasis, Domain, EvidenceKind, Judgment,
)
from ..equations.adapter import EquationRegistry, InputPort, OutputPort, _calculate
from ..equations.example import (
    example_runs, fixture_equation, fixture_experiment, fixture_plan,
)
from ..equations.substitution import (
    BoundaryProtocol, ExperimentalDiagnostics, RunState, ScopedDiagnostics, execute, substitute,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.l0_closure import ValueProvenance
from ..gates.gate_results import GateOutcome, GateResult
from ..lifecycle.unknown_expiry import UnknownState
from .known_answer import InstrumentValidation, KnownAnswerCase, validate_known_answers
from .null_harness import NullCase, NullValidation, validate_nulls


def diagnostic(axis, severity=Status.FAILED):
    return FailureRecord((Finding(axis, severity, "PLANTED", "planted failure",
                                  "validation.test_substitution"),))


class SubstitutionTests(unittest.TestCase):
    def setUp(self):
        self.eq = fixture_equation()
        self.experiment = fixture_experiment()
        self.plan = fixture_plan(self.eq, self.experiment)
        self.registry = EquationRegistry()
        self.registry.register(self.eq)

    def run_equation(self, equation=None, experiment=None, plan=None, **kwargs):
        eq = equation or self.eq
        exp = experiment or self.experiment
        return execute(
            self.registry, eq.equation_id, eq.revision, exp,
            plan or fixture_plan(eq, exp), DECISION, **kwargs,
        )

    def rebind_context(self, context):
        return replace(
            self.experiment, context=context,
            boundary=replace(self.experiment.boundary, context_digest=context.digest()),
        )

    def change_energy(self, **changes):
        context = replace(self.experiment.context, conditions=tuple(
            replace(c, **changes) if c.key == "energy" else c
            for c in self.experiment.context.conditions
        ))
        return self.rebind_context(context)

    def no_evaluation(self, **kwargs):
        with patch("playground.equations.substitution._calculate") as calculate:
            result = self.run_equation(**kwargs)
            calculate.assert_not_called()
        self.assertIs(result.state, RunState.BLOCKED)
        self.assertEqual(result.outputs, ())
        return result

    def test_clean_calculation_remains_physically_unknown(self):
        r = self.run_equation()
        self.assertIs(r.state, RunState.COMPUTED)
        self.assertEqual(r.outputs[0].value, 2.0)
        self.assertIs(r.record.instrument, Status.OK)
        self.assertIs(r.record.physical, Status.UNTESTED)
        self.assertIs(r.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertIsNone(r.outputs[0].uncertainty)
        self.assertEqual(r.stages[-1], "calculation:computed")

    def test_full_stage_order(self):
        r = self.run_equation()
        self.assertEqual(r.stages, (
            "protocol-binding:pass", "l0:pass", "applicability:candidate-domain",
            "validation-plan:pass", "known-answer:pass", "null:pass",
            "calculation:computed",
        ))

    def test_l0_recomputed_not_accepted_from_caller(self):
        with patch("playground.equations.substitution.l0_closure_gate", wraps=__import__(
            "playground.gates.l0_closure", fromlist=["l0_closure_gate"]
        ).l0_closure_gate) as gate:
            self.run_equation()
            self.assertEqual(gate.call_count, 1)

    def test_incomplete_balanced_ledger_cannot_pass_vacuously(self):
        b = self.experiment.boundary
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, declared_complete=False)))
        r = self.no_evaluation(experiment=exp)
        self.assertIs(r.record.determination, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_unbalanced_model_ledger_stops_before_equation(self):
        b = self.experiment.boundary
        account = replace(b.accounting.accounts[0], final=3.0)
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, accounts=(account,))))
        r = self.no_evaluation(experiment=exp)
        self.assertIs(r.record.physical, Status.FAILED)
        self.assertIsNone(r.known_answer)

    def test_unresolved_measured_misclosure_not_resolved_by_equation(self):
        b = self.experiment.boundary
        account = replace(b.accounting.accounts[0], final=3.0,
                          final_provenance=ValueProvenance.MEASURED)
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, accounts=(account,))))
        r = self.no_evaluation(experiment=exp)
        self.assertIs(r.record.physical, Status.INDETERMINATE)
        self.assertIs(r.record.instrument, Status.INDETERMINATE)

    def test_missing_intervention_ledger_entry_is_determination_failure(self):
        b = self.experiment.boundary
        a = replace(b.accounting.accounts[0], exchanges=b.accounting.accounts[0].exchanges[:1])
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, accounts=(a,))))
        r = self.no_evaluation(experiment=exp)
        self.assertIs(r.record.determination, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_ledger_bound_to_different_context_refused(self):
        exp = replace(self.experiment, boundary=replace(
            self.experiment.boundary, context_digest="old-context"))
        self.no_evaluation(experiment=exp)

    def test_anchor_digest_change_refused(self):
        exp = self.rebind_context(replace(self.experiment.context, anchor_digest="stale"))
        self.no_evaluation(experiment=exp)

    def test_anchor_actual_content_change_refused(self):
        exp = replace(self.experiment, anchor=replace(
            self.experiment.anchor, quantities=(("energy", 3.0),)))
        self.no_evaluation(experiment=exp)

    def test_boundary_label_mismatch_refused(self):
        b = self.experiment.boundary
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, boundary_label="different-boundary")))
        self.no_evaluation(experiment=exp)

    def test_ledger_initial_must_equal_anchor_value(self):
        b = self.experiment.boundary
        a = replace(b.accounting.accounts[0], initial=3.0, final=3.0)
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, accounts=(a,))))
        self.no_evaluation(experiment=exp)

    def test_unknown_exchange_source_refused(self):
        b = self.experiment.boundary
        a = b.accounting.accounts[0]
        a = replace(a, exchanges=(
            replace(a.exchanges[0], registered_by="unregistered"), a.exchanges[1]))
        exp = replace(self.experiment, boundary=replace(
            b, accounting=replace(b.accounting, accounts=(a,))))
        self.no_evaluation(experiment=exp)

    def test_intervention_must_link_to_control_or_observer(self):
        b = replace(self.experiment.boundary, intervention_conditions=(
            ("control:drive", "energy"), ("observer:sensor", "observer")))
        self.no_evaluation(experiment=replace(self.experiment, boundary=b))

    def test_outside_applicability_stops_harness_and_nominal(self):
        r = self.no_evaluation(experiment=self.change_energy(value=5.0))
        self.assertIs(r.applicability.state, ApplicabilityState.OUTSIDE)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_uncertainty_edge_stops_harness_and_nominal(self):
        self.no_evaluation(experiment=self.change_energy(value=3.0, uncertainty=.1))

    def test_unknown_uncertainty_stops_harness_and_nominal(self):
        self.no_evaluation(experiment=self.change_energy(uncertainty=None))

    def test_assumed_input_cannot_be_laundered_by_formula(self):
        self.no_evaluation(experiment=self.change_energy(basis=ConditionBasis.ASSUMED))

    def test_unresolved_model_assumption_stops_execution(self):
        eq = replace(self.eq, revision="assumed", assumptions=("coupling not established",))
        self.registry.register(eq)
        self.no_evaluation(equation=eq)

    def test_open_missing_or_stale_dependencies_stop_execution(self):
        eq = replace(self.eq, revision="dependent", unknown_dependencies=("u",))
        self.registry.register(eq)
        for states in ({}, {"u": UnknownState.UNKNOWN}, {"u": UnknownState.EXPIRED},
                       {"u": UnknownState.REEVALUATED}):
            with self.subTest(states=states):
                r = self.no_evaluation(equation=eq, dependency_states=states)
                self.assertIs(r.record.physical, Status.UNTESTED)

    def test_unbound_diagnostic_record_refused(self):
        with self.assertRaises(ValueError):
            self.run_equation(diagnostics=FailureRecord())

    def test_wrong_equation_diagnostic_binding_stops_execution(self):
        scoped = ScopedDiagnostics("different-equation", self.experiment.context.digest(),
                                   diagnostic(Axis.INSTRUMENT))
        self.no_evaluation(diagnostics=scoped)

    def test_bound_diagnostic_failure_stops_execution_without_model_failure(self):
        scoped = ScopedDiagnostics(self.eq.description().digest(), self.experiment.context.digest(),
                                   diagnostic(Axis.INSTRUMENT))
        r = self.no_evaluation(diagnostics=scoped)
        self.assertIs(r.record.instrument, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_plan_from_other_equation_does_not_certify_new_adapter(self):
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        self.no_evaluation(equation=eq, plan=self.plan)

    def test_plan_from_other_context_refused(self):
        self.no_evaluation(plan=replace(self.plan, context_digest="previous-context"))

    def test_missing_port_in_any_diagnostic_case_stops_before_all_harnesses(self):
        bad = KnownAnswerCase.from_maps("missing", {}, {"y": 1.0}, {"y": 0.0})
        self.no_evaluation(plan=replace(self.plan, known_answers=self.plan.known_answers + (bad,)))

    def test_validation_units_must_match(self):
        self.no_evaluation(plan=replace(self.plan, input_units=(("x", "different-unit"),)))

    def test_input_unit_mismatch_stops_execution(self):
        eq = replace(self.eq, revision="bad-unit", inputs=(InputPort("x", "energy", "other-unit"),))
        self.registry.register(eq)
        self.no_evaluation(equation=eq)

    def test_input_requires_own_numeric_scope_criterion(self):
        context = replace(self.experiment.context, conditions=self.experiment.context.conditions + (
            replace(next(c for c in self.experiment.context.conditions if c.key == "energy"),
                    key="unscoped-extra-input"),
        ))
        exp = self.rebind_context(context)
        eq = replace(self.eq, revision="unscoped-input",
                     inputs=(InputPort("x", "unscoped-extra-input", "toy-energy-unit"),))
        self.registry.register(eq)
        self.no_evaluation(equation=eq, experiment=exp)

    def test_empty_known_answer_set_cannot_certify(self):
        r = self.no_evaluation(plan=replace(self.plan, known_answers=()))
        self.assertIs(r.record.instrument, Status.INDETERMINATE)

    def test_empty_null_set_never_runs_nominal(self):
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calc:
            r = self.run_equation(plan=replace(self.plan, nulls=()))
        self.assertIs(r.state, RunState.BLOCKED)
        self.assertEqual(calc.call_count, len(self.plan.known_answers))
        self.assertEqual(r.outputs, ())

    def test_failed_known_answer_prevents_nominal_calculation(self):
        eq = fixture_equation("2*x", "wrong-expectation")
        self.registry.register(eq)
        r = self.run_equation(equation=eq)
        self.assertIs(r.state, RunState.BLOCKED)
        self.assertIs(r.record.instrument, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)
        self.assertIsNone(r.null)
        self.assertEqual(r.outputs, ())

    def test_false_positive_null_prevents_nominal_calculation(self):
        eq = fixture_equation("x+1", "offset")
        self.registry.register(eq)
        plan = fixture_plan(eq, self.experiment)
        plan = replace(plan, known_answers=(
            KnownAnswerCase.from_maps("offset-known", {"x": 1.0}, {"y": 2.0}, {"y": 0.0}),
        ))
        r = self.run_equation(equation=eq, plan=plan)
        self.assertIs(r.state, RunState.BLOCKED)
        self.assertTrue(r.null.cases_flagged)
        self.assertEqual(r.outputs, ())

    def test_runtime_domain_failure_is_instrument_not_physical(self):
        # Well-defined at test inputs 1 and 0, but singular at the actual x=2.
        eq = fixture_equation("x/(x-2)", "singularity")
        self.registry.register(eq)
        plan = replace(fixture_plan(eq, self.experiment), known_answers=(
            KnownAnswerCase.from_maps("one", {"x": 1.0}, {"y": -1.0}, {"y": 0.0}),
        ))
        r = self.run_equation(equation=eq, plan=plan)
        self.assertIs(r.state, RunState.ERROR)
        self.assertIs(r.record.instrument, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)
        self.assertIs(r.applicability.state, ApplicabilityState.BLOCKED)
        self.assertEqual(r.outputs, ())

    def test_supported_assessment_preserved_not_generated(self):
        a = support(self.eq.description(), self.experiment.context)
        r = self.run_equation(assessments=(a,))
        self.assertIs(r.state, RunState.COMPUTED)
        self.assertIs(r.applicability.state, ApplicabilityState.SUPPORTED)
        self.assertEqual(r.applicability.assessments, (a,))
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_mathematical_and_diagnostic_pass_not_empirical_support(self):
        for kind in (EvidenceKind.MATHEMATICAL, EvidenceKind.DIAGNOSTIC):
            a = replace(support(self.eq.description(), self.experiment.context), kind=kind)
            r = self.run_equation(assessments=(a,))
            self.assertIs(r.state, RunState.COMPUTED)
            self.assertIs(r.applicability.state, ApplicabilityState.UNKNOWN)

    def test_conflicting_or_opposing_adequacy_cannot_be_overridden(self):
        a = support(self.eq.description(), self.experiment.context, "yes")
        b = replace(a, assessment_id="no", judgment=Judgment.OPPOSES)
        for assessments in ((b,), (a, b)):
            self.no_evaluation(assessments=assessments)

    def test_new_formula_cannot_reuse_old_adequacy_even_same_declared_revision(self):
        a = support(self.eq.description(), self.experiment.context)
        changed = replace(self.eq, outputs=(OutputPort("y", "2*x", "toy-energy-unit"),))
        self.assertNotEqual(changed.description().digest(), self.eq.description().digest())
        other_registry = EquationRegistry()
        other_registry.register(changed)
        r = execute(other_registry, changed.equation_id, changed.revision,
                    self.experiment, fixture_plan(changed, self.experiment, doubled=True),
                    DECISION, (a,))
        self.assertIs(r.state, RunState.COMPUTED)
        self.assertIs(r.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertEqual(r.applicability.excluded_assessment_ids, (a.assessment_id,))

    def test_substitution_preserves_context_not_certificates(self):
        a, b = example_runs()
        self.assertIs(b.state, RunState.COMPUTED)
        self.assertEqual(a.outputs[0].value, 2.0)
        self.assertEqual(b.outputs[0].value, 4.0)
        self.assertEqual(a.experiment, b.experiment)
        self.assertEqual(b.parent_run_digest, a.digest())
        self.assertEqual(b.known_answer.instrument_id.split("@")[0], "toy-equation")
        self.assertNotEqual(a.known_answer.instrument_id, b.known_answer.instrument_id)

    def test_substitution_reruns_both_harnesses(self):
        first = self.run_equation()
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calc:
            r = substitute(first, self.registry, eq.equation_id, eq.revision,
                           fixture_plan(eq, self.experiment, doubled=True), DECISION)
        self.assertEqual(calc.call_count, 4)  # 2 known, 1 null, 1 nominal
        self.assertIs(r.state, RunState.COMPUTED)

    def test_substitution_does_not_inherit_old_adequacy(self):
        first = self.run_equation(assessments=(
            support(self.eq.description(), self.experiment.context),))
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        r = substitute(first, self.registry, eq.equation_id, eq.revision,
                       fixture_plan(eq, self.experiment, doubled=True), DECISION)
        self.assertIs(first.applicability.state, ApplicabilityState.SUPPORTED)
        self.assertIs(r.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertEqual(r.supplied_assessments, ())

    def test_substitution_cannot_reuse_previous_plan(self):
        first = self.run_equation()
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        with patch("playground.equations.substitution._calculate") as calc:
            r = substitute(first, self.registry, eq.equation_id, eq.revision, self.plan, DECISION)
            calc.assert_not_called()
        self.assertIs(r.state, RunState.BLOCKED)

    def test_context_bound_observer_failure_survives_substitution(self):
        snapshot = ExperimentalDiagnostics(
            self.experiment.context.digest(), diagnostic(Axis.INSTRUMENT), DECISION,
            (EvidenceRef("observer-test", "constructed-calibration-failure"),),
        )
        exp = replace(self.experiment, diagnostics=(snapshot,))
        first = self.no_evaluation(experiment=exp)
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        with patch("playground.equations.substitution._calculate") as calc:
            second = substitute(
                first, self.registry, eq.equation_id, eq.revision,
                fixture_plan(eq, exp, doubled=True), DECISION,
            )
            calc.assert_not_called()
        self.assertIs(second.state, RunState.BLOCKED)
        self.assertIs(second.record.instrument, Status.FAILED)
        self.assertIs(second.record.physical, Status.UNTESTED)
        self.assertEqual(second.experiment.diagnostics, (snapshot,))

    def test_context_bound_determination_failure_survives_substitution(self):
        snapshot = ExperimentalDiagnostics(
            self.experiment.context.digest(), diagnostic(Axis.DETERMINATION), DECISION,
            (EvidenceRef("control-audit", "constructed-missing-control"),),
        )
        exp = replace(self.experiment, diagnostics=(snapshot,))
        first = self.no_evaluation(experiment=exp)
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        with patch("playground.equations.substitution._calculate") as calc:
            second = substitute(first, self.registry, eq.equation_id, eq.revision,
                                fixture_plan(eq, exp, doubled=True), DECISION)
            calc.assert_not_called()
        self.assertIs(second.record.determination, Status.FAILED)
        self.assertIs(second.record.physical, Status.UNTESTED)

    def test_new_adapter_can_replace_equation_specific_failure_after_fresh_validation(self):
        first = self.run_equation(plan=replace(self.plan, nulls=()))
        self.assertIs(first.state, RunState.BLOCKED)
        eq = fixture_equation("2*x", "2")
        self.registry.register(eq)
        second = substitute(first, self.registry, eq.equation_id, eq.revision,
                            fixture_plan(eq, self.experiment, doubled=True), DECISION)
        self.assertIs(second.state, RunState.COMPUTED)
        self.assertIs(second.record.physical, Status.UNTESTED)

    def test_foreign_experimental_diagnostic_snapshot_stops_evaluation(self):
        snapshot = ExperimentalDiagnostics(
            "wrong-context", diagnostic(Axis.INSTRUMENT), DECISION,
            (EvidenceRef("observer-test", "other-context"),),
        )
        r = self.no_evaluation(experiment=replace(self.experiment, diagnostics=(snapshot,)))
        self.assertIs(r.record.determination, Status.FAILED)

    def test_full_report_json_preserves_bindings_criteria_and_unknowns(self):
        a, b = example_runs()
        report = json.loads(b.to_json())
        self.assertEqual(report["parent_run_digest"], a.digest())
        self.assertEqual(report["context_digest"], b.experiment.context.digest())
        self.assertEqual(report["equation_digest"], b.equation.digest())
        self.assertEqual(report["plan_digest"], b.plan.digest())
        self.assertTrue(report["selection"]["rationale"])
        self.assertTrue(report["plan"]["evidence"])
        self.assertTrue(report["experiment"]["boundary"]["decision"]["criteria"])
        self.assertTrue(report["applicability"]["ceases_to_hold"])
        self.assertIsNone(report["outputs"][0]["uncertainty"])

    def test_no_gate_override_or_free_input_arguments(self):
        for kwargs in ({"inputs": {"x": 999.0}}, {"skip_validation": True},
                       {"validated": True}, {"l0_result": object()}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                self.run_equation(**kwargs)

    def test_selection_provenance_required(self):
        with self.assertRaises(ValueError):
            execute(self.registry, self.eq.equation_id, self.eq.revision, self.experiment,
                    self.plan, None)


class AdapterAndProtocolTests(unittest.TestCase):
    def test_unsafe_or_unbounded_expression_rejected(self):
        for expression in ("__import__('os')", "x.__class__", "x[0]", "[x for x in (1,)]",
                           "abs(x)", "lambda: x", "True", "float('nan')", "y+1",
                           "'hello'", "1e999", "x//2", "x%2", "x" * 5000):
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                fixture_equation(expression)

    def test_allowed_arithmetic(self):
        for expression, expected in (("x", 2.), ("+x", 2.), ("-x", -2.),
                                     ("x+1", 3.), ("x-1", 1.), ("2*x", 4.),
                                     ("x/2", 1.), ("x**2", 4.)):
            with self.subTest(expression=expression):
                self.assertEqual(_calculate(fixture_equation(expression), {"x": 2.})["y"], expected)

    def test_nonreal_or_nonfinite_arithmetic_rejected(self):
        for expression in ("1/0", "(-1)**0.5", "x**101", "1e308*1e308"):
            with self.subTest(expression=expression), self.assertRaises(
                (ValueError, ZeroDivisionError, OverflowError)
            ):
                _calculate(fixture_equation(expression), {"x": 2.})

    def test_registry_refuses_arbitrary_callables_and_in_place_replacement(self):
        r = EquationRegistry()
        with self.assertRaises(ValueError):
            r.register(lambda x: x)
        r.register(fixture_equation())
        with self.assertRaises(ValueError):
            r.register(fixture_equation("2*x"))

    def test_explicit_revision_required(self):
        r = EquationRegistry()
        r.register(fixture_equation())
        with self.assertRaises(KeyError):
            r.select("toy-equation", "latest")

    def test_engine_version_bound(self):
        with self.assertRaises(ValueError):
            replace(fixture_equation(), engine="unverified-engine")

    def test_port_schema_rejects_missing_units_and_duplicate_outputs(self):
        with self.assertRaises(ValueError):
            InputPort("x", "energy", "")
        with self.assertRaises(ValueError):
            replace(fixture_equation(), outputs=fixture_equation().outputs * 2)

    def test_empty_or_nonfinite_ledger_rejected_at_protocol_construction(self):
        b = fixture_experiment().boundary
        with self.assertRaises(ValueError):
            replace(b, accounting=replace(b.accounting, accounts=()), quantity_units=())
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(b, accounting=replace(b.accounting, accounts=(
                    replace(b.accounting.accounts[0], initial=value),)))

    def test_negative_or_nonfinite_exchange_rejected(self):
        b = fixture_experiment().boundary
        a = b.accounting.accounts[0]
        for value in (-1., float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(b, accounting=replace(b.accounting, accounts=(
                    replace(a, exchanges=(
                        replace(a.exchanges[0], magnitude=value), a.exchanges[1])),)))

    def test_empty_or_mutable_adapter_provenance_rejected(self):
        eq = fixture_equation()
        for changes in ({"evidence": ()}, {"inputs": list(eq.inputs)},
                        {"constraints": ()}, {"decision": None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(eq, **changes)

    def test_mutable_anchor_and_diagnostics_cannot_enter_run_snapshot(self):
        exp = fixture_experiment()
        with self.assertRaises(ValueError):
            replace(exp, anchor=replace(exp.anchor, quantities=list(exp.anchor.quantities)))
        with self.assertRaises(ValueError):
            replace(exp, anchor=replace(exp.anchor, conditions=list(exp.anchor.conditions)))
        with self.assertRaises(ValueError):
            ScopedDiagnostics("equation", "context", FailureRecord([]))


class HarnessHardeningTests(unittest.TestCase):
    class Instrument:
        instrument_id = "test-instrument"

        def __init__(self, output):
            self.output = output
            self.calls = 0

        def run(self, inputs):
            self.calls += 1
            return self.output

    def test_nonfinite_outputs_fail_both_harnesses(self):
        case = KnownAnswerCase.from_maps("ka", {"x": 0.}, {"y": 0.}, {"y": 0.})
        null = NullCase.from_maps("null", {"x": 0.}, {"y": 0.}, {"y": 0.})
        for value in (float("nan"), float("inf"), float("-inf"), True, "0", 1j):
            with self.subTest(value=value):
                ka = validate_known_answers(self.Instrument({"y": value}), (case,))
                nu = validate_nulls(self.Instrument({"y": value}), (null,))
                self.assertIs(ka.record.instrument, Status.FAILED)
                self.assertIs(nu.record.instrument, Status.FAILED)
                self.assertFalse(ka.validated_within_tested_cases)
                self.assertFalse(nu.clean_within_tested_cases)
                self.assertIs(ka.record.physical, Status.UNTESTED)

    def test_empty_expectations_are_not_a_vacuous_pass(self):
        for validator, case in (
            (validate_known_answers, KnownAnswerCase.from_maps("ka", {}, {}, {})),
            (validate_nulls, NullCase.from_maps("null", {}, {}, {})),
        ):
            instrument = self.Instrument({"y": 0.})
            result = validator(instrument, (case,))
            self.assertIs(result.record.determination, Status.FAILED)
            self.assertIs(result.record.instrument, Status.UNTESTED)
            self.assertEqual(instrument.calls, 0)

    def test_bad_tolerances_stop_before_instrument_execution(self):
        for tol in (-1., float("nan"), float("inf"), True):
            for validator, case in (
                (validate_known_answers, KnownAnswerCase.from_maps(
                    "ka", {"x": 0.}, {"y": 0.}, {"y": tol})),
                (validate_nulls, NullCase.from_maps(
                    "null", {"x": 0.}, {"y": 0.}, {"y": tol})),
            ):
                instrument = self.Instrument({"y": 0.})
                result = validator(instrument, (case,))
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertEqual(instrument.calls, 0)

    def test_entire_protocol_preflight_before_any_instrument_execution(self):
        good = KnownAnswerCase.from_maps("good", {"x": 0.}, {"y": 0.}, {"y": 0.})
        bad = KnownAnswerCase.from_maps("bad", {"x": 0.}, {"y": float("nan")}, {"y": 0.})
        instrument = self.Instrument({"y": 0.})
        result = validate_known_answers(instrument, (good, bad))
        self.assertEqual(instrument.calls, 0)
        self.assertIs(result.record.determination, Status.FAILED)

    def test_missing_or_extra_tolerance_keys_are_invalid_criteria(self):
        for tol in ({}, {"y": 0., "z": 1.}):
            case = KnownAnswerCase.from_maps("ka", {}, {"y": 0.}, tol)
            self.assertIs(validate_known_answers(self.Instrument({"y": 0.}), (case,)).
                          record.determination, Status.FAILED)

    def test_duplicate_case_ids_rejected_by_both_harnesses(self):
        ka = KnownAnswerCase.from_maps("same", {}, {"y": 0.}, {"y": 0.})
        nu = NullCase.from_maps("same", {}, {"y": 0.}, {"y": 0.})
        for validator, case in ((validate_known_answers, ka), (validate_nulls, nu)):
            instrument = self.Instrument({"y": 0.})
            result = validator(instrument, (case, case))
            self.assertIs(result.record.determination, Status.FAILED)
            self.assertEqual(instrument.calls, 0)


class BypassDetectionTests(unittest.TestCase):
    """Controlled mutants: the anti-bypass tests must notice forged PASS results."""

    def require_detected(self, target, forged, test_name):
        result = unittest.TestResult()
        with patch(target, return_value=forged):
            SubstitutionTests(test_name).run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertTrue(result.failures, "anti-bypass test failed to detect the forged PASS")
        self.assertFalse(result.errors, "a test crash is not a detected bypass")

    def test_forged_l0_pass_is_detected(self):
        self.require_detected(
            "playground.equations.substitution.l0_closure_gate",
            GateResult("l0_closure", GateOutcome.PASS),
            "test_unbalanced_model_ledger_stops_before_equation",
        )

    def test_forged_known_answer_pass_is_detected(self):
        self.require_detected(
            "playground.equations.substitution.validate_known_answers",
            InstrumentValidation("forged", FailureRecord(), ("forged-case",)),
            "test_failed_known_answer_prevents_nominal_calculation",
        )

    def test_forged_null_pass_is_detected(self):
        self.require_detected(
            "playground.equations.substitution.validate_nulls",
            NullValidation("forged", FailureRecord(), ("forged-case",)),
            "test_false_positive_null_prevents_nominal_calculation",
        )


if __name__ == "__main__":
    unittest.main()
