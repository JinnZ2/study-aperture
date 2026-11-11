"""CONSTRUCTED example, not an empirical claim about any physical system.

Run from experimental/: python3 -m playground.applicability.example
Emits an inspectable JSON map to stdout. All evidence locations identify
synthetic fixtures in this file; no real experiment has been performed.
"""

from dataclasses import replace

from ..failures import EvidenceRef
from .mapping import (
    ApplicabilityMap, Assessment, Condition, ConditionBasis, Constraint,
    Context, Decision, Description, Domain, EvidenceKind, Judgment, build_map,
)


DECISION = Decision(
    "synthetic-example-author",
    "Exercise independent context-dependent mapping cells, not select a universal model.",
    "Constructed seven-coordinate protocol; toy energy window and observation duration.",
)


def fixture() -> tuple[Description, Context]:
    categories = (
        ("boundary", Domain.BOUNDARY, "selected-cell-A"),
        ("control", Domain.CONTROL, "fixed-drive"),
        ("observer", Domain.OBSERVER, "passive-v1"),
        ("relationships", Domain.RELATIONSHIPS, "nearest-neighbour"),
        ("uncertainty", Domain.UNCERTAINTY, "bounded-protocol-v1"),
        ("anchor", Domain.ANCHOR, "anchor-A-v1"),
    )
    conditions = tuple(
        Condition(key, domain, value, ConditionBasis.SELECTED, DECISION)
        for key, domain, value in categories
    ) + (
        Condition("energy", Domain.ENVIRONMENT, 2.0, ConditionBasis.SELECTED,
                  DECISION, "toy-energy-unit", 0.1),
        Condition("observation-window", Domain.CONTROL, 10.0,
                  ConditionBasis.SELECTED, DECISION, "s", 0.0),
    )
    rules = tuple(
        Constraint(key, domain, DECISION, equals=value)
        for key, domain, value in categories
    ) + (
        Constraint("energy", Domain.ENVIRONMENT, DECISION,
                   lower=1.0, upper=3.0, unit="toy-energy-unit"),
        Constraint("observation-window", Domain.CONTROL, DECISION,
                   lower=10.0, upper=10.0, unit="s"),
    )
    context = Context(
        "toy-cell", "1", "CONSTRUCTED synthetic cell; no observed physics",
        "synthetic-anchor-digest-v1", conditions,
        "Energy bound +/-0.1 toy unit; synthetic fixed 10 s observation window; "
        "no inference of permanent organization.",
    )
    model = Description("description-A", "1", "toy finite-window return behaviour",
                        rules, DECISION)
    return model, context


def support(model: Description, context: Context, label: str = "synthetic-support") -> Assessment:
    return Assessment(
        label, model.digest(), context.digest(), EvidenceKind.EMPIRICAL,
        Judgment.SUPPORTS, DECISION,
        (EvidenceRef("constructed-fixture", f"applicability/example.py:{label}"),),
        "Synthetic judgment only. No empirical adequacy or instrument sensitivity established.",
    )


def example_map() -> ApplicabilityMap:
    a, centre = fixture()
    b = replace(a, model_id="description-B")
    overlap = replace(
        centre, context_id="toy-cell-overlap", revision="2",
        conditions=tuple(replace(c, value=2.5) if c.key == "energy" else c
                         for c in centre.conditions),
    )
    edge = replace(
        centre, context_id="toy-cell-edge",
        conditions=tuple(replace(c, value=3.0) if c.key == "energy" else c
                         for c in centre.conditions),
    )
    outside = replace(
        centre, context_id="toy-cell-outside",
        conditions=tuple(replace(c, value=5.0) if c.key == "energy" else c
                         for c in centre.conditions),
    )
    # Both descriptions have support at the centre; at overlap only B has
    # support. A's domain includes overlap, but evidence must not transfer.
    evidence = (
        support(a, centre, "A-centre"),
        support(b, centre, "B-centre"),
        support(b, overlap, "B-overlap"),
    )
    return build_map((a, b), (centre, overlap, edge, outside), evidence)


if __name__ == "__main__":
    print(example_map().to_json())
