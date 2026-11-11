"""Independent finite-generation Markov oracle and planted branching defects.

The oracle evolves a census distribution by summing independent offspring per
current individual. Production instead composes descendant PGFs with common
integer denominators. Neither diagnostic success nor model extinction is
physical evidence.
"""

import json
import unittest
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from unittest.mock import patch

from ..applicability.example import support
from ..applicability.mapping import ApplicabilityState, ConditionBasis, Domain
from ..detection.non_detection import NonDetectionObservation, record_non_detection
from ..detection.scoped_absence import AbsenceRejection, claim_absence
from ..equations.adapter import EquationRegistry, _calculate
from ..equations.branching import (
    MAX_GENERATIONS, MAX_INITIAL_POPULATION, MAX_OFFSPRING, MAX_POPULATION,
    MAX_TOTAL_WEIGHT, FiniteBranching, OffspringLaw,
)
from ..equations.branching_example import (
    DECISION, EVIDENCE, binary_law, deterministic_one, example_runs,
    fixture_experiment, fixture_model, fixture_plan,
)
from ..equations.branching_report import branching_report, generation_profile
from ..equations.percolation_example import (
    fixture_experiment as graph_experiment, fixture_model as graph_model,
    fixture_plan as graph_plan,
)
from ..equations.substitution import (
    ExperimentalDiagnostics, RunState, ValidationPlan, execute, substitute,
)
from ..failures import Axis, FailureRecord, Finding, Status
from ..gates.gate_results import GateOutcome
from ..gates.l0_closure import ValueProvenance, l0_closure_gate
from ..lifecycle.unknown_expiry import UnknownState
from .known_answer import InstrumentValidation, KnownAnswerCase
from .null_harness import NullCase, validate_nulls


def law(weights):
    return OffspringLaw(tuple(weights), DECISION, EVIDENCE)


def oracle_distribution(offspring, initial, generations):
    """Independent census-state Markov recursion using exact Fraction values."""
    denominator = sum(w for _, w in offspring.weights)
    offspring_pmf = {k: Fraction(w, denominator) for k, w in offspring.weights}
    census = {initial: Fraction(1)}
    for _ in range(generations):
        next_census = {}
        for parents, probability in census.items():
            children = {0: Fraction(1)}
            for _ in range(parents):
                updated = {}
                for total, a in children.items():
                    for count, b in offspring_pmf.items():
                        updated[total + count] = updated.get(total + count, Fraction(0)) + a * b
                children = updated
            for count, conditional in children.items():
                next_census[count] = next_census.get(count, Fraction(0)) + probability * conditional
        census = next_census
    return census


def oracle_values(offspring, initial, generations):
    pmf = oracle_distribution(offspring, initial, generations)
    denominator = sum(w for _, w in offspring.weights)
    mean = Fraction(sum(k * w for k, w in offspring.weights), denominator)
    offspring_var = sum(Fraction(w, denominator) * (k - mean) ** 2
                        for k, w in offspring.weights)
    expected = sum(k * p for k, p in pmf.items())
    variance = sum((k - expected) ** 2 * p for k, p in pmf.items())
    return dict(
        offspring_mean=float(mean), offspring_variance=float(offspring_var),
        expected_population=float(expected), population_variance=float(variance),
        extinction_by_horizon=float(pmf.get(0, 0)),
        survival_at_horizon=float(sum(p for k, p in pmf.items() if k > 0)),
        expected_cumulative_population=float(initial * sum(mean ** n for n in range(generations + 1))),
        probability_mass=1.0,
        **{f"population_probability_{k}": float(pmf.get(k, 0))
           for k in range(MAX_POPULATION + 1)},
    )


def oracle_plan(model, experiment, inputs=((1, 0), (1, 1))):
    cases = []
    for initial, generations in inputs:
        expected = oracle_values(model.law, initial, generations)
        cases.append(KnownAnswerCase.from_maps(
            f"oracle-{initial}-{generations}", {"initial": initial, "generations": generations},
            expected, {key: 1e-12 for key in expected},
            "Independent exact census-state oracle, not production PGF composition.",
        ))
    baseline = oracle_values(model.law, 0, 0)
    return ValidationPlan(
        "independent-branching-oracle", model.digest(), experiment.context.digest(), tuple(cases),
        (NullCase.from_maps("no-founders", {"initial": 0, "generations": 0}, baseline,
                            {key: 0 for key in baseline}),),
        tuple((p.name, p.unit) for p in model.inputs),
        tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
    )


def run_law(offspring, initial=1, generations=2):
    model = fixture_model(offspring)
    experiment = fixture_experiment(offspring, initial, generations)
    registry = EquationRegistry()
    registry.register(model)
    return execute(registry, model.equation_id, model.revision, experiment,
                   oracle_plan(model, experiment), DECISION)


