"""Independent exact oracles, design guards, and planted finite-bond defects.

Expected graph results use transitive closure and Fraction arithmetic, not the
production union-find implementation or its ensemble routine. Hand-stated
chain/cycle polynomials provide a second check on the enumerating oracle.
These are mathematical tests, never empirical validation.
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
from ..equations.adapter import Equation, EquationRegistry, _calculate
from ..equations.percolation import (
    BondPercolation, FiniteGraph, MAX_EDGES, MAX_NODES, OCCUPATION_LAW,
)
from ..equations.percolation_example import (
    DECISION, EVIDENCE, example_runs, fixture_experiment, fixture_model,
    fixture_plan, line_expectation, line_graph,
)
from ..equations.percolation_report import finite_transition_bracket, percolation_report
from ..equations.substitution import (
    ExperimentalDiagnostics, RunState, ValidationPlan, execute, substitute,
)
from ..failures import Axis, FailureRecord, Finding, Status
from ..lifecycle.unknown_expiry import UnknownState
from .known_answer import InstrumentValidation, KnownAnswerCase
from .null_harness import NullCase, validate_nulls


def graph(nodes, edges, sources=None, targets=None):
    return FiniteGraph(tuple(nodes), tuple(edges), tuple(sources or (nodes[0],)),
                       tuple(targets or (nodes[-1],)), DECISION, EVIDENCE)


def oracle_partition(g, mask):
    """Independent Floyd-Warshall reachability, including isolated vertices."""
    n = len(g.nodes)
    reach = [[i == j for j in range(n)] for i in range(n)]
    for bit, (a, b) in enumerate(g.edges):
        if mask & (1 << bit):
            i, j = g.nodes.index(a), g.nodes.index(b)
            reach[i][j] = reach[j][i] = True
    for k in range(n):
        for i in range(n):
            for j in range(n):
                reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])
    labels = [next(j for j in range(n) if reach[i][j]) for i in range(n)]
    groups = tuple(tuple(i for i, label in enumerate(labels) if label == root)
                   for root in sorted(set(labels)))
    spans = any(reach[g.nodes.index(a)][g.nodes.index(b)]
                for a in g.sources for b in g.targets)
    return groups, spans, labels


def oracle_values(g, mask, p):
    groups, spans, labels = oracle_partition(g, mask)
    p = Fraction(str(p))
    m = len(g.edges)
    probability = count = largest = Fraction(0)
    for state in range(1 << m):
        partition, spanning, _ = oracle_partition(g, state)
        occupied = state.bit_count()
        weight = p ** occupied * (1 - p) ** (m - occupied)
        probability += weight * spanning
        count += weight * len(partition)
        largest += weight * max(map(len, partition))
    return dict(
        spanning=float(spans), component_count=len(groups),
        largest_component_size=max(map(len, groups)), occupied_edge_count=mask.bit_count(),
        spanning_probability=float(probability), expected_component_count=float(count),
        expected_largest_component_size=float(largest),
        **{f"component_{i}": label for i, label in enumerate(labels)},
    )


def oracle_plan(model, experiment, exhaustive=False):
    """Test-only independent mathematical criteria, bound to this exact graph."""
    masks = range(1 << len(model.graph.edges)) if exhaustive else sorted({
        0, (1 << len(model.graph.edges)) - 1,
    })
    cases = []
    for mask in masks:
        for p in (0.0, 0.5, 1.0):
            expected = oracle_values(model.graph, mask, p)
            cases.append(KnownAnswerCase.from_maps(
                f"oracle-mask-{mask}-p-{p}", {"p": p, "mask": mask}, expected,
                {key: 1e-12 for key in expected}, "Independent transitive closure and exact rational sum.",
            ))
    null = oracle_values(model.graph, 0, 0)
    return ValidationPlan(
        "independent-test-oracle", model.digest(), experiment.context.digest(), tuple(cases),
        (NullCase.from_maps("empty-mask", {"p": 0, "mask": 0}, null,
                            {key: 0 for key in null}),),
        tuple((p.name, p.unit) for p in model.inputs),
        tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
    )


class GraphContractTests(unittest.TestCase):
    def test_graph_and_model_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            line_graph().nodes = ("x", "y")
        with self.assertRaises(FrozenInstanceError):
            fixture_model().engine = "unverified"

    def test_invalid_node_sets(self):
        for nodes in (["a", "b"], ("a",), ("a", "a"), ("a", ""),
                      tuple(str(i) for i in range(MAX_NODES + 1))):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                FiniteGraph(nodes, (), ("a",), ("b",), DECISION, EVIDENCE)

    def test_invalid_edges(self):
        for edges in ([("a", "b")], (["a", "b"],), (("a", "a"),),
                      (("a", "z"),), (("a", "b", "c"),),
                      (("a", "b"), ("b", "a")), (("a", "b"), ("a", "b"))):
            with self.subTest(edges=edges), self.assertRaises(ValueError):
                replace(line_graph(), edges=edges)

    def test_edge_enumeration_bound(self):
        nodes = tuple(str(i) for i in range(MAX_EDGES + 2))
        with self.assertRaises(ValueError):
            graph(nodes, tuple(zip(nodes, nodes[1:])))

    def test_invalid_boundary_subsets(self):
        for changes in ({"sources": ()}, {"targets": ()}, {"targets": ("a",)},
                        {"sources": ("z",)}, {"sources": ("a", "a")},
                        {"targets": ["c"]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(line_graph(), **changes)

    def test_graph_selection_provenance_required(self):
        for changes in ({"decision": None}, {"evidence": ()}, {"evidence": ["ref"]}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(line_graph(), **changes)

    def test_engine_and_occupation_law_cannot_be_swapped(self):
        for changes in ({"engine": "python-callback"}, {"occupation_law": "correlated"},
                        {"decision": None}, {"evidence": ()}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                replace(fixture_model(), **changes)

    def test_graph_law_and_numeric_scope_are_required(self):
        eq = fixture_model()
        for key in ("graph", "occupation_law", "bond_probability", "occupation_mask"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                replace(eq, constraints=tuple(c for c in eq.constraints if c.key != key))

    def test_numeric_scope_cannot_exceed_backend_domain(self):
        eq = fixture_model()
        for key, changes in (("bond_probability", {"upper": 2}),
                             ("occupation_mask", {"upper": 4}),
                             ("occupation_mask", {"unit": "bits"}),
                             ("bond_probability", {"domain": Domain.ENVIRONMENT})):
            with self.subTest(key=key, changes=changes), self.assertRaises(ValueError):
                replace(eq, constraints=tuple(replace(c, **changes) if c.key == key else c
                                               for c in eq.constraints))

    def test_graph_content_and_order_are_bound(self):
        first = line_graph()
        variants = (
            replace(first, edges=tuple(reversed(first.edges))),
            replace(first, nodes=tuple(reversed(first.nodes))),
            replace(first, targets=("b",)),
            replace(first, decision=replace(DECISION, chosen_by="different-selector")),
        )
        for other in variants:
            with self.subTest(other=other):
                self.assertNotEqual(first.digest(), other.digest())
                self.assertNotEqual(fixture_model(first).digest(), fixture_model(other).digest())
                self.assertNotEqual(fixture_model(first).description().digest(),
                                    fixture_model(other).description().digest())

    def test_closed_registry_rejects_callable_plugins_and_subclasses(self):
        class ForgedBond(BondPercolation):
            def digest(self):
                raise AssertionError("untrusted override must never be called")

        class ForgedArithmetic(Equation):
            pass

        eq = fixture_model()
        forged = ForgedBond(eq.equation_id, eq.revision, eq.graph, eq.constraints,
                            eq.decision, eq.evidence)
        registry = EquationRegistry()
        for adapter in (lambda x: x, object(), forged, ForgedArithmetic):
            with self.subTest(adapter=adapter), self.assertRaises(ValueError):
                registry.register(adapter)
        with self.assertRaises(ValueError):
            _calculate(forged, {"p": 0.5, "mask": 3})

    def test_revision_selection_is_explicit(self):
        registry = EquationRegistry()
        registry.register(fixture_model())
        with self.assertRaises(ValueError):
            registry.register(fixture_model())
        with self.assertRaises(KeyError):
            registry.select("finite-bond-connectivity", "latest")


class ExactFiniteGraphTests(unittest.TestCase):
    def test_declared_maximum_size_runs_through_all_gates(self):
        nodes = tuple(str(i) for i in range(MAX_NODES))
        g = graph(nodes, tuple(zip(nodes[:MAX_EDGES], nodes[1:MAX_EDGES + 1])),
                  sources=("0",), targets=(str(MAX_EDGES),))
        model = fixture_model(g)
        full = (1 << MAX_EDGES) - 1
        experiment = fixture_experiment(g, p=1, mask=full)
        registry = EquationRegistry()
        registry.register(model)
        # Hand-stated partitions: empty graph vs a 13-node path + 19 isolates.
        cases = []
        for p, mask in ((0, 0), (1, full)):
            count = MAX_NODES - (MAX_EDGES if mask else 0)
            largest = MAX_EDGES + 1 if mask else 1
            expected = dict(
                spanning=p, component_count=count, largest_component_size=largest,
                occupied_edge_count=MAX_EDGES if mask else 0, spanning_probability=p,
                expected_component_count=count, expected_largest_component_size=largest,
                **{f"component_{i}": 0 if mask and i <= MAX_EDGES else i
                   for i in range(MAX_NODES)},
            )
            cases.append(KnownAnswerCase.from_maps(
                f"maximum-size-{p}", {"p": p, "mask": mask}, expected,
                {name: 0 for name in expected},
            ))
        plan = ValidationPlan(
            "maximum-size-exact-extremes", model.digest(), experiment.context.digest(), tuple(cases),
            (NullCase("maximum-empty-null", cases[0].inputs, cases[0].expected, cases[0].tolerances),),
            tuple((p.name, p.unit) for p in model.inputs),
            tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
        )
        run = execute(registry, model.equation_id, model.revision, experiment, plan, DECISION)
        self.assertIs(run.state, RunState.COMPUTED)
        self.assertEqual(percolation_report(run)["independent_bond_ensemble"]["enumerated_states"], 4096)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_all_masks_against_independent_exact_oracle(self):
        graphs = (
            line_graph(),
            graph("abc", (("a", "b"), ("b", "c"), ("a", "c"))),
            graph("abcd", (("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")),
                  targets=("c",)),
            graph("abcd", (("a", "b"), ("a", "c"), ("a", "d")),
                  sources=("b",), targets=("d",)),
            graph("abcd", (("a", "b"), ("c", "d"))),
            graph("ab", ()),
            graph("abcd", (("a", "c"), ("b", "d")), sources=("a", "b"), targets=("c", "d")),
            graph("abcde", (("a", "b"), ("b", "c"), ("c", "d"),
                            ("d", "e"), ("a", "e"), ("b", "d"))),
        )
        for g in graphs:
            with self.subTest(graph=g):
                model = fixture_model(g)
                experiment = fixture_experiment(g, mask=0)
                registry = EquationRegistry()
                registry.register(model)
                run = execute(registry, model.equation_id, model.revision, experiment,
                              oracle_plan(model, experiment, exhaustive=True), DECISION)
                self.assertIs(run.state, RunState.COMPUTED)
                self.assertFalse(run.known_answer.cases_failed)
                self.assertEqual(len(run.known_answer.cases_run), 3 * (1 << len(g.edges)))
                self.assertIs(run.record.physical, Status.UNTESTED)

    def test_chain_polynomial_and_hand_stated_partitions(self):
        for p in (0, 0.125, 0.5, 0.9, 1):
            for mask in range(4):
                with self.subTest(p=p, mask=mask):
                    got = _calculate(fixture_model(), {"p": p, "mask": mask})
                    for key, expected in line_expectation(mask, p).items():
                        self.assertAlmostEqual(got[key], expected)

    def test_cycle_two_alternative_paths(self):
        g = graph("abcd", (("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")), targets=("c",))
        for p in (0.125, 0.5, 0.9, 1):
            got = _calculate(fixture_model(g), {"p": p, "mask": 0})
            self.assertAlmostEqual(got["spanning_probability"], 2 * p ** 2 - p ** 4)

    def test_triangle_direct_and_two_bond_paths(self):
        g = graph("abc", (("a", "b"), ("b", "c"), ("a", "c")))
        for p in (0, 0.25, 0.5, 1):
            got = _calculate(fixture_model(g), {"p": p, "mask": 0})
            self.assertAlmostEqual(got["spanning_probability"], p + p ** 2 - p ** 3)

    def test_realization_and_ensemble_are_distinct_questions(self):
        a = _calculate(fixture_model(), {"p": 0.5, "mask": 0})
        b = _calculate(fixture_model(), {"p": 0.5, "mask": 3})
        self.assertEqual(a["spanning"], 0)
        self.assertEqual(b["spanning"], 1)
        self.assertEqual(a["spanning_probability"], b["spanning_probability"])

    def test_isolated_vertices_are_not_discarded(self):
        g = graph("abcd", (("a", "b"),))
        got = _calculate(fixture_model(g), {"p": 1, "mask": 1})
        self.assertEqual(got["component_count"], 3)
        self.assertEqual(got["component_2"], 2)
        self.assertEqual(got["component_3"], 3)
        self.assertEqual(got["spanning_probability"], 0)

    def test_any_source_any_target_rule_is_explicit(self):
        g = graph("abcd", (("b", "d"),), sources=("a", "b"), targets=("c", "d"))
        got = _calculate(fixture_model(g), {"p": 0.5, "mask": 1})
        self.assertEqual(got["spanning"], 1)
        self.assertEqual(got["spanning_probability"], 0.5)

    def test_reverse_edge_direction_does_not_make_graph_directed(self):
        original = line_graph()
        reversed_edges = replace(original, edges=tuple((b, a) for a, b in original.edges))
        for mask in range(4):
                self.assertEqual(_calculate(fixture_model(original), {"p": 0.25, "mask": mask}),
                                 _calculate(fixture_model(reversed_edges), {"p": 0.25, "mask": mask}))

    def test_adding_an_occupied_bond_cannot_destroy_spanning(self):
        g = graph("abcd", (("a", "b"), ("b", "c"), ("c", "d"), ("a", "d")))
        model = fixture_model(g)
        for mask in range(1 << len(g.edges)):
            a = _calculate(model, {"p": 0.5, "mask": mask})
            for edge in range(len(g.edges)):
                b = _calculate(model, {"p": 0.5, "mask": mask | (1 << edge)})
                self.assertLessEqual(a["spanning"], b["spanning"])
                self.assertGreaterEqual(a["component_count"], b["component_count"])

    def test_direct_private_primitive_still_checks_numeric_domain(self):
        # Private functions are not supported experimental entry points, but
        # cannot silently round masks or accept nonfinite numerical arguments.
        for inputs in ({"p": float("nan"), "mask": 0}, {"p": True, "mask": 0},
                       {"p": 0.5, "mask": True}, {"p": 0.5, "mask": 0.25},
                       {"p": 0.5, "mask": 4}, {"p": 0.5}, {"p": 0.5, "mask": 0, "free": 1}):
            with self.subTest(inputs=inputs), self.assertRaises(ValueError):
                _calculate(fixture_model(), inputs)


class PercolationGateTests(unittest.TestCase):
    def setUp(self):
        self.eq = fixture_model()
        self.exp = fixture_experiment()
        self.plan = fixture_plan(self.eq, self.exp)
        self.registry = EquationRegistry()
        self.registry.register(self.eq)

    def run_model(self, exp=None, plan=None, eq=None, **kwargs):
        eq, exp = eq or self.eq, exp or self.exp
        return execute(self.registry, eq.equation_id, eq.revision, exp,
                       plan or fixture_plan(eq, exp), DECISION, **kwargs)

    def context_change(self, key, **changes):
        context = replace(self.exp.context, conditions=tuple(
            replace(c, **changes) if c.key == key else c for c in self.exp.context.conditions
        ))
        return replace(self.exp, context=context, boundary=replace(
            self.exp.boundary, context_digest=context.digest(),
        ))

    def no_evaluation(self, **kwargs):
        with patch("playground.equations.substitution._calculate", wraps=_calculate) as calculate:
            result = self.run_model(**kwargs)
            calculate.assert_not_called()
        self.assertIs(result.state, RunState.BLOCKED)
        self.assertEqual(result.outputs, ())
        return result

    def test_full_gate_order_and_unknown_physical_adequacy(self):
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

    def test_incomplete_ledger_blocks_before_graph(self):
        boundary = replace(self.exp.boundary, accounting=replace(
            self.exp.boundary.accounting, declared_complete=False,
        ))
        result = self.no_evaluation(exp=replace(self.exp, boundary=boundary))
        self.assertIs(result.record.determination, Status.FAILED)

    def test_l0_model_misclosure_blocks_before_graph(self):
        accounting = self.exp.boundary.accounting
        boundary = replace(self.exp.boundary, accounting=replace(
            accounting, accounts=(replace(accounting.accounts[0], final=4),),
        ))
        run = self.no_evaluation(exp=replace(self.exp, boundary=boundary))
        self.assertIs(run.record.physical, Status.FAILED)
        self.assertIsNone(run.known_answer)

    def test_actual_anchor_binding_cannot_be_replaced(self):
        self.no_evaluation(exp=replace(self.exp, anchor=replace(self.exp.anchor, label="another")))

    def test_changed_graph_context_is_not_an_independent_physical_fact(self):
        run = self.no_evaluation(exp=self.context_change("graph", value="another-graph"))
        self.assertIs(run.applicability.state, ApplicabilityState.OUTSIDE)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_correlated_law_cannot_use_independent_ensemble(self):
        self.no_evaluation(exp=self.context_change("occupation_law", value="correlated-bonds"))

    def test_probability_scope_and_uncertainty_are_checked(self):
        for changes in ({"value": -0.1}, {"value": 1.1}, {"uncertainty": 0.6},
                        {"uncertainty": None}, {"basis": ConditionBasis.ASSUMED}):
            with self.subTest(changes=changes):
                self.no_evaluation(exp=self.context_change("bond_probability", **changes))

    def test_fractional_or_out_of_range_mask_is_a_design_failure(self):
        for mask in (0.5, -1, 4):
            with self.subTest(mask=mask):
                run = self.no_evaluation(exp=self.context_change("occupation_mask", value=mask))
                self.assertIs(run.record.physical, Status.UNTESTED)
                if mask == 0.5:
                    self.assertIs(run.record.determination, Status.FAILED)

    def test_uncertain_discrete_mask_is_not_silently_rounded(self):
        run = self.no_evaluation(exp=self.context_change("occupation_mask", value=1, uncertainty=0.1))
        self.assertIs(run.record.determination, Status.FAILED)

    def test_invalid_late_harness_case_preflight_stops_all_evaluation(self):
        bad = replace(self.plan.known_answers[-1], inputs=(("p", 0.5), ("mask", 0.5)))
        plan = replace(self.plan, known_answers=self.plan.known_answers[:-1] + (bad,))
        run = self.no_evaluation(plan=plan)
        self.assertIs(run.record.determination, Status.FAILED)
        self.assertIs(run.record.instrument, Status.UNTESTED)

    def test_out_of_domain_harness_probability_is_not_executed(self):
        bad = replace(self.plan.known_answers[-1], inputs=(("p", 2), ("mask", 3)))
        self.no_evaluation(plan=replace(self.plan, known_answers=(bad,)))

    def test_empty_harnesses_never_qualify(self):
        for changes in ({"known_answers": ()}, {"nulls": ()}):
            with self.subTest(changes=changes):
                run = self.run_model(plan=replace(self.plan, **changes))
                self.assertIs(run.state, RunState.BLOCKED)
                self.assertEqual(run.outputs, ())

    def test_missing_metric_criteria_block_before_graph(self):
        case = self.plan.known_answers[0]
        case = replace(case, expected=(("spanning", 0),), tolerances=(("spanning", 0),))
        self.no_evaluation(plan=replace(self.plan, known_answers=(case,)))

    def test_foreign_plan_cannot_be_reused(self):
        self.no_evaluation(plan=replace(self.plan, equation_digest="old"))
        self.no_evaluation(plan=replace(self.plan, context_digest="old"))

    def test_bad_known_answers_stop_before_null_or_nominal(self):
        case = self.plan.known_answers[0]
        case = replace(case, expected=tuple(
            (key, value + 1 if key == "spanning" else value) for key, value in case.expected
        ))
        with patch("playground.equations.substitution.validate_nulls", wraps=validate_nulls) as nulls:
            run = self.run_model(plan=replace(self.plan, known_answers=(case,)))
            self.assertIs(run.state, RunState.BLOCKED)
            nulls.assert_not_called()
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_defective_spanning_implementation_is_caught_as_instrument_failure(self):
        with patch("playground.equations.percolation._spans", return_value=True):
            run = self.run_model()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)
        self.assertIsNone(run.null)

    def test_defective_union_implementation_cannot_hide_isolated_nodes(self):
        with patch("playground.equations.percolation._components", return_value=((0, 1, 2),)):
            run = self.run_model()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)

    def test_missing_bridge_in_implementation_is_detected(self):
        from ..equations.percolation import _components
        with patch("playground.equations.percolation._components",
                   side_effect=lambda g, mask: _components(g, mask & ~2)):
            run = self.run_model()
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_null_false_positive_stops_before_nominal(self):
        from ..equations.percolation import _calculate_bonds

        def false_positive(eq, inputs):
            result = _calculate_bonds(eq, inputs)
            result["spanning"] = 1.0
            return result

        # A positive-only known case cannot establish false-positive behavior.
        positive = self.plan.known_answers[3]
        plan = replace(self.plan, known_answers=(positive,))
        with patch("playground.equations.percolation._calculate_bonds", side_effect=false_positive) as calc:
            run = self.run_model(plan=plan)
            self.assertEqual(calc.call_count, 2)  # one known + one null, no nominal
        self.assertIs(run.state, RunState.BLOCKED)
        self.assertTrue(run.known_answer.validated_within_tested_cases)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertEqual(run.outputs, ())

    def test_nominal_runtime_failure_retains_no_partial_outputs(self):
        from ..equations.percolation import _calculate_bonds

        def crash_only_nominal(eq, inputs):
            if inputs["p"] == 0.25:
                raise RuntimeError("planted nominal-only error")
            return _calculate_bonds(eq, inputs)

        exp = self.context_change("bond_probability", value=0.25)
        with patch("playground.equations.percolation._calculate_bonds", side_effect=crash_only_nominal):
            run = self.run_model(exp=exp)
        self.assertIs(run.state, RunState.ERROR)
        self.assertIs(run.record.instrument, Status.FAILED)
        self.assertIs(run.record.physical, Status.UNTESTED)
        self.assertEqual(run.outputs, ())

    def test_nominal_nonfinite_missing_or_extra_metrics_are_instrument_failures(self):
        from ..equations.percolation import _calculate_bonds

        for defect in ("nonfinite", "missing", "extra"):
            def corrupt_only_nominal(eq, inputs):
                result = _calculate_bonds(eq, inputs)
                if inputs["p"] == 0.25:
                    if defect == "nonfinite":
                        result["spanning_probability"] = float("nan")
                    elif defect == "missing":
                        result.pop("spanning")
                    else:
                        result["unsupported_metric"] = 0
                return result

            exp = self.context_change("bond_probability", value=0.25)
            with self.subTest(defect=defect), patch(
                "playground.equations.percolation._calculate_bonds", side_effect=corrupt_only_nominal,
            ):
                run = self.run_model(exp=exp)
            self.assertIs(run.state, RunState.ERROR)
            self.assertIs(run.record.instrument, Status.FAILED)
            self.assertIs(run.record.physical, Status.UNTESTED)
            self.assertEqual(run.outputs, ())

    def test_nonzero_p_uncertainty_is_retained_not_propagated(self):
        exp = self.context_change("bond_probability", uncertainty=0.1)
        run = self.run_model(exp=exp)
        self.assertIs(run.state, RunState.COMPUTED)
        self.assertTrue(all(v.uncertainty is None for v in run.outputs))
        condition = next(c for c in run.experiment.context.conditions if c.key == "bond_probability")
        self.assertEqual(condition.uncertainty, 0.1)

    def test_unresolved_assumptions_and_dependencies_block(self):
        for changes, states in (
            ({"assumptions": ("physical links might be correlated",)}, {}),
            ({"unknown_dependencies": ("edge-survey",)}, {}),
            ({"unknown_dependencies": ("edge-survey",)}, {"edge-survey": UnknownState.UNKNOWN}),
            ({"unknown_dependencies": ("edge-survey",)}, {"edge-survey": UnknownState.EXPIRED}),
        ):
            eq = replace(self.eq, revision=str(changes) + str(states), **changes)
            self.registry.register(eq)
            with self.subTest(changes=changes, states=states):
                self.no_evaluation(eq=eq, dependency_states=states)

    def test_substitution_reruns_and_does_not_inherit_support(self):
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
        self.assertNotEqual(first.equation.description().digest(), second.equation.description().digest())

    def test_experiment_failures_stay_with_replacement(self):
        new = replace(self.eq, revision="2")
        self.registry.register(new)
        for axis in (Axis.INSTRUMENT, Axis.DETERMINATION):
            record = FailureRecord((Finding(axis, Status.FAILED, "PLANTED", "failed observation/design",
                                            "validation.test_percolation"),))
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

    def test_changed_boundary_or_edge_set_cannot_inherit_physical_support(self):
        first = self.run_model(assessments=(support(self.eq.description(), self.exp.context),))
        g = replace(self.eq.graph, edges=(("a", "b"),))
        new = fixture_model(g, revision="2")
        self.registry.register(new)
        with patch("playground.equations.substitution._calculate") as calc:
            second = substitute(first, self.registry, new.equation_id, new.revision,
                                oracle_plan(new, self.exp), DECISION, first.supplied_assessments)
            calc.assert_not_called()
        self.assertIs(second.state, RunState.BLOCKED)
        self.assertIs(second.applicability.state, ApplicabilityState.OUTSIDE)
        self.assertEqual(second.applicability.assessments, ())

    def test_disconnection_does_not_qualify_physical_absence(self):
        exp = self.context_change("occupation_mask", value=1)
        run = self.run_model(exp=exp)
        report = percolation_report(run)
        self.assertFalse(report["realization"]["spanning"])
        self.assertGreater(report["independent_bond_ensemble"]["spanning_probability"], 0)
        observation = NonDetectionObservation.from_map(
            "constructed-no-spanning", {"graph_digest": self.eq.graph.digest()},
            effect_size_of_interest=1,
        )
        rejection = claim_absence("physical-coupling-absence", record_non_detection(observation, None))
        self.assertIsInstance(rejection, AbsenceRejection)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_rebound_omitted_edge_model_can_pass_math_without_physical_support(self):
        g = replace(self.eq.graph, edges=(("a", "b"),))
        eq = fixture_model(g, revision="omitted-edge")
        exp = fixture_experiment(g, p=1, mask=1)
        self.registry.register(eq)
        run = self.run_model(eq=eq, exp=exp, plan=oracle_plan(eq, exp))
        self.assertIs(run.state, RunState.COMPUTED)
        self.assertTrue(run.known_answer.validated_within_tested_cases)
        self.assertFalse(percolation_report(run)["realization"]["spanning"])
        self.assertIs(run.applicability.state, ApplicabilityState.UNKNOWN)
        self.assertIs(run.record.physical, Status.UNTESTED)

    def test_audit_record_is_json_and_content_bound(self):
        run = self.run_model()
        data = json.loads(run.to_json())
        self.assertEqual(data["equation"]["graph"]["nodes"], ["a", "b", "c"])
        self.assertEqual(data["equation"]["occupation_law"], OCCUPATION_LAW)
        self.assertEqual(data["equation_digest"], self.eq.digest())
        self.assertEqual(data["context_digest"], self.exp.context.digest())
        self.assertEqual(data["plan_digest"], self.plan.digest())
        self.assertTrue(all(v["uncertainty"] is None for v in data["outputs"]))


class PercolationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = example_runs()

    def test_labeled_components_are_derived_from_recorded_outputs(self):
        run = self.runs[2]
        with patch("playground.equations.percolation._calculate_bonds") as calc:
            report = percolation_report(run)
            calc.assert_not_called()
        self.assertEqual(report["realization"]["components"], [["a", "b", "c"]])
        self.assertEqual(report["independent_bond_ensemble"]["spanning_probability"], 0.25)
        self.assertEqual(report["run_digest"], run.digest())
        self.assertIsNone(report["output_uncertainty"])

    def test_report_refuses_blocked_runs(self):
        with self.assertRaises(ValueError):
            percolation_report(replace(self.runs[0], state=RunState.BLOCKED, outputs=()))

    def test_finite_grid_crossing_is_a_bracket_not_a_critical_point(self):
        result = finite_transition_bracket(self.runs, 0.5, DECISION)
        self.assertEqual(result["status"], "finite-grid-bracket")
        self.assertEqual(result["p_bracket"], [0.5, 0.75])
        self.assertNotIn("critical_threshold", result)
        self.assertFalse(result["uncertainty_propagated"])
        self.assertEqual(len(result["run_digests"]), 5)

    def test_changing_selected_criterion_changes_bracket_not_system(self):
        a = finite_transition_bracket(self.runs, 0.25, DECISION)
        b = finite_transition_bracket(self.runs, 0.9, DECISION)
        self.assertEqual(a["p_bracket"], [0.25, 0.5])
        self.assertEqual(b["p_bracket"], [0.75, 1.0])
        self.assertEqual(a["run_digests"], b["run_digests"])

    def test_unreached_criterion_has_no_invented_threshold(self):
        result = finite_transition_bracket(self.runs[:3], 0.5, DECISION)
        self.assertEqual(result["status"], "criterion-not-reached-on-supplied-grid")
        self.assertIsNone(result["p_bracket"])

    def test_criterion_met_at_start_has_no_extrapolated_bracket(self):
        result = finite_transition_bracket(self.runs[3:], 0.5, DECISION)
        self.assertEqual(result["status"], "criterion-already-met-at-grid-start")
        self.assertIsNone(result["p_bracket"])

    def test_grid_must_be_ordered_and_have_two_points(self):
        for runs in (self.runs[:1], tuple(reversed(self.runs)), (self.runs[0], self.runs[0])):
            with self.subTest(runs=len(runs)), self.assertRaises(ValueError):
                finite_transition_bracket(runs, 0.5, DECISION)

    def test_probability_criterion_and_selection_are_explicit(self):
        for target in (0, 1, -1, float("nan"), float("inf"), True):
            with self.subTest(target=target), self.assertRaises(ValueError):
                finite_transition_bracket(self.runs, target, DECISION)
        with self.assertRaises(ValueError):
            finite_transition_bracket(self.runs, 0.5, None)

    def test_context_changes_other_than_p_cannot_be_called_a_probability_scan(self):
        for key, value in (("observer", "another-observer"), ("occupation_mask", 0),
                           ("environment", "another-environment")):
            last = self.runs[-1]
            context = replace(last.experiment.context, conditions=tuple(
                replace(c, value=value) if c.key == key else c
                for c in last.experiment.context.conditions
            ))
            altered = replace(last, experiment=replace(last.experiment, context=context))
            with self.subTest(key=key), self.assertRaises(ValueError):
                finite_transition_bracket(self.runs[:-1] + (altered,), 0.5, DECISION)

    def test_nonzero_probability_uncertainty_is_not_a_crisp_bracket(self):
        last = self.runs[-1]
        context = replace(last.experiment.context, conditions=tuple(
            replace(c, uncertainty=0.01) if c.key == "bond_probability" else c
            for c in last.experiment.context.conditions
        ))
        with self.assertRaises(ValueError):
            finite_transition_bracket(
                self.runs[:-1] + (replace(last, experiment=replace(last.experiment, context=context)),),
                0.5, DECISION,
            )

    def test_grid_rejects_different_revisions(self):
        last = replace(self.runs[-1], equation=replace(self.runs[-1].equation, revision="2"))
        with self.assertRaises(ValueError):
            finite_transition_bracket(self.runs[:-1] + (last,), 0.5, DECISION)

    def test_disconnected_graph_can_never_reach_selected_grid_criterion(self):
        g = graph("abcd", (("a", "b"), ("c", "d")))
        model = fixture_model(g)
        registry = EquationRegistry()
        registry.register(model)
        runs = []
        for p in (0, 0.5, 1):
            exp = fixture_experiment(g, p=p, mask=3)
            runs.append(execute(registry, model.equation_id, model.revision, exp,
                                oracle_plan(model, exp), DECISION))
        result = finite_transition_bracket(tuple(runs), 0.5, DECISION)
        self.assertEqual(result["status"], "criterion-not-reached-on-supplied-grid")
        self.assertIsNone(result["p_bracket"])
        self.assertTrue(all(r.record.physical is Status.UNTESTED for r in runs))


class PercolationMutationProbeTests(unittest.TestCase):
    def test_known_answer_bypass_test_detects_a_forged_pass(self):
        forged = InstrumentValidation("forged", FailureRecord(), ("forged-case",), ())
        result = unittest.TestResult()
        case = PercolationGateTests("test_bad_known_answers_stop_before_null_or_nominal")
        with patch("playground.equations.substitution.validate_known_answers", return_value=forged):
            case.run(result)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.failures), 1)


if __name__ == "__main__":
    unittest.main()
