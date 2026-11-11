"""Closed finite-graph bond backend, called only through diagnostic substitution.

The declared graph is a selected mathematical object, not evidence of physical
coupling. A supplied mask describes one configuration; the independent uniform
bond ensemble at p is a separate mathematical question, not a claim that this
mask was sampled at p. Enumeration is exhaustive, arithmetic is floating point.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping

from ..applicability.mapping import Constraint, Decision, Description, Domain
from ..failures import EvidenceRef
from ..validation.numeric_contract import finite_number
from .adapter import InputPort, _name, _text, digest_record


ENGINE_VERSION = "finite-undirected-bond-enumeration/1"
OCCUPATION_LAW = "independent-uniform-bonds"
MAX_NODES = 32
MAX_EDGES = 12
METRICS = (
    "spanning", "component_count", "largest_component_size", "occupied_edge_count",
    "spanning_probability", "expected_component_count", "expected_largest_component_size",
)


def _refs(evidence: tuple[EvidenceRef, ...]) -> None:
    if not isinstance(evidence, tuple) or not evidence:
        raise ValueError("immutable nonempty evidence references required")
    for ref in evidence:
        if not isinstance(ref, EvidenceRef):
            raise ValueError("typed evidence references required")
        _text(ref.kind)
        _text(ref.locator)


@dataclass(frozen=True)
class FiniteGraph:
    """Edge order defines mask bits; node order defines canonical component labels.

    Spanning means at least one occupied path joins ANY source to ANY target.
    Self-loops, duplicate/reversed duplicate edges, and overlapping boundary
    sets are rejected rather than assigned hidden conventions.
    """

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        if (not isinstance(self.nodes, tuple) or not 2 <= len(self.nodes) <= MAX_NODES
                or any(not isinstance(n, str) or not n.strip() for n in self.nodes)
                or len(set(self.nodes)) != len(self.nodes)):
            raise ValueError(f"2..{MAX_NODES} unique immutable node labels required")
        if not isinstance(self.edges, tuple) or len(self.edges) > MAX_EDGES:
            raise ValueError(f"immutable edge tuple, at most {MAX_EDGES} edges required")
        seen = set()
        for edge in self.edges:
            if (not isinstance(edge, tuple) or len(edge) != 2
                    or any(not isinstance(n, str) or n not in self.nodes for n in edge)
                    or edge[0] == edge[1]):
                raise ValueError("edges must join two distinct declared nodes")
            key = frozenset(edge)
            if key in seen:
                raise ValueError("duplicate undirected edge")
            seen.add(key)
        for boundary in (self.sources, self.targets):
            if (not isinstance(boundary, tuple) or not boundary
                    or any(not isinstance(n, str) or n not in self.nodes for n in boundary)
                    or len(set(boundary)) != len(boundary)):
                raise ValueError("nonempty unique boundary subsets required")
        if set(self.sources) & set(self.targets):
            raise ValueError("source and target sets must be disjoint")
        if not isinstance(self.decision, Decision):
            raise ValueError("graph/boundary selection provenance required")
        _refs(self.evidence)

    def digest(self) -> str:
        return digest_record(self)


@dataclass(frozen=True)
class MetricPort:
    """A built-in graph metric, not a Python callable or an expression hook."""

    name: str
    unit: str = "1"

    def __post_init__(self):
        _name(self.name)
        if self.unit != "1":
            raise ValueError("finite-graph metrics use dimensionless declared units")


@dataclass(frozen=True)
class BondPercolation:
    equation_id: str
    revision: str
    graph: FiniteGraph
    constraints: tuple[Constraint, ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]
    assumptions: tuple[str, ...] = ()  # unresolved assumptions still block execution
    unknown_dependencies: tuple[str, ...] = ()
    engine: str = ENGINE_VERSION
    occupation_law: str = OCCUPATION_LAW

    def __post_init__(self):
        _text(self.equation_id)
        _text(self.revision)
        if type(self.graph) is not FiniteGraph or not isinstance(self.decision, Decision):
            raise ValueError("exact built-in finite graph and selection Decision required")
        if self.engine != ENGINE_VERSION or self.occupation_law != OCCUPATION_LAW:
            raise ValueError("unsupported graph engine or occupation law")
        _refs(self.evidence)
        if not isinstance(self.constraints, tuple) or any(
            not isinstance(c, Constraint) for c in self.constraints
        ):
            raise ValueError("immutable typed applicability criteria required")
        self._description("schema-check")
        rules = {c.key: c for c in self.constraints}
        for key, value in (("graph", self.graph.digest()), ("occupation_law", OCCUPATION_LAW)):
            r = rules.get(key)
            if r is None or r.domain is not Domain.RELATIONSHIPS or r.equals != value:
                raise ValueError(f"{key}: exact graph/law relationship criterion required")
        for key, domain, upper in (
            ("bond_probability", Domain.CONTROL, 1),
            ("occupation_mask", Domain.RELATIONSHIPS, (1 << len(self.graph.edges)) - 1),
        ):
            r = rules.get(key)
            if (r is None or r.domain is not domain or r.equals is not None
                    or r.unit != "1" or not 0 <= r.lower <= r.upper <= upper):
                raise ValueError(f"{key}: explicit bounded dimensionless criterion required")

    @property
    def inputs(self) -> tuple[InputPort, ...]:
        return (
            InputPort("p", "bond_probability", "1"),
            InputPort("mask", "occupation_mask", "1"),
        )

    @property
    def outputs(self) -> tuple[MetricPort, ...]:
        return tuple(MetricPort(name) for name in METRICS + tuple(
            f"component_{i}" for i in range(len(self.graph.nodes))
        ))

    @property
    def property(self) -> str:
        return "finite selected-graph connectivity and independent bond-ensemble metrics"

    def digest(self) -> str:
        return digest_record(self)

    def _description(self, binding: str) -> Description:
        return Description(
            self.equation_id, f"{self.revision}@{binding}", self.property,
            self.constraints, self.decision, self.assumptions, self.unknown_dependencies,
        )

    def description(self) -> Description:
        return self._description(self.digest())


def _bond_input_problems(equation: BondPercolation, inputs: Mapping[str, float]) -> list[str]:
    if set(inputs) != {"p", "mask"}:
        return ["bond inputs must cover exactly p and mask"]
    p, mask = inputs["p"], inputs["mask"]
    problems = []
    if not finite_number(p) or not 0 <= p <= 1:
        problems.append("p must be finite and within [0, 1]")
    if (not finite_number(mask) or mask != int(mask)
            or not 0 <= mask < (1 << len(equation.graph.edges))):
        problems.append("mask must be an integer within the declared edge-bit range")
    return problems


def _components(graph: FiniteGraph, mask: int) -> tuple[tuple[int, ...], ...]:
    """Union-find implementation; canonical components include isolated nodes."""
    index = {node: i for i, node in enumerate(graph.nodes)}
    parent = list(range(len(index)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for bit, (a, b) in enumerate(graph.edges):
        if mask & (1 << bit):
            ra, rb = root(index[a]), root(index[b])
            parent[rb] = ra
    groups: dict[int, list[int]] = {}
    for i in range(len(index)):
        groups.setdefault(root(i), []).append(i)
    return tuple(sorted((tuple(group) for group in groups.values()), key=lambda g: g[0]))


def _spans(graph: FiniteGraph, components: tuple[tuple[int, ...], ...]) -> bool:
    for group in components:
        nodes = {graph.nodes[i] for i in group}
        if nodes.intersection(graph.sources) and nodes.intersection(graph.targets):
            return True
    return False


def _calculate_bonds(equation: BondPercolation, inputs: Mapping[str, float]) -> dict[str, float]:
    """Private primitive. The supported path remains substitution.execute()."""
    problems = _bond_input_problems(equation, inputs)
    if problems:
        raise ValueError("; ".join(problems))
    graph, p, mask = equation.graph, float(inputs["p"]), int(inputs["mask"])
    components = _components(graph, mask)
    result = {
        "spanning": float(_spans(graph, components)),
        "component_count": float(len(components)),
        "largest_component_size": float(max(map(len, components))),
        "occupied_edge_count": float(mask.bit_count()),
    }
    for group in components:
        for node in group:
            result[f"component_{node}"] = float(group[0])
    terms: list[tuple[float, float, float]] = []
    m = len(graph.edges)
    for state in range(1 << m):
        occupied = state.bit_count()
        weight = p ** occupied * (1 - p) ** (m - occupied)
        partition = _components(graph, state)
        terms.append((
            weight * float(_spans(graph, partition)),
            weight * len(partition),
            weight * max(map(len, partition)),
        ))
    for column, name in enumerate((
        "spanning_probability", "expected_component_count", "expected_largest_component_size",
    )):
        result[name] = math.fsum(term[column] for term in terms)
    return result