class BranchingContractTests(unittest.TestCase):
    def test_law_and_adapter_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            binary_law().weights = ((0, 1),)
        with self.assertRaises(FrozenInstanceError):
            fixture_model().definition = "immigration"

    def test_invalid_weight_tables(self):
        for weights in ((), [(0, 1)], ([0, 1],), ((0, 1, 2),), ((0, 0),),
                        ((0, -1),), ((0, 0.5),), ((True, 1),), ((0, True),),
                        ((-1, 1),), ((MAX_OFFSPRING + 1, 1),), ((1, 1), (1, 2))):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                OffspringLaw(weights, DECISION, EVIDENCE)

    def test_weight_resource_bound(self):
        for weights in (((0, MAX_TOTAL_WEIGHT + 1),),
                        ((0, MAX_TOTAL_WEIGHT), (1, 1))):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                law(weights)

    def test_law_provenance_is_required(self):
        for changes in ({"decision": None}, {"evidence": ()}, {"evidence": ["ref"]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(binary_law(), **changes)

    def test_exact_law_and_metadata_are_content_bound(self):
        first = fixture_model()
        alternatives = (
            fixture_model(law(((0, 1), (2, 3)))),
            fixture_model(replace(binary_law(), weights=tuple(reversed(binary_law().weights)))),
            fixture_model(replace(binary_law(), decision=replace(DECISION, chosen_by="another-author"))),
            replace(first, revision="2"),
        )
        for other in alternatives:
            self.assertNotEqual(first.digest(), other.digest())
            self.assertNotEqual(first.description().digest(), other.description().digest())

    def test_engine_process_and_provenance_cannot_be_omitted(self):
        for changes in ({"engine": "callable"}, {"definition": "density-dependent"},
                        {"decision": None}, {"evidence": ()}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(fixture_model(), **changes)

    def test_law_definition_and_numeric_criteria_required(self):
        eq = fixture_model()
        for key in ("offspring_law", "branching_definition", "initial_population", "generation_horizon"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                replace(eq, constraints=tuple(c for c in eq.constraints if c.key != key))

    def test_scope_cannot_exceed_backend_limits_or_change_units(self):
        eq = fixture_model()
        for key, changes in (
            ("initial_population", {"upper": MAX_INITIAL_POPULATION + 1}),
            ("generation_horizon", {"upper": MAX_GENERATIONS + 1}),
            ("generation_horizon", {"unit": "seconds"}),
            ("initial_population", {"domain": Domain.ENVIRONMENT}),
        ):
            with self.subTest(key=key, changes=changes), self.assertRaises(ValueError):
                replace(eq, constraints=tuple(replace(c, **changes) if c.key == key else c
                                               for c in eq.constraints))

    def test_closed_registry_rejects_subclass_callbacks(self):
        class Forged(FiniteBranching):
            def digest(self):
                raise AssertionError("overridden code must never run")
        eq = fixture_model()
        forged = Forged(eq.equation_id, eq.revision, eq.law, eq.constraints, eq.decision, eq.evidence)
        registry = EquationRegistry()
        for item in (forged, lambda x: x, object()):
            with self.subTest(item=item), self.assertRaises(ValueError):
                registry.register(item)
        with self.assertRaises(ValueError):
            _calculate(forged, {"initial": 1, "generations": 1})

    def test_revision_registration_is_explicit_and_nonreplaceable(self):
        registry = EquationRegistry()
        registry.register(fixture_model())
        with self.assertRaises(ValueError):
            registry.register(fixture_model())
        with self.assertRaises(KeyError):
            registry.select("finite-lineage-branching", "latest")


class ExactBranchingTests(unittest.TestCase):
    def test_finite_distributions_against_independent_census_oracle(self):
        laws = (
            law(((0, 1),)), deterministic_one(), law(((2, 1),)),
            law(((0, 1), (1, 3))), binary_law(), law(((0, 1), (2, 3))),
            law(((0, 2), (1, 1), (3, 1))), law(((0, 1), (4, 1))),
        )
        for offspring in laws:
            with self.subTest(weights=offspring.weights):
                model = fixture_model(offspring)
                experiment = fixture_experiment(offspring, generations=1)
                registry = EquationRegistry()
                registry.register(model)
                inputs = tuple((initial, generations)
                               for initial in (0, 1, 2, 4) for generations in range(4)
                               if initial * offspring.max_offspring ** generations <= 32)
                run = execute(registry, model.equation_id, model.revision, experiment,
                              oracle_plan(model, experiment, inputs), DECISION)
                self.assertIs(run.state, RunState.COMPUTED)
                self.assertEqual(len(run.known_answer.cases_run), len(inputs))
                self.assertFalse(run.known_answer.cases_failed)
                self.assertIs(run.record.physical, Status.UNTESTED)

    def test_generation_zero_is_the_founder_cohort_not_extinction(self):
        for initial in range(MAX_INITIAL_POPULATION + 1):
            got = _calculate(fixture_model(), {"initial": initial, "generations": 0})
            self.assertEqual(got[f"population_probability_{initial}"], 1)
            self.assertEqual(got["expected_population"], initial)
            self.assertEqual(got["extinction_by_horizon"], float(initial == 0))
            self.assertEqual(got["expected_cumulative_population"], initial)

    def test_zero_founders_remain_zero_without_immigration(self):
        offspring = law(((4, MAX_TOTAL_WEIGHT),))
        run = run_law(offspring, initial=0, generations=MAX_GENERATIONS)
        self.assertIs(run.state, RunState.COMPUTED)
        values = {v.name: v.value for v in run.outputs}
        self.assertEqual(values["population_probability_0"], 1)
        self.assertEqual(values["expected_population"], 0)
        self.assertEqual(values["expected_cumulative_population"], 0)

    def test_deterministic_die_off_and_deterministic_reproduction(self):
        for count in (0, 1, 2, 3, 4):
            offspring = law(((count, 1),))
            initial, generations = 2, 2
            got = _calculate(fixture_model(offspring), {"initial": initial, "generations": generations})
            expected = initial * count ** generations
            self.assertEqual(got[f"population_probability_{expected}"], 1)
            self.assertEqual(got["expected_population"], expected)
            self.assertEqual(got["population_variance"], 0)
            self.assertEqual(got["extinction_by_horizon"], float(count == 0))

    def test_binary_two_generation_hand_answer(self):
        got = _calculate(fixture_model(), {"initial": 1, "generations": 2})
        self.assertEqual(got["population_probability_0"], 5 / 8)
        self.assertEqual(got["population_probability_2"], 1 / 4)
        self.assertEqual(got["population_probability_4"], 1 / 8)
        self.assertEqual(got["population_variance"], 2)
        self.assertEqual(got["expected_cumulative_population"], 3)

    def test_independent_founders_are_not_one_shared_draw(self):
        got = _calculate(fixture_model(), {"initial": 2, "generations": 1})
        self.assertEqual(got["population_probability_0"], 1 / 4)
        self.assertEqual(got["population_probability_2"], 1 / 2)
        self.assertEqual(got["population_probability_4"], 1 / 4)

    def test_mean_one_does_not_determine_extinction_or_permanent_organization(self):
        stochastic = run_law(binary_law(), generations=3)
        deterministic = run_law(deterministic_one(), generations=3)
        a, b = branching_report(stochastic), branching_report(deterministic)
        self.assertEqual(a["conditional_ensemble_metrics"]["expected_population"], 1)
        self.assertEqual(b["conditional_ensemble_metrics"]["expected_population"], 1)
        self.assertGreater(a["conditional_ensemble_metrics"]["extinction_by_horizon"], 0)
        self.assertEqual(b["conditional_ensemble_metrics"]["extinction_by_horizon"], 0)
        self.assertNotIn("permanent_organization", a)
        self.assertIs(stochastic.applicability.state, ApplicabilityState.UNKNOWN)

    def test_mean_above_one_still_has_positive_finite_extinction_probability(self):
        got = _calculate(fixture_model(law(((0, 1), (2, 3)))), {"initial": 1, "generations": 2})
        self.assertEqual(got["offspring_mean"], 1.5)
        self.assertEqual(got["extinction_by_horizon"], 19 / 64)
        self.assertEqual(got["expected_population"], 2.25)

    def test_moment_recursion_and_extinction_recursion_independently_agree(self):
        offspring = law(((0, 2), (1, 1), (3, 1)))
        total = sum(w for _, w in offspring.weights)
        mean = Fraction(sum(k * w for k, w in offspring.weights), total)
        sigma = sum(Fraction(w, total) * (k - mean) ** 2 for k, w in offspring.weights)
        expected, variance, q = Fraction(1), Fraction(0), Fraction(0)
        for generations in range(4):
            got = _calculate(fixture_model(offspring), {"initial": 1, "generations": generations})
            self.assertAlmostEqual(got["expected_population"], float(expected))
            self.assertAlmostEqual(got["population_variance"], float(variance))
            self.assertAlmostEqual(got["extinction_by_horizon"], float(q))
            variance, expected = mean ** 2 * variance + sigma * expected, mean * expected
            q = sum(Fraction(w, total) * q ** k for k, w in offspring.weights)

    def test_complete_support_reaches_declared_population_bound(self):
        run = run_law(binary_law(), generations=7)
        self.assertIs(run.state, RunState.COMPUTED)
        values = {v.name: v.value for v in run.outputs}
        self.assertGreater(values[f"population_probability_{MAX_POPULATION}"], 0)
        self.assertEqual(values["probability_mass"], 1)
        self.assertEqual(values["expected_population"], 1)
        self.assertEqual(values["population_variance"], 7)
        self.assertEqual(values["expected_cumulative_population"], 8)

    def test_rare_survival_is_not_cancelled_by_one_minus_rounded_extinction(self):
        offspring = law(((0, MAX_TOTAL_WEIGHT - 1), (1, 1)))
        run = run_law(offspring, generations=MAX_GENERATIONS)
        self.assertIs(run.state, RunState.COMPUTED)
        values = {v.name: v.value for v in run.outputs}
        self.assertEqual(values["extinction_by_horizon"], 1.0)  # rounded float
        self.assertGreater(values["survival_at_horizon"], 0)
        self.assertAlmostEqual(values["survival_at_horizon"] / 1e-48, 1)
        self.assertEqual(values["survival_at_horizon"], values["population_probability_1"])

    def test_positive_probability_underflow_is_instrument_error_not_zero(self):
        offspring = law(((0, MAX_TOTAL_WEIGHT - 1), (2, 1)))
        run = run_law(offspring, generations=7)
        self.assertIs(run.state, RunState.ERROR)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)
        self.assertEqual(run.outputs, ())
        self.assertIn("underflow", run.record.findings[-1].message)

    def test_selected_weights_are_exact_ratios_not_observed_sample_counts(self):
        a = _calculate(fixture_model(law(((0, 1), (2, 1)))), {"initial": 1, "generations": 2})
        b = _calculate(fixture_model(law(((0, 2), (2, 2)))), {"initial": 1, "generations": 2})
        self.assertEqual(a, b)
        self.assertNotEqual(law(((0, 1), (2, 1))).digest(), law(((0, 2), (2, 2))).digest())

    def test_private_primitive_still_rejects_invalid_numeric_domains(self):
        for inputs in ({"initial": True, "generations": 0}, {"initial": 1, "generations": 0.5},
                       {"initial": 1, "generations": float("nan")},
                       {"initial": 1, "generations": 8}, {"initial": -1, "generations": 1},
                       {"initial": 1}, {"initial": 1, "generations": 0, "override": 1}):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                _calculate(fixture_model(), inputs)

    def test_law_order_changes_binding_not_numerical_predictions(self):
        other = replace(binary_law(), weights=tuple(reversed(binary_law().weights)))
        a = _calculate(fixture_model(), {"initial": 2, "generations": 3})
        b = _calculate(fixture_model(other), {"initial": 2, "generations": 3})
        self.assertEqual(a, b)
        self.assertNotEqual(binary_law().digest(), other.digest())


class BranchingGateTests(unittest.TestCase):
    def setUp(self):
        self.eq = fixture_model()
        self.exp = fixture_experiment()
        self.plan = fixture_plan(self.eq, self.exp)
        self.registry = EquationRegistry()
        self.registry.register(self.eq)

    def run_model(self, exp=None, eq=None, plan=None, **kwargs):
        eq, exp = eq or self.eq, exp or self.exp
        return execute(self.registry, eq.equation_id, eq.revision, exp,
                       plan or fixture_plan(eq, exp), DECISION, **kwargs)

    def change_context(self, key, **changes):
        context = replace(self.exp.context, conditions=tuple(
            replace(c, **changes) if c.key == key else c for c in self.exp.context.conditions
        ))
        return replace(self.exp, context=context,
                       boundary=replace(self.exp.boundary, context_digest=context.digest()))

    def no_evaluation(self, **kwargs):
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calc:
            run = self.run_model(**kwargs)
            calc.assert_not_called()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertEqual(run.outputs, ())
        return run

    def test_full_gate_order_and_no_physical_promotion(self):
        run = self.run_model()
        self.assertEqual(run.stages, (
            "protocol-binding:pass", "l0:pass", "applicability:candidate-domain",
            "validation-plan:pass", "known-answer:pass", "null:pass", "calculation:computed",
        ))
        self.assertIs(run.state, RunState.COMPUTED)
        self.assertIs(run.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertIs(run.record.physical, Status.UNTESTED)
        self.assertIs(run.record.instrument, Status.OK)
        self.assertTrue(all(v.uncertainty is None for v in run.outputs))

    def test_incomplete_ledger_cannot_be_replaced_by_branching_math(self):
        boundary = replace(self.exp.boundary, accounting=replace(
            self.exp.boundary.accounting, declared_complete=False,
        ))
        self.assertIs(self.no_evaluation(exp=replace(self.exp, boundary=boundary)).record.determination,
                      Status.FAILED)

    def test_l0_error_on_an_additional_quantity_blocks_before_branching(self):
        # Cohort matching itself is a determination guard. A separate modeled
        # physical ledger quantity still follows the existing L0 failure axis.
        from ..gates.l0_closure import QuantityAccount
        anchor = replace(self.exp.anchor, quantities=self.exp.anchor.quantities + (("toy_energy", 1.0),))
        context = replace(self.exp.context, anchor_digest=anchor.digest())
        accounting = replace(self.exp.boundary.accounting, accounts=(
            *self.exp.boundary.accounting.accounts,
            QuantityAccount("toy_energy", 1, 2, ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
                            self.exp.boundary.accounting.accounts[0].exchanges, 0),
        ))
        # Each new quantity needs its own correctly assigned intervention entries.
        accounting = replace(accounting, accounts=(
            accounting.accounts[0],
            replace(accounting.accounts[1], exchanges=tuple(
                replace(e, quantity="toy_energy") for e in accounting.accounts[1].exchanges
            )),
        ))
        boundary = replace(self.exp.boundary, context_digest=context.digest(), anchor_digest=anchor.digest(),
                           accounting=accounting, quantity_units=(("founder_count", "1"), ("toy_energy", "toy-unit")))
        exp = replace(self.exp, anchor=anchor, context=context, boundary=boundary)
        run = self.no_evaluation(exp=exp)
        self.assertIs(run.record.physical, Status.FAILED)

    def test_frozen_cohort_cannot_be_replaced_by_another_anchor(self):
        self.no_evaluation(exp=replace(self.exp, anchor=replace(self.exp.anchor, label="another")))

    def test_selected_initial_population_must_match_anchored_cohort(self):
        run = self.no_evaluation(exp=self.change_context("initial_population", value=2))
        self.assertIs(run.record.determination, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_missing_cohort_ledger_cannot_be_replaced_by_unrelated_accounting(self):
        account = self.exp.boundary.accounting.accounts[0]
        other = replace(account, quantity="unrelated_quantity", exchanges=tuple(
            replace(e, quantity="unrelated_quantity") for e in account.exchanges
        ))
        anchor = replace(self.exp.anchor, quantities=(("unrelated_quantity", 1.0),))
        context = replace(self.exp.context, anchor_digest=anchor.digest())
        accounting = replace(self.exp.boundary.accounting, accounts=(other,))
        boundary = replace(self.exp.boundary, context_digest=context.digest(), anchor_digest=anchor.digest(),
                           accounting=accounting, quantity_units=(("unrelated_quantity", "1"),))
        self.assertIs(l0_closure_gate(accounting).outcome, GateOutcome.PASS)
        run = self.no_evaluation(exp=replace(self.exp, anchor=anchor, context=context, boundary=boundary))
        self.assertIs(run.record.determination, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_founder_quantity_unit_is_not_an_unchecked_label(self):
        boundary = replace(self.exp.boundary, quantity_units=(("founder_count", "unrelated-unit"),))
        run = self.no_evaluation(exp=replace(self.exp, boundary=boundary))
        self.assertIs(run.record.determination, Status.FAILED)

    def test_balanced_founder_exchange_is_not_no_immigration(self):
        accounting = self.exp.boundary.accounting
        account = accounting.accounts[0]
        exchanges = tuple(replace(e, magnitude=1) if i in (0, 2) else e
                          for i, e in enumerate(account.exchanges))
        accounting = replace(accounting, accounts=(replace(account, exchanges=exchanges),))
        self.assertIs(l0_closure_gate(accounting).outcome, GateOutcome.PASS)
        run = self.no_evaluation(exp=replace(self.exp, boundary=replace(
            self.exp.boundary, accounting=accounting,
        )))
        self.assertIs(run.record.determination, Status.FAILED)

    def test_foreign_protocol_binding_is_rejected(self):
        self.no_evaluation(exp=replace(self.exp, boundary=replace(self.exp.boundary, context_digest="old")))

    def test_wrong_law_or_process_definition_is_not_a_physical_refutation(self):
        for key, value in (("offspring_law", "another-law"),
                           ("branching_definition", "immigration-or-correlated-process")):
            with self.subTest(key=key):
                run = self.no_evaluation(exp=self.change_context(key, value=value))
                self.assertIs(run.applicability.state, ApplicabilityState.OUTSIDE)
                self.assertIs(run.record.physical, Status.UNTESTED)

    def test_discrete_inputs_cannot_be_fractional_uncertain_or_assumed(self):
        for key in ("initial_population", "generation_horizon"):
            for changes in ({"value": 0.5}, {"uncertainty": 0.1},
                            {"uncertainty": None}, {"basis": ConditionBasis.ASSUMED}):
                with self.subTest(key=key, changes=changes):
                    self.no_evaluation(exp=self.change_context(key, **changes))

    def test_horizon_domain_and_complete_support_bound_are_checked_before_any_case(self):
        for horizon in (-1, MAX_GENERATIONS + 1, 8):
            with self.subTest(horizon=horizon):
                run = self.no_evaluation(exp=self.change_context("generation_horizon", value=horizon))
                self.assertIs(run.record.physical, Status.UNTESTED)

    def test_invalid_late_harness_input_prevents_all_evaluation(self):
        for inputs in (
            (("initial", 0.5), ("generations", 1)),
            (("initial", 1), ("generations", 8)),  # complete support would exceed bound
            (("initial", 1), ("generations", MAX_GENERATIONS + 1)),
        ):
            bad = replace(self.plan.known_answers[-1], inputs=inputs)
            plan = replace(self.plan, known_answers=self.plan.known_answers[:-1] + (bad,))
            with self.subTest(inputs=inputs):
                run = self.no_evaluation(plan=plan)
                self.assertIs(run.record.determination, Status.FAILED)
                self.assertIs(run.record.instrument, Status.UNTESTED)

    def test_missing_output_contract_and_foreign_plan_block(self):
        case = replace(self.plan.known_answers[0],
                       expected=(("expected_population", 1),), tolerances=(("expected_population", 0),))
        for plan in (replace(self.plan, known_answers=(case,)),
                     replace(self.plan, equation_digest="old"), replace(self.plan, context_digest="old")):
            with self.subTest(plan=plan.plan_id):
                self.no_evaluation(plan=plan)

    def test_empty_harnesses_do_not_validate(self):
        for changes in ({"known_answers": ()}, {"nulls": ()}):
            with self.subTest(changes=changes):
                run = self.run_model(plan=replace(self.plan, **changes))
                self.assertIs(run.state, RunState.BLOCKED)
                self.assertEqual(run.outputs, ())

    def test_bad_known_answer_stops_before_null_and_nominal(self):
        case = self.plan.known_answers[0]
        case = replace(case, expected=tuple((k, 1 if k == "extinction_by_horizon" else v)
                                            for k, v in case.expected))
        with patch("playground.equations.substitution.validate_nulls", wraps=validate_nulls) as nulls:
            run = self.run_model(plan=replace(self.plan, known_answers=(case,)))
            self.assertIs(run.state, RunState.BLOCKED)
            nulls.assert_not_called()
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_planted_generation_zero_extinction_is_instrument_failure(self):
        from ..equations.branching import _calculate_branching

        def wrong_zero(eq, inputs):
            result = _calculate_branching(eq, inputs)
            if inputs["generations"] == 0:
                result["extinction_by_horizon"] = 1.0
            return result

        with patch("playground.equations.branching._calculate_branching", side_effect=wrong_zero):
            run = self.run_model()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_lost_mass_is_not_silently_renormalized(self):
        with patch("playground.equations.branching._population_distribution", return_value=([1, 1], 3)):
            run = self.run_model()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_negative_invalid_or_oversized_exact_distribution_is_instrument_failure(self):
        for output in (([2, -1], 1), ([1], 0), ([True], 1), ([], 1),
                       ([0] * (MAX_POPULATION + 1) + [1], 1)):
            with self.subTest(output=output), patch(
                "playground.equations.branching._population_distribution", return_value=output,
            ):
                run = self.run_model()
            self.assertIs(run.state, RunState.BLOCKED)
            self.assertIs(run.record.instrument, Status.FAILED)
            self.assertIs(run.record.physical, Status.UNTESTED)

    def test_summed_survival_catches_subtraction_cancellation_mutant(self):
        offspring = law(((0, MAX_TOTAL_WEIGHT - 1), (1, 1)))
        model = fixture_model(offspring, revision="rare-survival-test")
        experiment = fixture_experiment(offspring, generations=MAX_GENERATIONS)
        self.registry.register(model)
        plan = oracle_plan(model, experiment, inputs=((1, MAX_GENERATIONS),))
        case = plan.known_answers[0]
        # Tiny values require an explicit detecting tolerance, not 1e-12.
        case = replace(case, tolerances=tuple((k, 0) for k, _ in case.tolerances))
        plan = replace(plan, known_answers=(case,))
        from ..equations.branching import _calculate_branching

        def subtract_survival(eq, inputs):
            result = _calculate_branching(eq, inputs)
            result["survival_at_horizon"] = 1 - result["extinction_by_horizon"]
            return result

        with patch("playground.equations.branching._calculate_branching", side_effect=subtract_survival):
            run = self.run_model(eq=model, exp=experiment, plan=plan)
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)

    def test_null_invents_descendants_and_blocks_before_nominal(self):
        from ..equations.branching import _calculate_branching

        def invented(eq, inputs):
            result = _calculate_branching(eq, inputs)
            if inputs["initial"] == 0:
                result["expected_population"] = 1.0
            return result

        with patch("playground.equations.branching._calculate_branching", side_effect=invented) as calc:
            run = self.run_model()
            self.assertEqual(calc.call_count, len(self.plan.known_answers) + 1)
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertTrue(run.known_answer.validated_within_tested_cases)
        self.assertIs(run.record.instrument, Status.FAILED)

    def test_nominal_crash_nonfinite_missing_or_extra_outputs_are_instrument_failures(self):
        from ..equations.branching import _calculate_branching

        for defect in ("crash", "nan", "missing", "extra"):
            def corrupt(eq, inputs):
                if inputs["generations"] == 3:
                    if defect == "crash":
                        raise RuntimeError("planted nominal error")
                    result = _calculate_branching(eq, inputs)
                    if defect == "nan":
                        result["expected_population"] = float("nan")
                    elif defect == "missing":
                        result.pop("expected_population")
                    else:
                        result["unregistered_metric"] = 0
                    return result
                return _calculate_branching(eq, inputs)

            exp = fixture_experiment(generations=3)
            with self.subTest(defect=defect), patch(
                "playground.equations.branching._calculate_branching", side_effect=corrupt,
            ):
                run = self.run_model(exp=exp)
            self.assertIs(run.state, RunState.ERROR)
            self.assertIs(run.record.instrument, Status.FAILED)
            self.assertIs(run.record.physical, Status.UNTESTED)
            self.assertEqual(run.outputs, ())

    def test_unresolved_assumptions_and_unknown_dependencies_block(self):
        for changes, states in (
            ({"assumptions": ("offspring correlation untested",)}, {}),
            ({"unknown_dependencies": ("offspring-survey",)}, {}),
            ({"unknown_dependencies": ("offspring-survey",)}, {"offspring-survey": UnknownState.UNKNOWN}),
            ({"unknown_dependencies": ("offspring-survey",)}, {"offspring-survey": UnknownState.EXPIRED}),
        ):
            eq = replace(self.eq, revision=str(changes) + str(states), **changes)
            self.registry.register(eq)
            with self.subTest(changes=changes, states=states):
                self.no_evaluation(eq=eq, dependency_states=states)

    def test_substitution_retests_and_cannot_inherit_physical_support(self):
        first = self.run_model(assessments=(support(self.eq.description(), self.exp.context),))
        new = replace(self.eq, revision="2")
        self.registry.register(new)
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calc:
            second = substitute(first, self.registry, new.equation_id, new.revision,
                                fixture_plan(new, self.exp), DECISION)
            self.assertEqual(calc.call_count, len(self.plan.known_answers) + len(self.plan.nulls) + 1)
        self.assertEqual(second.parent_run_digest, first.digest())
        self.assertIs(first.applicability.state, ApplicabilityState.SUPPORTED)
        self.assertIs(second.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertEqual(second.supplied_assessments, ())

    def test_observer_and_design_failures_stay_with_replacement(self):
        new = replace(self.eq, revision="2")
        self.registry.register(new)
        for axis in (Axis.INSTRUMENT, Axis.DETERMINATION):
            record = FailureRecord((Finding(axis, Status.FAILED, "PLANTED", "experimental failure",
                                            "validation.test_branching"),))
            exp = replace(self.exp, diagnostics=(ExperimentalDiagnostics(
                self.exp.context.digest(), record, DECISION, EVIDENCE,
            ),))
            first = self.run_model(exp=exp)
            with patch("playground.equations.substitution._calculate") as calc:
                second = substitute(first, self.registry, new.equation_id, new.revision,
                                    fixture_plan(new, exp), DECISION)
                calc.assert_not_called()
            self.assertIs(second.state, RunState.BLOCKED)
            self.assertIs(second.record.status_for(axis), Status.FAILED)

    def test_different_law_needs_revised_determination_not_inherited_evidence(self):
        first = self.run_model(assessments=(support(self.eq.description(), self.exp.context),))
        new = fixture_model(deterministic_one(), revision="2")
        self.registry.register(new)
        with patch("playground.equations.substitution._calculate") as calc:
            second = substitute(first, self.registry, new.equation_id, new.revision,
                                fixture_plan(new, self.exp), DECISION, first.supplied_assessments)
            calc.assert_not_called()
        self.assertIs(second.state, RunState.BLOCKED)
        self.assertIs(second.applicability.state, ApplicabilityState.OUTSIDE)
        self.assertEqual(second.applicability.assessments, ())

    def test_percolation_is_not_a_branching_fallback_or_universal_hierarchy(self):
        other = graph_model()
        self.registry.register(other)
        graph_exp = graph_experiment()
        graph_run = execute(self.registry, other.equation_id, other.revision, graph_exp,
                            graph_plan(other, graph_exp), DECISION)
        self.assertIs(graph_run.state, RunState.COMPUTED)
        branching_run = self.run_model()
        with patch("playground.equations.substitution._calculate") as calc:
            branching_on_graph = substitute(graph_run, self.registry, self.eq.equation_id, self.eq.revision,
                                           fixture_plan(self.eq, graph_exp), DECISION)
            graph_on_branching = substitute(branching_run, self.registry, other.equation_id, other.revision,
                                           graph_plan(other, self.exp), DECISION)
            calc.assert_not_called()
        self.assertIs(branching_on_graph.state, RunState.BLOCKED)
        self.assertIs(graph_on_branching.state, RunState.BLOCKED)

    def test_model_extinction_does_not_qualify_physical_absence(self):
        offspring = law(((0, 1),))
        run = run_law(offspring, generations=2)
        self.assertEqual(branching_report(run)["conditional_ensemble_metrics"]["extinction_by_horizon"], 1)
        observation = NonDetectionObservation.from_map(
            "no-observed-descendants", {"law_digest": offspring.digest()}, effect_size_of_interest=1,
        )
        rejection = claim_absence("physical-extinction", record_non_detection(observation, None))
        self.assertIsInstance(rejection, AbsenceRejection)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_json_audit_contains_law_context_plan_and_unknown_uncertainty(self):
        run = self.run_model()
        data = json.loads(run.to_json())
        self.assertEqual(data["equation"]["law"]["weights"], [[0, 1], [2, 1]])
        self.assertEqual(data["equation_digest"], self.eq.digest())
        self.assertEqual(data["context_digest"], self.exp.context.digest())
        self.assertEqual(data["plan_digest"], self.plan.digest())
        self.assertTrue(all(output["uncertainty"] is None for output in data["outputs"]))


class BranchingProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = example_runs()

    def test_report_and_profile_do_not_recalculate(self):
        with patch("playground.equations.branching._calculate_branching") as calc:
            report = branching_report(self.runs[2])
            profile = generation_profile(self.runs, DECISION)
            calc.assert_not_called()
        self.assertEqual(report["conditional_ensemble_metrics"]["extinction_by_horizon"], 5 / 8)
        self.assertEqual(report["offspring_mean_relation_to_one"], "equal-to-one")
        self.assertEqual(report["run_digest"], self.runs[2].digest())
        self.assertEqual(len(profile["points"]), 6)
        self.assertIsNone(report["output_uncertainty"])

    def test_only_consecutive_increasing_horizons_are_a_profile(self):
        for runs in (self.runs[:1], (self.runs[0], self.runs[2]),
                     tuple(reversed(self.runs)), (self.runs[0], self.runs[0])):
            with self.subTest(horizons=[dict(r.inputs)["generations"] for r in runs]), self.assertRaises(ValueError):
                generation_profile(runs, DECISION)

    def test_blocked_runs_cannot_be_reported(self):
        bad = replace(self.runs[1], state=RunState.BLOCKED, outputs=())
        with self.assertRaises(ValueError):
            branching_report(bad)
        with self.assertRaises(ValueError):
            generation_profile((self.runs[0], bad), DECISION)

    def test_profile_selection_provenance_required(self):
        with self.assertRaises(ValueError):
            generation_profile(self.runs, None)

    def test_other_context_changes_do_not_become_generation_dynamics(self):
        for key, value in (("observer", "another"), ("environment", "another"),
                           ("initial_population", 2)):
            last = self.runs[-1]
            context = replace(last.experiment.context, conditions=tuple(
                replace(c, value=value) if c.key == key else c
                for c in last.experiment.context.conditions
            ))
            changed = replace(last, experiment=replace(last.experiment, context=context))
            with self.subTest(key=key), self.assertRaises(ValueError):
                generation_profile(self.runs[:-1] + (changed,), DECISION)

    def test_profile_cannot_mix_laws_revisions_or_dependency_states(self):
        for changed in (
            replace(self.runs[-1], equation=replace(self.runs[-1].equation, revision="2")),
            example_runs(deterministic_one())[-1],
            replace(self.runs[-1], dependency_states=(("different-dependency", "resolved"),)),
        ):
            with self.subTest(changed=changed.equation.revision), self.assertRaises(ValueError):
                generation_profile(self.runs[:-1] + (changed,), DECISION)

    def test_finite_profile_has_no_infinite_survival_or_organization_claim(self):
        profile = generation_profile(self.runs, DECISION)
        self.assertNotIn("infinite_survival_probability", profile)
        self.assertNotIn("critical_threshold", profile)
        self.assertNotIn("continuity", profile)
        values = [p["conditional_ensemble_metrics"] for p in profile["points"]]
        self.assertTrue(all(p["expected_population"] == 1 for p in values))
        self.assertTrue(all(a["extinction_by_horizon"] < b["extinction_by_horizon"]
                            for a, b in zip(values, values[1:])))
        self.assertTrue(all(r.applicability.state is ApplicabilityState.UNKNOWN for r in self.runs))


class BranchingMutationProbeTests(unittest.TestCase):
    def test_known_answer_guard_detects_forged_pass_by_assertion(self):
        forged = InstrumentValidation("forged", FailureRecord(), ("forged-case",), ())
        result = unittest.TestResult()
        case = BranchingGateTests("test_bad_known_answer_stops_before_null_and_nominal")
        with patch("playground.equations.substitution.validate_known_answers", return_value=forged):
            case.run(result)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 1)


if __name__ == "__main__":
    unittest.main()
