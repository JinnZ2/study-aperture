"""CONSTRUCTED branching experiments: same mean is not the same persistence.

From experimental/: python3 -m playground.equations.branching_example
The fixed-founder ledger is mathematical bookkeeping, NOT population or energy
conservation. No physical adequacy or calibrated observer is supplied.
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
from .branching import (
    BRANCHING_DEFINITION, MAX_GENERATIONS, MAX_INITIAL_POPULATION, MAX_POPULATION,
    FiniteBranching, OffspringLaw,
)
from .substitution import BoundaryProtocol, Experiment, ValidationPlan, execute


DECISION = Decision(
    "constructed-branching-example-author",
    "Examine finite lineage ensembles without equating a stable mean with permanent organization.",
    "Selected iid single-type offspring, fixed founder cohort, discrete finite generations, no immigration.",
)
EVIDENCE = (EvidenceRef("constructed-definition", "equations/branching_example.py"),)


def binary_law() -> OffspringLaw:
    return OffspringLaw(((0, 1), (2, 1)), DECISION, EVIDENCE)


def deterministic_one() -> OffspringLaw:
    return OffspringLaw(((1, 1),), DECISION, EVIDENCE)


def _conditions(law: OffspringLaw, initial: int, generations: int):
    categories = (
        ("boundary", Domain.BOUNDARY, "selected-founder-lineage-universe"),
        ("observer", Domain.OBSERVER, "constructed-exact-generation-readout"),
        ("environment", Domain.ENVIRONMENT, "no-resource-or-physical-energy-model"),
        ("offspring_law", Domain.RELATIONSHIPS, law.digest()),
        ("branching_definition", Domain.RELATIONSHIPS, BRANCHING_DEFINITION),
        ("uncertainty", Domain.UNCERTAINTY, "selected-integer-cohort-and-horizon-no-propagation"),
        ("anchor", Domain.ANCHOR, "founder-cohort-anchor-v1"),
    )
    conditions = tuple(Condition(key, domain, value, ConditionBasis.SELECTED, DECISION)
                       for key, domain, value in categories) + (
        Condition("initial_population", Domain.CONTROL, initial, ConditionBasis.SELECTED, DECISION, "1", 0.0),
        Condition("generation_horizon", Domain.CONTROL, generations, ConditionBasis.SELECTED, DECISION, "1", 0.0),
    )
    rules = tuple(Constraint(key, domain, DECISION, equals=value)
                  for key, domain, value in categories) + (
        Constraint("initial_population", Domain.CONTROL, DECISION,
                   lower=0, upper=MAX_INITIAL_POPULATION, unit="1"),
        Constraint("generation_horizon", Domain.CONTROL, DECISION,
                   lower=0, upper=MAX_GENERATIONS, unit="1"),
    )
    return conditions, rules


def fixture_model(law: OffspringLaw | None = None, revision: str = "1") -> FiniteBranching:
    law = law if law is not None else binary_law()
    return FiniteBranching("finite-lineage-branching", revision, law,
                           _conditions(law, 1, 2)[1], DECISION, EVIDENCE)


def fixture_experiment(
    law: OffspringLaw | None = None, initial: int = 1, generations: int = 2,
) -> Experiment:
    law = law if law is not None else binary_law()
    anchor = AnchorState.from_maps(
        "founder-cohort-anchor-v1", {"founder_count": float(initial)},
        ("Selected founder cohort, NOT a conserved total population or physical energy",),
    )
    context = Context(
        "constructed-branching-cell", "1",
        "CONSTRUCTED finite-generation lineage ensemble; no realized history or empirical finding.",
        anchor.digest(), _conditions(law, initial, generations)[0],
        "Exact selected initial count/horizon and rational law; no parameter, measurement or model uncertainty propagated.",
    )
    ledger = BoundaryAccounting(
        "selected-founder-lineage-universe",
        (QuantityAccount(
            "founder_count", float(initial), float(initial),
            ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
            (
                Exchange("founder_count", Direction.INFLOW, 0.0, "zero-cohort-entry",
                         ValueProvenance.SPECIFIED, "control:cohort"),
                Exchange("founder_count", Direction.INFLOW, 0.0, "zero-horizon-cohort-entry",
                         ValueProvenance.SPECIFIED, "control:horizon"),
                Exchange("founder_count", Direction.OUTFLOW, 0.0, "zero-observer-cohort-removal",
                         ValueProvenance.SPECIFIED, "observer:readout"),
            ), 0.0,
        ),), True, ("control:cohort", "control:horizon", "observer:readout"),
    )
    protocol = BoundaryProtocol(
        context.digest(), anchor.digest(), ledger, (("founder_count", "1"),),
        (("control:cohort", "initial_population"), ("control:horizon", "generation_horizon"),
         ("observer:readout", "observer")), DECISION,
    )
    return Experiment(context, anchor, protocol)


def stated_expectation(pmf, mean, offspring_variance, expected, variance, cumulative):
    """Assemble explicit hand-stated answers, never invoke the backend."""
    return dict(
        offspring_mean=mean, offspring_variance=offspring_variance,
        expected_population=expected, population_variance=variance,
        extinction_by_horizon=pmf.get(0, 0), survival_at_horizon=sum(p for k, p in pmf.items() if k > 0),
        expected_cumulative_population=cumulative, probability_mass=1.0,
        **{f"population_probability_{k}": pmf.get(k, 0.0) for k in range(MAX_POPULATION + 1)},
    )


def fixture_plan(model: FiniteBranching, experiment: Experiment) -> ValidationPlan:
    if model.law == binary_law():
        entries = (
            (1, 0, stated_expectation({1: 1}, 1, 1, 1, 0, 1)),
            (1, 1, stated_expectation({0: 0.5, 2: 0.5}, 1, 1, 1, 1, 2)),
            (1, 2, stated_expectation({0: 5 / 8, 2: 1 / 4, 4: 1 / 8}, 1, 1, 1, 2, 3)),
            (2, 1, stated_expectation({0: 1 / 4, 2: 1 / 2, 4: 1 / 4}, 1, 1, 2, 2, 4)),
        )
        baseline = stated_expectation({0: 1}, 1, 1, 0, 0, 0)
    elif model.law == deterministic_one():
        entries = (
            (1, 0, stated_expectation({1: 1}, 1, 0, 1, 0, 1)),
            (1, 3, stated_expectation({1: 1}, 1, 0, 1, 0, 4)),
            (2, 2, stated_expectation({2: 1}, 1, 0, 2, 0, 6)),
        )
        baseline = stated_expectation({0: 1}, 1, 0, 0, 0, 0)
    else:
        raise ValueError("this hand-stated plan covers only the two declared example laws")
    cases = tuple(KnownAnswerCase.from_maps(
        f"stated-initial-{initial}-generation-{generations}",
        {"initial": initial, "generations": generations}, expected,
        {key: 1e-12 for key in expected}, "Hand-stated finite branching distribution and moments.",
    ) for initial, generations, expected in entries)
    return ValidationPlan(
        "constructed-finite-branching-plan", model.digest(), experiment.context.digest(), cases,
        (NullCase.from_maps(
            "no-founders-no-descendants", {"initial": 0, "generations": 0}, baseline,
            {key: 0 for key in baseline}, "Mathematical zero-cohort null, not physical absence.",
        ),),
        tuple((p.name, p.unit) for p in model.inputs),
        tuple((p.name, p.unit) for p in model.outputs), DECISION, EVIDENCE,
    )


def example_runs(law: OffspringLaw | None = None):
    model = fixture_model(law)
    registry = EquationRegistry()
    registry.register(model)
    runs = []
    for generations in range(6):
        experiment = fixture_experiment(model.law, generations=generations)
        runs.append(execute(registry, model.equation_id, model.revision, experiment,
                            fixture_plan(model, experiment), DECISION))
    return tuple(runs)


if __name__ == "__main__":
    from .branching_report import branching_report, generation_profile

    examples = {}
    for label, law in (("stochastic-mean-one", binary_law()),
                       ("deterministic-mean-one", deterministic_one())):
        runs = example_runs(law)
        examples[label] = {
            "runs": [r.to_dict() for r in runs],
            "reports": [branching_report(r) for r in runs],
            "finite_generation_profile": generation_profile(runs, DECISION),
        }
    print(json.dumps({
        "status": "CONSTRUCTED ensembles, not observed histories or physical validation",
        "examples": examples,
    }, indent=2, sort_keys=True, allow_nan=False))
