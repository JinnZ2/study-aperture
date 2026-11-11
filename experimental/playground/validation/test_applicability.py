"""Milestone 4: adversarial applicability tests. All fixtures CONSTRUCTED."""

import json
import unittest
from dataclasses import replace

from ..applicability.example import DECISION, example_map, fixture, support
from ..applicability.mapping import (
    ApplicabilityState as A, Assessment, ConditionBasis, Constraint, Domain,
    EvidenceKind, Judgment, ScopeState as S, assess, build_map,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..lifecycle.unknown_expiry import (
    ExpiryTrigger, ExpiryTriggerKind, UnknownDetermination, UnknownState, check_expiry,
)


def failed(axis, severity=Status.FAILED):
    return FailureRecord((Finding(axis, severity, "PLANTED", "planted finding",
                                  "validation.test_applicability"),))


class ApplicabilityTests(unittest.TestCase):
    def setUp(self):
        self.model, self.context = fixture()

    def change_energy(self, **changes):
        return replace(self.context, conditions=tuple(
            replace(c, **changes) if c.key == "energy" else c
            for c in self.context.conditions
        ))

    def result(self, context=None, model=None, **kwargs):
        return assess(model or self.model, context or self.context, **kwargs)

    def supported(self, context=None, model=None, **kwargs):
        d, c = model or self.model, context or self.context
        return assess(d, c, (support(d, c),), **kwargs)

    def test_matching_domain_does_not_prove_adequacy(self):
        r = self.result()
        self.assertEqual((r.scope, r.state), (S.INSIDE, A.UNKNOWN))
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_bound_assessment_is_explicit_not_automatically_validated(self):
        r = self.supported()
        self.assertIs(r.state, A.SUPPORTED)
        self.assertEqual(r.assessments[0].decision, DECISION)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_math_and_diagnostic_pass_cannot_promote(self):
        for kind in (EvidenceKind.MATHEMATICAL, EvidenceKind.DIAGNOSTIC):
            with self.subTest(kind=kind):
                a = replace(support(self.model, self.context), kind=kind)
                r = self.result(assessments=(a,))
                self.assertIs(r.state, A.UNKNOWN)
                self.assertIs(r.record.physical, Status.UNTESTED)

    def test_selected_boundary_stays_selected(self):
        r = self.supported()
        match = next(m for m in r.matches if m.constraint.key == "boundary")
        self.assertIs(match.condition.basis, ConditionBasis.SELECTED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_outside_is_not_physical_failure(self):
        r = self.supported(self.change_energy(value=5.0))
        self.assertEqual((r.scope, r.state), (S.OUTSIDE, A.OUTSIDE))
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_unknown_numeric_uncertainty_stays_unknown(self):
        self.assertIs(self.supported(self.change_energy(uncertainty=None)).state, A.UNKNOWN)

    def test_uncertainty_straddling_boundary_is_unknown(self):
        r = self.supported(self.change_energy(value=3.0, uncertainty=0.1))
        self.assertEqual((r.scope, r.state), (S.UNKNOWN, A.UNKNOWN))

    def test_touching_edge_with_exact_value_is_inside(self):
        self.assertIs(self.result(self.change_energy(value=3.0, uncertainty=0.0)).scope, S.INSIDE)

    def test_interval_containment_not_nominal_value(self):
        self.assertIs(self.result(self.change_energy(value=2.0, uncertainty=2.0)).scope, S.UNKNOWN)

    def test_lower_boundary_rules(self):
        for value, uncertainty, scope in ((1., 0., S.INSIDE), (1., .1, S.UNKNOWN),
                                          (.8, .1, S.OUTSIDE)):
            with self.subTest(value=value, uncertainty=uncertainty):
                self.assertIs(self.result(self.change_energy(
                    value=value, uncertainty=uncertainty)).scope, scope)

    def test_units_are_not_implicitly_converted(self):
        r = self.supported(self.change_energy(unit="different-unit"))
        self.assertIs(r.state, A.UNKNOWN)
        self.assertIn("unit mismatch", " ".join(r.unresolved))

    def test_numeric_string_not_coerced(self):
        self.assertIs(self.result(self.change_energy(value="2", uncertainty=None)).scope, S.UNKNOWN)

    def test_missing_context_coordinate(self):
        c = replace(self.context, conditions=tuple(
            c for c in self.context.conditions if c.domain is not Domain.OBSERVER))
        self.assertIs(self.supported(c).state, A.UNKNOWN)

    def test_missing_description_coordinate(self):
        d = replace(self.model, constraints=tuple(
            r for r in self.model.constraints if r.domain is not Domain.BOUNDARY))
        self.assertIs(self.supported(model=d).state, A.UNKNOWN)

    def test_empty_domains_do_not_mean_universal_model(self):
        self.assertIs(self.supported(model=replace(self.model, constraints=())).state, A.UNKNOWN)

    def test_none_value_never_means_zero(self):
        c = self.change_energy(value=None, uncertainty=None)
        self.assertIs(self.supported(c).state, A.UNKNOWN)

    def test_assumed_context_condition_stays_unresolved(self):
        self.assertIs(self.supported(self.change_energy(basis=ConditionBasis.ASSUMED)).state, A.UNKNOWN)

    def test_model_assumptions_stay_visible(self):
        r = self.supported(model=replace(self.model, assumptions=("unmeasured coupling",)))
        self.assertIs(r.state, A.UNKNOWN)
        self.assertIn("unmeasured coupling", " ".join(r.unresolved))

    def test_evidence_never_transfers_to_new_context(self):
        r = self.result(self.change_energy(value=2.5),
                        assessments=(support(self.model, self.context),))
        self.assertIs(r.state, A.UNKNOWN)
        self.assertEqual(r.excluded_assessment_ids, ("synthetic-support",))

    def test_new_anchor_invalidates_evidence_binding(self):
        c = replace(self.context, anchor_digest="new-anchor")
        self.assertIs(self.result(c, assessments=(support(self.model, self.context),)).state, A.UNKNOWN)

    def test_new_model_revision_requires_new_evidence(self):
        d = replace(self.model, revision="2")
        self.assertIs(self.result(model=d, assessments=(support(self.model, self.context),)).state, A.UNKNOWN)

    def test_new_property_requires_new_evidence(self):
        d = replace(self.model, property="different-property")
        self.assertIs(self.result(model=d, assessments=(support(self.model, self.context),)).state, A.UNKNOWN)

    def test_profile_rule_change_cannot_reuse_evidence(self):
        d = replace(self.model, constraints=tuple(
            replace(r, upper=4.0) if r.key == "energy" else r for r in self.model.constraints))
        self.assertIs(self.result(model=d, assessments=(support(self.model, self.context),)).state, A.UNKNOWN)

    def test_provenance_change_changes_context_digest(self):
        c = self.change_energy(decision=replace(DECISION, chosen_by="different-selector"))
        self.assertNotEqual(c.digest(), self.context.digest())

    def test_uncertainty_change_changes_context_digest(self):
        self.assertNotEqual(self.change_energy(uncertainty=.2).digest(), self.context.digest())

    def test_order_of_conditions_not_semantic(self):
        c = replace(self.context, conditions=self.context.conditions[::-1])
        self.assertEqual(c.digest(), self.context.digest())
        self.assertEqual(replace(self.model, constraints=self.model.constraints[::-1]).digest(),
                         self.model.digest())

    def test_opposing_assessment_preserved_not_universal_failure(self):
        a = replace(support(self.model, self.context), judgment=Judgment.OPPOSES)
        r = self.result(assessments=(a,))
        self.assertIs(r.state, A.CONTRADICTED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_conflicting_evidence_never_ranked_away(self):
        yes = support(self.model, self.context, "yes")
        no = replace(yes, assessment_id="no", judgment=Judgment.OPPOSES)
        for items in ((yes, no), (no, yes)):
            r = self.result(assessments=items)
            self.assertIs(r.state, A.CONFLICTING)
            self.assertEqual(len(r.assessments), 2)

    def test_unresolved_assessment_prevents_promoting_support(self):
        yes = support(self.model, self.context, "yes")
        pending = replace(yes, assessment_id="pending", judgment=Judgment.UNRESOLVED)
        self.assertIs(self.result(assessments=(yes, pending)).state, A.UNKNOWN)

    def test_instrument_failure_blocks_not_model_failed(self):
        r = self.supported(diagnostics=failed(Axis.INSTRUMENT))
        self.assertIs(r.state, A.BLOCKED)
        self.assertIs(r.record.instrument, Status.FAILED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_determination_failure_blocks_not_model_failed(self):
        r = self.supported(diagnostics=failed(Axis.DETERMINATION))
        self.assertIs(r.state, A.BLOCKED)
        self.assertIs(r.record.physical, Status.UNTESTED)

    def test_inconclusive_diagnostic_not_ignored(self):
        self.assertIs(self.supported(diagnostics=failed(
            Axis.INSTRUMENT, Status.INDETERMINATE)).state, A.UNKNOWN)

    def test_physical_failure_cannot_be_overridden_by_support(self):
        r = self.supported(diagnostics=failed(Axis.PHYSICAL))
        self.assertIs(r.state, A.UNKNOWN)
        self.assertIs(r.record.physical, Status.FAILED)

    def test_bound_assessment_diagnostic_failure_blocks(self):
        a = replace(support(self.model, self.context), record=failed(Axis.INSTRUMENT))
        self.assertIs(self.result(assessments=(a,)).state, A.BLOCKED)

    def test_unbound_failure_does_not_contaminate_cell(self):
        a = replace(support(self.model, self.context), record=failed(Axis.INSTRUMENT))
        r = self.result(self.change_energy(value=2.5), assessments=(a,))
        self.assertIs(r.state, A.UNKNOWN)
        self.assertIs(r.record.instrument, Status.UNTESTED)

    def test_open_or_missing_unknown_dependency_stays_unknown(self):
        d = replace(self.model, unknown_dependencies=("coupling",))
        for states in ({}, {"coupling": UnknownState.UNKNOWN}):
            with self.subTest(states=states):
                r = self.supported(model=d, dependency_states=states)
                self.assertIs(r.state, A.UNKNOWN)
                self.assertNotEqual(r.record.determination, Status.FAILED)

    def test_expired_or_superseded_dependency_blocks(self):
        d = replace(self.model, unknown_dependencies=("coupling",))
        for state in (UnknownState.EXPIRED, UnknownState.REEVALUATED):
            r = self.supported(model=d, dependency_states={"coupling": state})
            self.assertIs(r.state, A.BLOCKED)
            self.assertIs(r.record.determination, Status.FAILED)
            self.assertIs(r.record.physical, Status.UNTESTED)

    def test_expiry_integration_no_physical_transition_inferred(self):
        u = UnknownDetermination("u", "unresolved", expiry_triggers=(
            ExpiryTrigger("new", ExpiryTriggerKind.NEW_EVIDENCE),))
        e = check_expiry(u, ("new",))
        d = replace(self.model, unknown_dependencies=("u",))
        r = self.supported(model=d, dependency_states={"u": e.determination.state})
        self.assertIs(r.state, A.BLOCKED)
        self.assertIs(r.record.physical, Status.UNTESTED)
        self.assertEqual(e.transition.track.value, "determination")

    def test_models_can_overlap_without_winner(self):
        m = example_map()
        self.assertEqual([c.state for c in m.cells[:2]], [A.SUPPORTED, A.SUPPORTED])
        self.assertFalse(hasattr(m, "winner"))
        self.assertEqual(len(m.cells), 8)

    def test_grid_does_not_extrapolate_support(self):
        self.assertEqual([c.state for c in example_map().cells],
                         [A.SUPPORTED, A.SUPPORTED, A.UNKNOWN, A.SUPPORTED,
                          A.UNKNOWN, A.UNKNOWN, A.OUTSIDE, A.OUTSIDE])

    def test_map_order_is_input_order_not_score(self):
        b = replace(self.model, model_id="B")
        m = build_map((b, self.model), (self.context,))
        self.assertEqual([c.description.model_id for c in m.cells], ["B", self.model.model_id])

    def test_map_diagnostics_are_cell_local(self):
        b = replace(self.model, model_id="B")
        m = build_map((self.model, b), (self.context,), (
            support(self.model, self.context, "a"), support(b, self.context, "b")),
            {(self.model.digest(), self.context.digest()): failed(Axis.INSTRUMENT)})
        self.assertEqual([c.state for c in m.cells], [A.BLOCKED, A.SUPPORTED])

    def test_report_json_retains_audit_trail(self):
        report = json.loads(example_map().to_json())
        first = report["cells"][0]
        self.assertEqual(first["context"]["anchor_digest"], "synthetic-anchor-digest-v1")
        self.assertEqual(first["description"]["property"], self.model.property)
        self.assertTrue(first["assessments"][0]["evidence"])
        self.assertTrue(first["context"]["uncertainty_notes"])
        self.assertTrue(first["ceases_to_hold"])
        self.assertTrue(report["limits"])
        json.dumps(example_map().to_dict(), allow_nan=False)

    def test_observation_window_cannot_imply_permanence(self):
        c = replace(self.context, conditions=tuple(
            replace(c, value=1000.0) if c.key == "observation-window" else c
            for c in self.context.conditions))
        self.assertIs(self.result(c, assessments=(support(self.model, self.context),)).state, A.OUTSIDE)

    def test_empty_map_contains_no_synthetic_support(self):
        self.assertEqual(build_map((), ()).cells, ())


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.model, self.context = fixture()
        self.energy = next(c for c in self.context.conditions if c.key == "energy")

    def test_invalid_numeric_values_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf"), True, object()):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.energy, value=value)

    def test_invalid_uncertainty_rejected(self):
        for value in (-1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replace(self.energy, uncertainty=value)

    def test_invalid_constraint_bounds_rejected(self):
        for lo, hi in ((3., 1.), (None, 3.), (1., None), (float("nan"), 3.),
                       (1., float("inf")), (False, 1.)):
            with self.subTest(lo=lo, hi=hi), self.assertRaises(ValueError):
                Constraint("energy", Domain.ENVIRONMENT, DECISION, lower=lo, upper=hi)

    def test_empty_or_mixed_constraint_rejected(self):
        with self.assertRaises(ValueError):
            Constraint("x", Domain.CONTROL, DECISION)
        with self.assertRaises(ValueError):
            Constraint("x", Domain.CONTROL, DECISION, equals="one", lower=1., upper=2.)

    def test_duplicate_context_and_constraint_keys_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.context, conditions=self.context.conditions + (self.energy,))
        with self.assertRaises(ValueError):
            replace(self.model, constraints=self.model.constraints * 2)

    def test_evidence_required_for_measured_condition(self):
        with self.assertRaises(ValueError):
            replace(self.energy, basis=ConditionBasis.MEASURED)
        c = replace(self.energy, basis=ConditionBasis.MEASURED,
                    evidence=(EvidenceRef("measurement", "run-1"),))
        self.assertIs(c.basis, ConditionBasis.MEASURED)

    def test_assessment_without_provenance_rejected(self):
        a = support(self.model, self.context)
        for changes in ({"evidence": ()}, {"uncertainty": ""},
                        {"evidence": (EvidenceRef("", ""),)}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(a, **changes)

    def test_duplicate_assessment_ids_rejected(self):
        a = support(self.model, self.context)
        with self.assertRaises(ValueError):
            assess(self.model, self.context, (a, a))

    def test_duplicate_map_coordinates_rejected(self):
        with self.assertRaises(ValueError):
            build_map((self.model, self.model), (self.context,))
        with self.assertRaises(ValueError):
            build_map((self.model,), (self.context, self.context))

    def test_untyped_dependency_state_rejected(self):
        d = replace(self.model, unknown_dependencies=("u",))
        with self.assertRaises(ValueError):
            assess(d, self.context, dependency_states={"u": "unknown"})

    def test_empty_provenance_text_rejected(self):
        with self.assertRaises(ValueError):
            replace(DECISION, rationale="")
        with self.assertRaises(ValueError):
            replace(self.context, anchor_digest="")

    def test_missing_decision_rejected(self):
        for item in (self.energy, self.model, self.model.constraints[0],
                     support(self.model, self.context)):
            with self.subTest(item=type(item).__name__), self.assertRaises(ValueError):
                replace(item, decision=None)

    def test_mutable_collections_rejected(self):
        with self.assertRaises(ValueError):
            replace(self.context, conditions=list(self.context.conditions))
        with self.assertRaises(ValueError):
            replace(self.model, constraints=list(self.model.constraints))
        with self.assertRaises(ValueError):
            replace(support(self.model, self.context), evidence=[])

    def test_assessment_rejects_untyped_judgment(self):
        with self.assertRaises(ValueError):
            replace(support(self.model, self.context), judgment="supports")


if __name__ == "__main__":
    unittest.main()
