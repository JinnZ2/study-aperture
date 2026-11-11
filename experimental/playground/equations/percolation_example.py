"""CONSTRUCTED finite chain, with hand-stated diagnostic expectations.

From experimental/: python3 -m playground.equations.percolation_example
The node-count ledger is mathematical accounting, NOT physical energy closure.
"""

from __future__ import annotations

import json

from ..applicability.mapping import (
    Condition, ConditionBasis, Constraint, Context, Decision, Domain,
)
from ..failures import EvidenceRef
from ..gates.l0_closure import (
    BoundaryAccounting, Direction, Exchange, QuantityAccount, ValueProvenance,
)
from ..reference.anchor import AnchorState
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase
from .adapter import EquationRegistry
from .percolation import BondPercolation, FiniteGraph, OCCUPATION_LAW
from .percolation_report import finite_transition_bracket, percolation_report
from .substitution import BoundaryProtocol, Experiment, ValidationPlan, execute


DECISION = Decision(
    "constructed-percolation-example-author",
    "Test finite mathematical connectivity without asserting a physical network.",
    "Selected node universe, disjoint any-source/any-target boundary sets, independent uniform bonds.",
)
EVIDENCE = (EvidenceRef("constructed-definition", "equations/percolation_example.py"),)


def line_graph() -> FiniteGraph:
    return FiniteGraph(("a", "b", "c"), (("a", "b"), ("b", "c")),
                       ("a",), ("c",), DECISION, EVIDENCE)


def fixture_model(graph: FiniteGraph | None = None, revision: str = "1") -> BondPercolation:
    graph = graph if graph is not None else line_graph()
    _, rules = _conditions(graph, 0.5, 3 if len(graph.edges) >= 2 else 0)
    return BondPercolation("finite-bond-connectivity", revision, graph, rules, DECISION, EVIDENCE)


def _conditions(graph: FiniteGraph, p: float, mask: int):
    categories = (
        ("boundary", Domain.BOUNDARY, "selected-finite-node-universe"),
        ("observer", Domain.OBSERVER, "constructed-exact-graph-readout"),
        ("environment", Domain.ENVIRONMENT, "topology-only-no-physical-energy-model"),
        ("graph", Domain.RELATIONSHIPS, graph.digest()),
        ("occupation_law", Domain.RELATIONSHIPS, OCCUPATION_LAW),
        ("uncertainty", Domain.UNCERTAINTY, "nominal-only-no-uncertainty-propagation"),
        ("anchor", Domain.ANCHOR, "node-universe-anchor-v1"),
    )
    conditions = tuple(
        Condition(key, domain, value, ConditionBasis.SELECTED, DECISION)
        for key, domain, value in categories
    ) + (
        Condition("bond_probability", Domain.CONTROL, p, ConditionBasis.SELECTED, DECISION, "1", 0.0),
        Condition("occupation_mask", Domain.RELATIONSHIPS, mask,
                  ConditionBasis.SELECTED, DECISION, "1", 0.0),
    )
    rules = tuple(Constraint(key, domain, DECISION, equals=value)
                  for key, domain, value in categories) + (
        Constraint("bond_probability", Domain.CONTROL, DECISION, lower=0, upper=1, unit="1"),
        Constraint("occupation_mask", Domain.RELATIONSHIPS, DECISION,
                   lower=0, upper=(1 << len(graph.edges)) - 1, unit="1"),
    )
    return conditions, rules


def fixture_experiment(graph: FiniteGraph | None = None, p: float = 0.5, mask: int = 3) -> Experiment:
    graph = graph if graph is not None else line_graph()
    anchor = AnchorState.from_maps(
        "node-universe-anchor-v1", {"node_count": float(len(graph.nodes))},
        ("CONSTRUCTED fixed node universe; no physical energy model",),
    )
    context = Context(
        "constructed-finite-bond-cell", "1",
        "Selected mathematical graph only; no empirical claim or physical observer validation.",
        anchor.digest(), _conditions(graph, p, mask)[0],
        "Exact selected mask; nominal p only; no measurement uncertainty or physical adequacy established.",
    )
    ledger = BoundaryAccounting(
        "selected-finite-node-universe",
        (QuantityAccount(
            "node_count", float(len(graph.nodes)), float(len(graph.nodes)),
            ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
            (
                Exchange("node_count", Direction.INFLOW, 0.0, "zero-node-entry",
                         ValueProvenance.SPECIFIED, "control:bonds"),
                Exchange("node_count", Direction.OUTFLOW, 0.0, "zero-node-removal",
                         ValueProvenance.SPECIFIED, "observer:readout"),
            ), 0.0,
        ),), True, ("control:bonds", "observer:readout"),
    )
    protocol = BoundaryProtocol(
        context.digest(), anchor.digest(), ledger, (("node_count", "1"),),
        (("control:bonds", "bond_probability"), ("observer:readout", "observer")), DECISION,
    )
    return Experiment(context, anchor, protocol)


def line_expectation(mask, p):
    """Hand-stated closed-form expectations for the TWO-edge three-node chain.

    No production graph routine or enumeration is used to form these answers.
    """
    configurations = {
        0: (0, 3, 1, 0, (0, 1, 2)),
        1: (0, 2, 2, 1, (0, 0, 2)),
        2: (0, 2, 2, 1, (0, 1, 1)),
        3: (1, 1, 3, 2, (0, 0, 0)),
    }
    spanning, count, largest, occupied, labels = configurations[mask]
    return dict(
        spanning=spanning, component_count=count, largest_component_size=largest,
        occupied_edge_count=occupied, spanning_probability=p * p,
        expected_component_count=3 - 2 * p, expected_largest_component_size=1 + 2 * p,
        **{f"component_{i}": label for i, label in enumerate(labels)},
    )


def fixture_plan(model: BondPercolation, experiment: Experiment) -> ValidationPlan:
    if model.graph != line_graph():
        raise ValueError("hand-stated chain plan cannot validate another graph")
    cases = []
    for mask, p in ((0, 0), (1, 0.5), (2, 0.5), (3, 1), (3, 0.5)):
        expected = line_expectation(mask, p)
        cases.append(KnownAnswerCase.from_maps(
            f"chain-mask-{mask}-p-{p}", {"p": p, "mask": mask}, expected,
            {key: 1e-12 for key in expected}, "Hand-stated chain partition and polynomial.",
        ))
    baseline = line_expectation(0, 0)
    return ValidationPlan(
        "constructed-two-edge-chain-plan", model.digest(), experiment.context.digest(),
        tuple(cases),
        (NullCase.from_maps(
            "no-occupied-bonds-no-spanning", {"p": 0, "mask": 0}, baseline,
            {key: 0.0 for key in baseline}, "Known mathematical null, not a physical absence.",
        ),),
        tuple((p.name, p.unit) for p in model.inputs),
        tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
    )


def example_runs():
    model = fixture_model()
    registry = EquationRegistry()
    registry.register(model)
    runs = []
    for p in (0.0, 0.25, 0.5, 0.75, 1.0):
        experiment = fixture_experiment(p=p)
        runs.append(execute(registry, model.equation_id, model.revision, experiment,
                            fixture_plan(model, experiment), DECISION))
    return tuple(runs)


if __name__ == "__main__":
    runs = example_runs()
    print(json.dumps({
        "status": "CONSTRUCTED finite graph, not physical validation",
        "runs": [r.to_dict() for r in runs],
        "reports": [percolation_report(r) for r in runs],
        "finite_transition": finite_transition_bracket(runs, 0.5, DECISION),
    }, indent=2, sort_keys=True, allow_nan=False))
