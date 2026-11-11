"""Cross-class contracts: no diagnostic, physical or evidential promotion.

These are constructed fixtures and planted faults, not experiments on physical
thermal cells, capacitors, springs, porous media or biological populations.
"""

import json
import unittest
from dataclasses import FrozenInstanceError, replace
from itertools import permutations
from unittest.mock import patch

from ..applicability.mapping import (
    ApplicabilityState, Assessment, ConditionBasis, Domain, EvidenceKind,
    Judgment, ScopeState, assess, build_map,
)
from ..detection.non_detection import NonDetectionObservation, record_non_detection
from ..detection.scoped_absence import AbsenceClaim, AbsenceRejection, claim_absence
from ..detection.sensitivity import SensitivityCase, establish_sensitivity
from ..equations.adapter import EquationRegistry
from ..equations.substitution import (
    ExperimentalDiagnostics, RunState, ScopedDiagnostics, execute, substitute,
)
from ..failures import Axis, CollapseError, FailureRecord, Finding, Status
from ..gates.gate_results import GateOutcome
from ..gates.l0_closure import ValueProvenance
from ..lifecycle.reevaluation import reevaluate
from ..lifecycle.state_transitions import Track
from ..lifecycle.unknown_expiry import (
    ExpiryTrigger, ExpiryTriggerKind, UnknownDetermination, UnknownState, check_expiry,
)
from ..reference.continuity import (
    ConfigurationObservation, ConfigurationPersistence, ContinuityCell,
    SystemPersistence, classify_continuity, compare_configurations,
)
from ..reference.return_test import ReturnOutcome, ReturnTestSpec, return_test
from .cross_system import DECISION, EVIDENCE, diagnostic_report, fixtures


def run(fixture, experiment=None, plan=None, **kwargs):
    registry = EquationRegistry()
    registry.register(fixture.model)
    return execute(
        registry, fixture.model.equation_id, fixture.model.revision,
        experiment if experiment is not None else fixture.experiment,
        plan if plan is not None else fixture.plan, DECISION, **kwargs,
    )


def assessment(fixture, kind=EvidenceKind.PHYSICAL):
    return Assessment(
        f"constructed-support-{fixture.system_class}",
        fixture.model.description().digest(), fixture.experiment.context.digest(),
        kind, Judgment.SUPPORTS, DECISION, EVIDENCE,
        "Synthetic assessor input only; not independently established physical adequacy.",
        record(Axis.PHYSICAL, Status.OK) if kind in (EvidenceKind.PHYSICAL, EvidenceKind.EMPIRICAL)
        else FailureRecord(),
    )


def record(axis, severity, code="PLANTED_CROSS_SYSTEM_FINDING"):
    return FailureRecord((Finding(axis, severity, code, "Constructed fault.", __name__, EVIDENCE),))


def ladder():
    return tuple(SensitivityCase.from_maps(
        f"selected-size-{size}", size, detected,
        {"effect": size}, {"signal": 0}, {"signal": 0},
    ) for size, detected in ((0.0, False), (0.25, True), (1.0, True)))


class SelectedReadout:
    """Diagnostic-only threshold readout; no claim to model a physical sensor."""

    def __init__(self, fixture, invalid_null=None):
        self.instrument_id = f"constructed-{fixture.system_class}-readout"
        self.invalid_null = invalid_null
        self.calls = 0

    def run(self, inputs):
        self.calls += 1
        effect = inputs["effect"]
        return {"signal": self.invalid_null if effect == 0 and self.invalid_null is not None
                else effect if effect >= 0.25 else 0.0}


class CrossSystemRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.systems = fixtures()

    def test_five_selected_classes_span_three_closed_backends(self):
        self.assertEqual(len(self.systems), 5)
        self.assertEqual(len({f.system_class for f in self.systems}), 5)
        self.assertEqual(len({type(f.model) for f in self.systems}), 3)
        for f in self.systems:
            with self.subTest(system=f.system_class):
                self.assertEqual({c.domain for c in f.experiment.context.conditions}, set(Domain))
                self.assertTrue(all(c.basis is ConditionBasis.SELECTED
                                    for c in f.experiment.context.conditions))
                self.assertTrue(f.question)
                self.assertTrue(f.accounting_meaning)
                self.assertTrue(f.limitations)

    def test_native_outputs_follow_full_path_but_physics_stays_untested(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                result = f.run()
                self.assertIs(result.state, RunState.COMPUTED)
                self.assertEqual({o.name: o.value for o in result.outputs}, dict(f.expected))
                self.assertIs(result.l0.outcome, GateOutcome.PASS)
                self.assertTrue(result.known_answer.validated_within_tested_cases)
                self.assertTrue(result.null.clean_within_tested_cases)
                self.assertIs(result.record.instrument, Status.OK)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertIs(result.applicability.state, ApplicabilityState.UNKNOWN)
                self.assertTrue(all(o.uncertainty is None for o in result.outputs))
                self.assertEqual(result.stages, (
                    "protocol-binding:pass", "l0:pass", "applicability:candidate-domain",
                    "validation-plan:pass", "known-answer:pass", "null:pass", "calculation:computed",
                ))
                with self.assertRaises(CollapseError):
                    bool(result.record)

    def test_known_answers_are_not_generated_with_backend(self):
        with patch("playground.equations.substitution._calculate",
                   side_effect=AssertionError("fixture criteria cannot call backend")):
            self.assertEqual(len(fixtures()), 5)

    def test_diagnostic_and_mathematical_assessments_do_not_supply_physics(self):
        for f in self.systems:
            for kind in (EvidenceKind.MATHEMATICAL, EvidenceKind.DIAGNOSTIC):
                with self.subTest(system=f.system_class, kind=kind):
                    result = f.run(assessments=(assessment(f, kind),))
                    self.assertIs(result.record.physical, Status.UNTESTED)
                    self.assertIs(result.applicability.state, ApplicabilityState.UNKNOWN)

    def test_explicit_synthetic_physical_support_is_not_erased_by_bad_instrument(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                bad = ScopedDiagnostics(
                    f.model.description().digest(), f.experiment.context.digest(),
                    record(Axis.INSTRUMENT, Status.FAILED),
                )
                result = f.run(assessments=(assessment(f),), diagnostics=bad)
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.physical, Status.OK)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertEqual(result.outputs, ())

    def test_instrument_ok_can_coexist_with_inadequate_experimental_design(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                finding = record(Axis.INSTRUMENT, Status.OK).merge(
                    record(Axis.DETERMINATION, Status.FAILED))
                experiment = replace(f.experiment, diagnostics=(ExperimentalDiagnostics(
                    f.experiment.context.digest(), finding, DECISION, EVIDENCE,
                ),))
                result = run(f, experiment=experiment)
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.instrument, Status.OK)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)

    def test_backend_bias_is_instrument_failure_for_every_class(self):
        from ..equations.substitution import _calculate
        for f in self.systems:
            with self.subTest(system=f.system_class):
                def biased(model, inputs):
                    values = _calculate(model, inputs)
                    return {k: v + 1.0 for k, v in values.items()}
                with patch("playground.equations.substitution._calculate", side_effect=biased):
                    result = f.run()
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertIsNone(result.null)
                self.assertEqual(result.outputs, ())

    def test_nominal_backend_error_after_clean_harnesses_stays_instrument_failure(self):
        from ..equations.substitution import _calculate
        for f in self.systems:
            with self.subTest(system=f.system_class):
                calls = 0
                def breaks_on_nominal(model, inputs):
                    nonlocal calls
                    calls += 1
                    if calls > len(f.plan.known_answers) + len(f.plan.nulls):
                        raise ArithmeticError("planted nominal-only fault")
                    return _calculate(model, inputs)
                with patch("playground.equations.substitution._calculate", side_effect=breaks_on_nominal):
                    result = f.run()
                self.assertIs(result.state, RunState.ERROR)
                self.assertTrue(result.known_answer.validated_within_tested_cases)
                self.assertTrue(result.null.clean_within_tested_cases)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertEqual(result.outputs, ())

    def test_new_revision_reruns_every_layer_and_does_not_inherit_support(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                parent = f.run(assessments=(assessment(f),))
                replacement = replace(f.model, revision="2")
                plan = replace(f.plan, equation_digest=replacement.digest())
                registry = EquationRegistry()
                registry.register(replacement)
                result = substitute(parent, registry, replacement.equation_id, "2", plan, DECISION)
                self.assertIs(result.state, RunState.COMPUTED)
                self.assertEqual(result.stages, parent.stages[:2] + (
                    "applicability:candidate-domain",) + parent.stages[3:])
                self.assertIsNot(result.known_answer, parent.known_answer)
                self.assertIsNot(result.null, parent.null)
                self.assertIsNot(result.l0, parent.l0)
                self.assertEqual(result.supplied_assessments, ())
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertEqual(result.parent_run_digest, parent.digest())

    def test_experiment_defect_survives_compatible_equation_replacement(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                experiment = replace(f.experiment, diagnostics=(ExperimentalDiagnostics(
                    f.experiment.context.digest(), record(Axis.INSTRUMENT, Status.FAILED),
                    DECISION, EVIDENCE,
                ),))
                parent = run(f, experiment=experiment)
                replacement = replace(f.model, revision="2")
                registry = EquationRegistry()
                registry.register(replacement)
                result = substitute(
                    parent, registry, replacement.equation_id, "2",
                    replace(f.plan, equation_digest=replacement.digest()), DECISION,
                )
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertEqual(result.experiment.diagnostics, experiment.diagnostics)

    def test_null_only_artifact_is_caught_after_clean_known_answers(self):
        from ..equations.substitution import _calculate
        for f in self.systems:
            with self.subTest(system=f.system_class):
                null_inputs = dict(f.plan.nulls[0].inputs)
                def contaminated(model, inputs):
                    values = _calculate(model, inputs)
                    return {k: v + 1.0 for k, v in values.items()} if inputs == null_inputs else values
                with patch("playground.equations.substitution._calculate", side_effect=contaminated):
                    result = f.run()
                self.assertTrue(result.known_answer.validated_within_tested_cases)
                self.assertFalse(result.null.clean_within_tested_cases)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertEqual(result.outputs, ())

    def test_empty_harnesses_never_become_vacuous_success(self):
        for f in self.systems:
            for field in ("known_answers", "nulls"):
                with self.subTest(system=f.system_class, field=field):
                    result = run(f, plan=replace(f.plan, **{field: ()}))
                    self.assertIs(result.state, RunState.BLOCKED)
                    self.assertIs(result.record.physical, Status.UNTESTED)
                    self.assertEqual(result.outputs, ())

    def test_plan_units_provenance_and_anchor_binding_are_required(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                units = ((f.plan.input_units[0][0], "wrong-unit"),) + f.plan.input_units[1:]
                result = run(f, plan=replace(f.plan, input_units=units))
                self.assertIs(result.record.determination, Status.FAILED)
                with self.assertRaises(ValueError):
                    replace(f.plan, evidence=())
                changed = replace(f.experiment.anchor, label="different-reference")
                result = run(f, experiment=replace(f.experiment, anchor=changed))
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertEqual(result.outputs, ())

    def test_incomplete_declared_accounting_blocks_all_classes(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                protocol = f.experiment.boundary
                experiment = replace(f.experiment, boundary=replace(
                    protocol, accounting=replace(protocol.accounting, declared_complete=False),
                ))
                result = run(f, experiment=experiment)
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertIsNone(result.known_answer)

    def test_stated_storage_misclosure_is_physical_failure_not_instrument_failure(self):
        for f in self.systems[:3]:
            for quantity in f.experiment.boundary.accounting.accounts:
                with self.subTest(system=f.system_class, quantity=quantity.quantity):
                    protocol = f.experiment.boundary
                    accounts = tuple(replace(a, final=a.final + 1) if a is quantity else a
                                     for a in protocol.accounting.accounts)
                    experiment = replace(f.experiment, boundary=replace(
                        protocol, accounting=replace(protocol.accounting, accounts=accounts),
                    ))
                    result = run(f, experiment=experiment)
                    self.assertIs(result.record.physical, Status.FAILED)
                    self.assertIs(result.record.instrument, Status.UNTESTED)
                    self.assertEqual(result.outputs, ())

    def test_measured_storage_misclosure_remains_ambiguous(self):
        for f in self.systems[:3]:
            with self.subTest(system=f.system_class):
                protocol = f.experiment.boundary
                first, *rest = protocol.accounting.accounts
                first = replace(first, final=first.final + 1,
                                final_provenance=ValueProvenance.MEASURED)
                experiment = replace(f.experiment, boundary=replace(
                    protocol, accounting=replace(protocol.accounting, accounts=(first, *rest)),
                ))
                result = run(f, experiment=experiment)
                self.assertIs(result.record.physical, Status.INDETERMINATE)
                self.assertIs(result.record.instrument, Status.INDETERMINATE)
                self.assertEqual(result.outputs, ())

    def test_founder_cohort_change_is_protocol_failure_before_l0(self):
        f = self.systems[-1]
        protocol = f.experiment.boundary
        first = replace(protocol.accounting.accounts[0], final=3)
        result = run(f, experiment=replace(f.experiment, boundary=replace(
            protocol, accounting=replace(protocol.accounting, accounts=(first,)),
        )))
        self.assertIs(result.record.determination, Status.FAILED)
        self.assertIs(result.record.physical, Status.UNTESTED)
        self.assertIsNone(result.l0)

    def test_structural_accounting_cannot_detect_unregistered_physics(self):
        # Pin the actual limitation, rather than pretending the gate knows
        # whether a human omitted a physically relevant account.
        f = self.systems[1]
        protocol = f.experiment.boundary
        energy_only = tuple(a for a in protocol.accounting.accounts if a.quantity == "energy")
        result = run(f, experiment=replace(f.experiment, boundary=replace(
            protocol, accounting=replace(protocol.accounting, accounts=energy_only),
            quantity_units=(("energy", "J"),),
        )))
        self.assertIs(result.l0.outcome, GateOutcome.PASS)
        self.assertIs(result.record.physical, Status.UNTESTED)
        self.assertIs(result.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertEqual(len(result.experiment.boundary.accounting.accounts), 1)

    def test_numerical_twins_are_not_equivalent_physical_descriptions(self):
        capacitor, spring = self.systems[1:3]
        cap = capacitor.run()
        mechanical = spring.run()
        self.assertEqual([v.value for v in cap.outputs], [v.value for v in mechanical.outputs])
        self.assertNotEqual([v.unit for v in cap.outputs], [v.unit for v in mechanical.outputs])
        self.assertNotEqual(cap.equation.description().digest(), mechanical.equation.description().digest())
        self.assertNotEqual(cap.experiment.context.digest(), mechanical.experiment.context.digest())


class CrossContextTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.systems = fixtures()

    def test_all_twenty_foreign_plans_rejected_before_backend(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                with patch("playground.equations.substitution._calculate",
                           side_effect=AssertionError("foreign plan reached backend")) as backend:
                    result = run(target, plan=source.plan)
                backend.assert_not_called()
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertEqual(result.outputs, ())

    def test_rebinding_foreign_plan_digests_cannot_hide_different_ports_units(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                plan = replace(source.plan, equation_digest=target.model.digest(),
                               context_digest=target.experiment.context.digest())
                result = run(target, plan=plan)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertEqual(result.outputs, ())

    def test_model_substitution_into_foreign_experiment_is_out_of_scope(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                registry = EquationRegistry()
                registry.register(source.model)
                parent = source.run()
                registry.register(target.model)
                result = substitute(parent, registry, target.model.equation_id,
                                    target.model.revision, target.plan, DECISION)
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertEqual(result.parent_run_digest, parent.digest())
                self.assertEqual(result.experiment, parent.experiment)
                self.assertEqual(result.outputs, ())

    def test_physical_evidence_never_transfers_between_classes(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                result = target.run(assessments=(assessment(source),))
                self.assertIs(result.record.physical, Status.UNTESTED)
                self.assertIs(result.applicability.state, ApplicabilityState.UNKNOWN)
                self.assertEqual(result.applicability.assessments, ())

    def test_equation_diagnostics_never_transfer_between_classes(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                diagnostics = ScopedDiagnostics(
                    source.model.description().digest(), source.experiment.context.digest(),
                    record(Axis.INSTRUMENT, Status.OK),
                )
                result = target.run(diagnostics=diagnostics)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertIs(result.record.instrument, Status.UNTESTED)

    def test_cartesian_map_preserves_native_unknown_and_foreign_outside(self):
        matrix = build_map(
            tuple(f.model.description() for f in self.systems),
            tuple(f.experiment.context for f in self.systems),
        )
        self.assertEqual(len(matrix.cells), 25)
        for cell in matrix.cells:
            native = any(cell.description == f.model.description()
                         and cell.context == f.experiment.context for f in self.systems)
            with self.subTest(model=cell.description.model_id, context=cell.context.context_id):
                self.assertIs(cell.scope, ScopeState.INSIDE if native else ScopeState.OUTSIDE)
                if native:
                    self.assertIs(cell.state, ApplicabilityState.UNKNOWN)
                self.assertIs(cell.record.physical, Status.UNTESTED)

    def test_simultaneous_synthetic_support_does_not_create_ranking(self):
        mapping = build_map(
            tuple(f.model.description() for f in self.systems),
            tuple(f.experiment.context for f in self.systems),
            tuple(assessment(f) for f in self.systems),
        )
        supported = [c for c in mapping.cells if c.state is ApplicabilityState.SUPPORTED]
        self.assertEqual(len(supported), 5)
        self.assertNotIn("ranking", mapping.to_dict())

    def test_control_observer_environment_boundary_changes_require_fresh_scope(self):
        for f in self.systems:
            for domain in (Domain.BOUNDARY, Domain.OBSERVER, Domain.ENVIRONMENT, Domain.CONTROL):
                with self.subTest(system=f.system_class, domain=domain):
                    selected = next(c for c in f.experiment.context.conditions
                                    if c.key == "observation_window") if domain is Domain.CONTROL else next(
                                        c for c in f.experiment.context.conditions if c.domain is domain)
                    context = replace(f.experiment.context, conditions=tuple(
                        replace(c, value=2.0 if domain is Domain.CONTROL else f"changed-{c.value}")
                        if c is selected else c
                        for c in f.experiment.context.conditions
                    ))
                    result = assess(f.model.description(), context, (assessment(f),))
                    self.assertIs(result.scope, ScopeState.OUTSIDE)
                    self.assertIs(result.record.physical, Status.UNTESTED)

    def test_output_record_retains_conditions_decisions_provenance_and_unknowns(self):
        payload = diagnostic_report()
        encoded = json.dumps(payload, allow_nan=False)
        decoded = json.loads(encoded)
        self.assertEqual(len(decoded["systems"]), 5)
        self.assertEqual(len(decoded["applicability"]["cells"]), 25)
        for system in decoded["systems"]:
            with self.subTest(system=system["system_class"]):
                result = system["run"]
                for field in ("experiment", "plan", "selection", "record", "notes",
                              "context_digest", "plan_digest", "equation_digest"):
                    self.assertIn(field, result)
                self.assertTrue(result["plan"]["evidence"])
                self.assertTrue(result["experiment"]["context"]["uncertainty_notes"])
                self.assertTrue(system["limitations"])
                self.assertTrue(all(o["uncertainty"] is None for o in result["outputs"]))

    def test_fixture_snapshots_are_immutable(self):
        f = self.systems[0]
        with self.assertRaises(FrozenInstanceError):
            f.system_class = "reclassified"


class CrossSystemLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.systems = fixtures()

    def return_result(self, fixture, delta=0, measured=False, expected=True, empty=False):
        anchor = fixture.experiment.anchor
        return return_test(ReturnTestSpec.from_maps(
            anchor,
            {} if empty else {q: (v + delta, ValueProvenance.MEASURED if measured
                                 else ValueProvenance.SPECIFIED) for q, v in anchor.quantities},
            {} if empty else {q: 0.01 for q, _ in anchor.quantities}, expected,
        ))

    def test_return_and_nonreturn_preserve_provenance_for_every_class(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                returned = self.return_result(f)
                self.assertIs(returned.outcome, ReturnOutcome.RETURNED)
                self.assertIs(returned.record.physical, Status.UNTESTED)
                specified = self.return_result(f, delta=1)
                self.assertIs(specified.record.physical, Status.FAILED)
                self.assertIs(specified.record.instrument, Status.UNTESTED)
                measured = self.return_result(f, delta=1, measured=True)
                self.assertIs(measured.record.physical, Status.INDETERMINATE)
                self.assertIs(measured.record.instrument, Status.INDETERMINATE)
                transition = self.return_result(f, delta=1, expected=False)
                self.assertIs(transition.outcome, ReturnOutcome.NOT_RETURNED)
                self.assertIs(transition.record.physical, Status.UNTESTED)
                # Surrogate returns concern only fixed nodes/founders, never
                # transport, total population or physical organization.

    def test_empty_return_protocol_is_not_permanent_or_even_temporary_persistence(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                result = self.return_result(f, empty=True)
                self.assertIs(result.outcome, ReturnOutcome.INDETERMINATE)
                self.assertIs(result.system_persistence, SystemPersistence.INDETERMINATE)
                self.assertIs(result.record.physical, Status.UNTESTED)

    def test_invalid_return_tolerances_do_not_certify_return_or_refute_physics(self):
        for f in self.systems:
            for invalid in (float("nan"), float("inf"), -1, True):
                with self.subTest(system=f.system_class, tolerance=invalid):
                    anchor = f.experiment.anchor
                    result = return_test(ReturnTestSpec.from_maps(
                        anchor, {q: (v, ValueProvenance.SPECIFIED) for q, v in anchor.quantities},
                        {q: invalid for q, _ in anchor.quantities}, True,
                    ))
                    self.assertIs(result.outcome, ReturnOutcome.INDETERMINATE)
                    self.assertIs(result.record.determination, Status.FAILED)
                    self.assertIs(result.record.physical, Status.UNTESTED)

    def test_invalid_return_readout_is_instrument_failure_not_physical_change(self):
        for f in self.systems:
            for invalid in (float("nan"), float("inf"), True, "bad"):
                with self.subTest(system=f.system_class, readout=invalid):
                    anchor = f.experiment.anchor
                    result = return_test(ReturnTestSpec.from_maps(
                        anchor, {q: (invalid, ValueProvenance.MEASURED) for q, _ in anchor.quantities},
                        {q: 0.01 for q, _ in anchor.quantities}, True,
                    ))
                    self.assertIs(result.outcome, ReturnOutcome.INDETERMINATE)
                    self.assertIs(result.record.instrument, Status.FAILED)
                    self.assertIs(result.record.physical, Status.UNTESTED)

    def test_duplicate_or_untyped_return_records_are_design_failures(self):
        for f in self.systems:
            anchor = f.experiment.anchor
            valid = ReturnTestSpec.from_maps(
                anchor, {q: (v, ValueProvenance.SPECIFIED) for q, v in anchor.quantities},
                {q: 0.01 for q, _ in anchor.quantities}, True,
            )
            malformed = (
                replace(valid, returned=valid.returned + (valid.returned[0],)),
                replace(valid, tolerances=valid.tolerances + (valid.tolerances[0],)),
                replace(valid, anchor=replace(anchor, quantities=anchor.quantities + (anchor.quantities[0],))),
                replace(valid, expected_return="yes"),
                replace(valid, returned=(
                    replace(valid.returned[0], provenance="measured"), *valid.returned[1:],
                )),
            )
            for spec in malformed:
                with self.subTest(system=f.system_class, protocol=spec):
                    result = return_test(spec)
                    self.assertIs(result.outcome, ReturnOutcome.INDETERMINATE)
                    self.assertIs(result.record.determination, Status.FAILED)
                    self.assertIs(result.record.physical, Status.UNTESTED)

    def test_missing_return_observation_cannot_fill_a_continuity_cell(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                anchor = f.experiment.anchor
                result = return_test(ReturnTestSpec.from_maps(
                    anchor, {}, {q: 0.01 for q, _ in anchor.quantities}, True,
                ))
                self.assertIs(result.record.determination, Status.INDETERMINATE)
                self.assertIs(classify_continuity(
                    result.system_persistence, ConfigurationPersistence.PERSISTED),
                    ContinuityCell.INDETERMINATE)
                self.assertIs(result.record.physical, Status.UNTESTED)

    def test_system_return_does_not_imply_configuration_persistence(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                before = ConfigurationObservation.from_map(f.system_class, {"arrangement": "A"})
                after = ConfigurationObservation.from_map(f.system_class, {"arrangement": "B"})
                self.assertIs(compare_configurations(before, after), ConfigurationPersistence.CHANGED)
                for delta, configuration, expected in (
                    (0, ConfigurationPersistence.PERSISTED, ContinuityCell.CONTINUOUS),
                    (0, ConfigurationPersistence.CHANGED, ContinuityCell.RETURN_WITH_RECONFIGURATION),
                    (1, ConfigurationPersistence.PERSISTED, ContinuityCell.DRIFT_WITH_STABLE_CONFIGURATION),
                    (1, ConfigurationPersistence.CHANGED, ContinuityCell.DISCONTINUOUS),
                ):
                    result = self.return_result(f, delta=delta, expected=False)
                    self.assertIs(classify_continuity(result.system_persistence, configuration), expected)
                self.assertIs(classify_continuity(
                    SystemPersistence.PERSISTED, ConfigurationPersistence.INDETERMINATE),
                    ContinuityCell.INDETERMINATE)

    def test_non_detection_without_sensitivity_never_means_absence(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                observation = NonDetectionObservation.from_map(
                    f.system_class, f.sensitivity_conditions(), 1.0,
                )
                nd = record_non_detection(observation, None)
                self.assertFalse(nd.qualified)
                self.assertIsInstance(claim_absence("no-calibration", nd), AbsenceRejection)
                self.assertIs(nd.record.physical, Status.UNTESTED)

    def test_scoped_absence_requires_native_calibration_and_sufficient_size(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                sensitivity = establish_sensitivity(SelectedReadout(f), ladder(), f.sensitivity_conditions())
                self.assertTrue(sensitivity.established)
                self.assertEqual(sensitivity.detection_limit, 0.25)
                observation = NonDetectionObservation.from_map(
                    f.system_class, f.sensitivity_conditions(), 1.0,
                )
                nd = record_non_detection(observation, sensitivity)
                claim = claim_absence("constructed-scoped-claim", nd)
                self.assertIsInstance(claim, AbsenceClaim)
                self.assertEqual(dict(claim.scope), f.sensitivity_conditions())
                self.assertEqual(claim.effect_size_floor, 1.0)
                small = record_non_detection(replace(observation, effect_size_of_interest=0.01), sensitivity)
                self.assertIsInstance(claim_absence("too-small", small), AbsenceRejection)
                self.assertIs(nd.record.physical, Status.UNTESTED)

    def test_calibration_cannot_transfer_even_between_dimensionless_surrogates(self):
        for source, target in permutations(self.systems, 2):
            with self.subTest(source=source.system_class, target=target.system_class):
                sensitivity = establish_sensitivity(
                    SelectedReadout(source), ladder(), source.sensitivity_conditions(),
                )
                observation = NonDetectionObservation.from_map(
                    target.system_class, target.sensitivity_conditions(), 1.0,
                )
                claim = claim_absence("foreign-calibration", record_non_detection(observation, sensitivity))
                self.assertIsInstance(claim, AbsenceRejection)
                self.assertIs(claim.record.determination, Status.INDETERMINATE)
                self.assertIs(claim.record.physical, Status.UNTESTED)

    def test_nonfinite_null_output_cannot_establish_sensitivity(self):
        for f in self.systems:
            for invalid in (float("nan"), float("inf"), float("-inf"), True, "bad"):
                with self.subTest(system=f.system_class, invalid=invalid):
                    sensitivity = establish_sensitivity(
                        SelectedReadout(f, invalid_null=invalid), ladder(), f.sensitivity_conditions(),
                    )
                    self.assertFalse(sensitivity.established)
                    self.assertIs(sensitivity.record.instrument, Status.FAILED)
                    self.assertIs(sensitivity.record.physical, Status.UNTESTED)

    def test_invalid_sensitivity_criteria_fail_design_before_readout(self):
        f = self.systems[0]
        cases = (
            replace(ladder()[1], effect_size=float("nan")),
            replace(ladder()[1], effect_size=float("inf")),
            replace(ladder()[1], effect_size=True),
            replace(ladder()[1], effect_size=-1),
            replace(ladder()[1], effect_size=0),
            replace(ladder()[1], null_outputs=(), tolerances=()),
            replace(ladder()[1], tolerances=(("signal", -1),)),
            replace(ladder()[1], tolerances=()),
            replace(ladder()[1], expected_detectable="yes"),
        )
        for case in cases:
            with self.subTest(case=case):
                instrument = SelectedReadout(f)
                result = establish_sensitivity(instrument, (case,), f.sensitivity_conditions())
                self.assertFalse(result.established)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertEqual(instrument.calls, 0)

    def test_entire_sensitivity_protocol_preflight_precedes_any_readout(self):
        for f in self.systems:
            for cases in (ladder() + (ladder()[0],),
                          (ladder()[0], replace(ladder()[1], tolerances=()))):
                with self.subTest(system=f.system_class, cases=cases):
                    instrument = SelectedReadout(f)
                    result = establish_sensitivity(instrument, cases, f.sensitivity_conditions())
                    self.assertIs(result.record.determination, Status.FAILED)
                    self.assertFalse(result.established)
                    self.assertEqual(instrument.calls, 0)

    def test_detection_limit_alone_does_not_establish_a_valid_instrument(self):
        for f in self.systems:
            valid = establish_sensitivity(SelectedReadout(f), ladder(), f.sensitivity_conditions())
            for malformed in (
                replace(valid, detection_limit=float("nan")),
                replace(valid, detection_limit=float("inf")),
                replace(valid, detection_limit=0),
                replace(valid, record=FailureRecord()),
                replace(valid, record=valid.record.merge(record(Axis.INSTRUMENT, Status.FAILED))),
                replace(valid, record=valid.record.merge(record(Axis.DETERMINATION, Status.FAILED))),
            ):
                with self.subTest(system=f.system_class, sensitivity=malformed):
                    self.assertFalse(malformed.established)
                    observation = NonDetectionObservation.from_map(
                        f.system_class, f.sensitivity_conditions(), 1.0,
                    )
                    self.assertIsInstance(claim_absence(
                        "invalid-certificate", record_non_detection(observation, malformed)),
                        AbsenceRejection)

    def test_sensitivity_with_missing_asserted_output_is_instrument_failure(self):
        for f in self.systems:
            instrument = SelectedReadout(f)
            with self.subTest(system=f.system_class):
                with patch.object(instrument, "run", return_value={"unrelated": 1.0}):
                    result = establish_sensitivity(instrument, ladder(), f.sensitivity_conditions())
                self.assertFalse(result.established)
                self.assertIs(result.record.instrument, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)

    def test_unrelated_unknown_expiry_does_not_poison_other_classes(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                result = f.run(dependency_states={"unrelated-class-dependency": UnknownState.EXPIRED})
                self.assertIs(result.state, RunState.COMPUTED)
                self.assertIs(result.record.physical, Status.UNTESTED)

    def test_invalid_effect_size_cannot_create_absence_claim(self):
        for f in self.systems:
            sensitivity = establish_sensitivity(SelectedReadout(f), ladder(), f.sensitivity_conditions())
            for size in (float("nan"), float("inf"), -1, True):
                with self.subTest(system=f.system_class, size=size):
                    observation = NonDetectionObservation.from_map(
                        f.system_class, f.sensitivity_conditions(), size,
                    )
                    nd = record_non_detection(observation, sensitivity)
                    self.assertFalse(nd.qualified)
                    self.assertIsInstance(claim_absence("invalid-size", nd), AbsenceRejection)
                    self.assertIs(nd.record.determination, Status.FAILED)

    def test_unknown_expiry_is_revision_not_physical_refutation(self):
        for f in self.systems:
            with self.subTest(system=f.system_class):
                trigger = ExpiryTrigger("observer-change", ExpiryTriggerKind.INSTRUMENT_CHANGE)
                unknown = UnknownDetermination.from_map(
                    f"adequacy-{f.system_class}", "Physical adequacy remains UNKNOWN.",
                    f.sensitivity_conditions(), (trigger,), EVIDENCE,
                )
                expired = check_expiry(unknown, ("observer-change",))
                self.assertTrue(expired.expired)
                self.assertIs(unknown.state, UnknownState.UNKNOWN)
                self.assertIs(expired.determination.state, UnknownState.EXPIRED)
                self.assertIs(expired.transition.track, Track.DETERMINATION)
                self.assertEqual(expired.record.findings, ())
                # Only explicitly declared dependencies are relied upon.
                dependent_model = replace(f.model, unknown_dependencies=(unknown.determination_id,))
                dependent = replace(f, model=dependent_model, plan=replace(
                    f.plan, equation_digest=dependent_model.digest(),
                ))
                result = dependent.run(dependency_states={unknown.determination_id: UnknownState.EXPIRED})
                self.assertIs(result.state, RunState.BLOCKED)
                self.assertIs(result.record.determination, Status.FAILED)
                self.assertIs(result.record.physical, Status.UNTESTED)
                revisited = reevaluate(
                    expired.determination, unknown.determination_id + "-v2",
                    "Adequacy still UNKNOWN under revised observer.",
                    "Observer changed; no new physical verdict.", f.sensitivity_conditions(),
                    evidence=EVIDENCE,
                )
                self.assertIs(revisited.original.state, UnknownState.REEVALUATED)
                self.assertIs(revisited.successor.state, UnknownState.UNKNOWN)
                self.assertEqual(revisited.original.evidence, unknown.evidence)
                successor_model = replace(f.model, unknown_dependencies=(revisited.successor.determination_id,))
                successor_fixture = replace(f, model=successor_model, plan=replace(
                    f.plan, equation_digest=successor_model.digest(),
                ))
                self.assertIs(successor_fixture.run(dependency_states={
                    revisited.successor.determination_id: UnknownState.UNKNOWN,
                }).record.physical, Status.UNTESTED)


if __name__ == "__main__":
    unittest.main()
