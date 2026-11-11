"""Constructed system classes, not a physical equation catalogue.

Every run enters the ordinary substitution path. Expectations are hand-stated,
never calculated by the backend under test. Class names, boundaries and
accounting choices are selections, not discovered facts.

From experimental/: python3 -m playground.validation.cross_system
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace

from ..applicability.mapping import (
    Condition, ConditionBasis, Constraint, Context, Decision, Domain, build_map,
)
from ..equations.adapter import Equation, EquationRegistry, InputPort, OutputPort
from ..equations.branching import FiniteBranching, OffspringLaw
from ..equations.branching_example import (
    fixture_experiment as lineage_experiment,
    fixture_model as lineage_model, stated_expectation,
)
from ..equations.percolation import BondPercolation, FiniteGraph
from ..equations.percolation_example import (
    fixture_experiment as graph_experiment, fixture_model as graph_model,
)
from ..equations.substitution import (
    BoundaryProtocol, Experiment, ValidationPlan, execute,
)
from ..failures import EvidenceRef
from ..gates.l0_closure import (
    BoundaryAccounting, Direction, Exchange, QuantityAccount, ValueProvenance,
)
from ..reference.anchor import AnchorState
from .known_answer import KnownAnswerCase
from .null_harness import NullCase


DECISION = Decision(
    "constructed-cross-system-fixture-author",
    "Test diagnostic distinctions across selected system classes, without ranking descriptions.",
    "Explicit synthetic boundaries, units, hand-stated expectations and finite observation scopes.",
)
EVIDENCE = (EvidenceRef("constructed-fixture", "validation/cross_system.py"),)


@dataclass(frozen=True)
class SystemFixture:
    system_class: str
    question: str
    accounting_meaning: str
    limitations: tuple[str, ...]
    model: Equation | BondPercolation | FiniteBranching
    experiment: Experiment
    plan: ValidationPlan
    expected: tuple[tuple[str, float], ...]
    observation_unit: str

    def run(self, **kwargs):
        registry = EquationRegistry()
        registry.register(self.model)
        return execute(
            registry, self.model.equation_id, self.model.revision,
            self.experiment, self.plan, DECISION, **kwargs,
        )

    def sensitivity_conditions(self):
        # Even numerical twins must not inherit each other's calibration.
        return {
            "system_class": self.system_class,
            "context_digest": self.experiment.context.digest(),
            "observer": next(c.value for c in self.experiment.context.conditions
                             if c.key == "observer"),
            "effect_unit": self.observation_unit,
            "window": "selected-1-second-readout-window",
        }


def _plan(model, experiment, known, null_inputs, baseline):
    return ValidationPlan(
        f"{model.equation_id}-hand-stated-plan", model.digest(),
        experiment.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            f"hand-stated-{i}", inputs, expected,
            {key: 1e-12 for key in expected},
            "CONSTRUCTED explicit answer; no backend used to generate this criterion.",
        ) for i, (inputs, expected) in enumerate(known)),
        (NullCase.from_maps(
            "hand-stated-null", null_inputs, baseline,
            {key: 0.0 for key in baseline},
            "Synthetic null only; not physical absence or observer calibration.",
        ),),
        tuple((p.name, p.unit) for p in model.inputs),
        tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
    )


def _storage(label, question, ports, expressions, accounts, known, null_inputs,
             baseline, expected, observation_unit, limits):
    """Separate selected storage laws; dimensional declarations are not proofs."""
    boundary_label = f"selected-{label}-boundary"
    anchor = AnchorState.from_maps(
        f"{label}-unloaded-reference", {q: 0.0 for q, _, _ in accounts},
        ("CONSTRUCTED selected unloaded reference; not a measured physical anchor.",),
    )
    categories = (
        ("system_class", Domain.BOUNDARY, label),
        ("boundary", Domain.BOUNDARY, boundary_label),
        ("observer", Domain.OBSERVER, f"synthetic-{label}-readout"),
        ("environment", Domain.ENVIRONMENT, f"selected-ideal-{label}-environment"),
        ("relationships", Domain.RELATIONSHIPS, f"selected-constant-linear-{label}-law"),
        ("uncertainty", Domain.UNCERTAINTY, "nominal-selected-values-no-propagation"),
        ("anchor", Domain.ANCHOR, anchor.label),
    )
    conditions = tuple(Condition(k, d, v, ConditionBasis.SELECTED, DECISION)
                       for k, d, v in categories) + tuple(
        Condition(k, domain, value, ConditionBasis.SELECTED, DECISION, unit, 0.0)
        for k, unit, value, domain, _, _ in ports
    ) + (
        Condition("observation_window", Domain.CONTROL, 1.0,
                  ConditionBasis.SELECTED, DECISION, "s", 0.0),
    )
    constraints = tuple(Constraint(k, d, DECISION, equals=v) for k, d, v in categories) + tuple(
        Constraint(k, domain, DECISION, lower=lo, upper=hi, unit=unit)
        for k, unit, _, domain, lo, hi in ports
    ) + (
        Constraint("observation_window", Domain.CONTROL, DECISION, lower=1, upper=1, unit="s"),
    )
    model = Equation(
        f"constructed-{label}", "1", question,
        tuple(InputPort(k, k, unit) for k, unit, *_ in ports),
        tuple(OutputPort(k, expression, unit) for k, expression, unit in expressions),
        constraints, DECISION, EVIDENCE,
    )
    context = Context(
        f"constructed-{label}-cell", "1", question, anchor.digest(), conditions,
        "Selected exact fixture inputs, not measurement certainty; output uncertainty unpropagated.",
    )
    # Exchange values are separately stated, not copied from calculated outputs.
    ledger = BoundaryAccounting(
        boundary_label, tuple(QuantityAccount(
            q, 0.0, final, ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
            (
                Exchange(q, Direction.INFLOW, final, f"stated-{q}-input",
                         ValueProvenance.SPECIFIED, "control:drive"),
                Exchange(q, Direction.OUTFLOW, 0.0, f"selected-zero-{q}-readout-cost",
                         ValueProvenance.SPECIFIED, "observer:readout"),
            ), 0.0,
        ) for q, _, final in accounts),
        True, ("control:drive", "observer:readout"),
    )
    experiment = Experiment(context, anchor, BoundaryProtocol(
        context.digest(), anchor.digest(), ledger,
        tuple((q, unit) for q, unit, _ in accounts),
        (("control:drive", ports[-1][0]), ("observer:readout", "observer")), DECISION,
    ))
    return SystemFixture(
        label, question,
        "Selected physical-quantity bookkeeping with separately stated inputs, not empirical closure.",
        limits + (
            "Structural completeness does not prove all physically relevant accounts or exchanges were included.",
            "Declared SI units are retained; no symbolic dimensional proof or calibration is performed.",
        ), model, experiment,
        _plan(model, experiment, known, null_inputs, baseline),
        tuple(sorted(expected.items())), observation_unit,
    )


def _tag_surrogate(label, model, experiment):
    """Add a selected class constraint without changing native backend gates."""
    condition = Condition("system_class", Domain.BOUNDARY, label,
                          ConditionBasis.SELECTED, DECISION)
    context = replace(
        experiment.context, context_id=f"constructed-{label}-cell",
        conditions=experiment.context.conditions + (
            condition, Condition("observation_window", Domain.CONTROL, 1.0,
                                 ConditionBasis.SELECTED, DECISION, "s", 0.0),
        ),
    )
    experiment = replace(experiment, context=context, boundary=replace(
        experiment.boundary, context_digest=context.digest(),
    ))
    model = replace(model, constraints=model.constraints + (
        Constraint("system_class", Domain.BOUNDARY, DECISION, equals=label),
        Constraint("observation_window", Domain.CONTROL, DECISION, lower=1, upper=1, unit="s"),
    ))
    return model, experiment


def fixtures() -> tuple[SystemFixture, ...]:
    thermal = _storage(
        "thermal-storage", "What does a selected constant-capacity cell store over this temperature increment?",
        (("capacity", "J/K", 2.0, Domain.RELATIONSHIPS, 1.0, 4.0),
         ("delta_temperature", "K", 3.0, Domain.CONTROL, 0.0, 4.0)),
        (("energy", "capacity*delta_temperature", "J"),),
        (("energy", "J", 6.0),),
        (({"capacity": 2, "delta_temperature": 1}, {"energy": 2}),
         ({"capacity": 3, "delta_temperature": 2}, {"energy": 6})),
        {"capacity": 2, "delta_temperature": 0}, {"energy": 0}, {"energy": 6}, "J",
        ("Constant heat capacity, selected finite increment; no phase change, transport or ambient heat-loss model.",),
    )
    electrical = _storage(
        "electrical-storage", "What charge and energy does a selected ideal capacitor store?",
        (("capacitance", "F", 2.0, Domain.RELATIONSHIPS, 1.0, 4.0),
         ("voltage", "V", 3.0, Domain.CONTROL, 0.0, 4.0)),
        (("charge", "capacitance*voltage", "C"),
         ("energy", "0.5*capacitance*voltage**2", "J")),
        (("charge", "C", 6.0), ("energy", "J", 9.0)),
        (({"capacitance": 2, "voltage": 1}, {"charge": 2, "energy": 1}),
         ({"capacitance": 3, "voltage": 2}, {"charge": 6, "energy": 6})),
        {"capacitance": 2, "voltage": 0}, {"charge": 0, "energy": 0},
        {"charge": 6, "energy": 9}, "C",
        ("Selected linear capacitance; no leakage, dielectric breakdown, dissipation or source circuit model.",),
    )
    mechanical = _storage(
        "mechanical-storage", "What force and energy does a selected linear spring produce?",
        (("stiffness", "N/m", 2.0, Domain.RELATIONSHIPS, 1.0, 4.0),
         ("displacement", "m", 3.0, Domain.CONTROL, 0.0, 4.0)),
        (("force", "stiffness*displacement", "N"),
         ("energy", "0.5*stiffness*displacement**2", "J")),
        (("energy", "J", 9.0),),
        (({"stiffness": 2, "displacement": 1}, {"force": 2, "energy": 1}),
         ({"stiffness": 3, "displacement": 2}, {"force": 6, "energy": 6})),
        {"stiffness": 2, "displacement": 0}, {"force": 0, "energy": 0},
        {"force": 6, "energy": 9}, "N",
        ("Selected linear elastic spring; no yielding, hysteresis, dissipation or dynamical trajectory model.",),
    )
    graph = FiniteGraph(
        ("s", "a", "b", "t"), (("s", "a"), ("a", "t"), ("s", "b"), ("b", "t")),
        ("s",), ("t",), DECISION, EVIDENCE,
    )
    graph_eq, graph_exp = _tag_surrogate(
        "porous-connectivity-surrogate", graph_model(graph),
        graph_experiment(graph, p=0.5, mask=3),
    )
    # Explicit partition answers and exact 16-mask ensemble counts.
    graph_nominal = dict(
        spanning=1, component_count=2, largest_component_size=3, occupied_edge_count=2,
        component_0=0, component_1=0, component_2=2, component_3=0,
        spanning_probability=7 / 16, expected_component_count=33 / 16,
        expected_largest_component_size=45 / 16,
    )
    graph_null = dict(
        spanning=0, component_count=4, largest_component_size=1, occupied_edge_count=0,
        component_0=0, component_1=1, component_2=2, component_3=3,
        spanning_probability=0, expected_component_count=4, expected_largest_component_size=1,
    )
    graph_full = dict(
        spanning=1, component_count=1, largest_component_size=4, occupied_edge_count=4,
        component_0=0, component_1=0, component_2=0, component_3=0,
        spanning_probability=1, expected_component_count=1, expected_largest_component_size=4,
    )
    porous = SystemFixture(
        "porous-connectivity-surrogate", "Does a selected finite diamond graph connect its declared boundaries?",
        "Fixed node-universe count only, NOT mass, energy, permeability or fluid conservation.",
        ("Selected topology and independent bonds; no pressure, flow rate or realized porous medium.",
         "Ensemble connectivity is not physical transport, an infinite threshold or an absence observation."),
        graph_eq, graph_exp, _plan(
            graph_eq, graph_exp,
            (({"p": 0.5, "mask": 3}, graph_nominal),
             ({"p": 1, "mask": 15}, graph_full)),
            {"p": 0, "mask": 0}, graph_null,
        ), tuple(sorted(graph_nominal.items())), "1",
    )
    law = OffspringLaw(((0, 1), (1, 1)), DECISION, EVIDENCE)
    branch_eq, branch_exp = _tag_surrogate(
        "lineage-reproduction-surrogate", lineage_model(law),
        lineage_experiment(law, initial=2, generations=2),
    )
    branch_nominal = stated_expectation(
        {0: 9 / 16, 1: 6 / 16, 2: 1 / 16}, 0.5, 0.25, 0.5, 0.375, 3.5,
    )
    branch_null = stated_expectation({0: 1}, 0.5, 0.25, 0, 0, 0)
    branch_initial = stated_expectation({2: 1}, 0.5, 0.25, 2, 0, 2)
    lineage = SystemFixture(
        "lineage-reproduction-surrogate", "What finite descendant distribution follows this selected offspring law?",
        "Fixed founder-cohort identity only, NOT conserved population, biomass, energy or resources.",
        ("Selected iid single-type law, two founders, finite generations; no interaction, immigration or resource model.",
         "Model extinction and finite survival are neither observed absence nor permanent organization."),
        branch_eq, branch_exp, _plan(
            branch_eq, branch_exp,
            (({"initial": 2, "generations": 0}, branch_initial),
             ({"initial": 2, "generations": 2}, branch_nominal)),
            {"initial": 0, "generations": 0}, branch_null,
        ), tuple(sorted(branch_nominal.items())), "1",
    )
    return thermal, electrical, mechanical, porous, lineage


def diagnostic_report():
    selected = fixtures()
    runs = tuple(f.run() for f in selected)
    mapping = build_map(
        tuple(f.model.description() for f in selected),
        tuple(f.experiment.context for f in selected),
        diagnostics={(r.equation.description().digest(), r.experiment.context.digest()): r.record
                     for r in runs},
    )
    return {
        "schema": "playground/cross-system-diagnostics/0.1",
        "status": "CONSTRUCTED fixtures, not physical validation or a universal hierarchy",
        "limits": [
            "Selected classes and boundaries are not independently established physical facts.",
            "Diagnostic consistency does not establish physical adequacy, observer validity or complete physical accounting.",
            "No untested system class, continuum process, biological population or external evidence is validated.",
        ],
        "systems": [
            dict(system_class=f.system_class, question=f.question,
                 accounting_meaning=f.accounting_meaning, limitations=f.limitations,
                 hand_stated_nominal=dict(f.expected),
                 sensitivity_scope=f.sensitivity_conditions(), run=r.to_dict())
            for f, r in zip(selected, runs)
        ],
        "applicability": mapping.to_dict(),
    }


if __name__ == "__main__":
    print(json.dumps(diagnostic_report(), indent=2, sort_keys=True, allow_nan=False))
