"""Closed finite-horizon branching backend under diagnostic substitution.

Independent identically distributed single-type offspring, discrete generations,
no immigration or interaction. These are selected mathematical definitions,
not empirical facts. Entire finite-generation distributions are represented;
no population tail is truncated or renormalized.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping

from ..applicability.mapping import Constraint, Decision, Description, Domain
from ..failures import EvidenceRef
from ..validation.numeric_contract import finite_number
from .adapter import InputPort, _name, _text, digest_record


ENGINE_VERSION = "finite-iid-single-type-branching/1"
BRANCHING_DEFINITION = "iid-single-type-discrete-generations-no-immigration-no-interaction"
MAX_OFFSPRING = 4
MAX_TOTAL_WEIGHT = 1_000_000
MAX_INITIAL_POPULATION = 4
MAX_GENERATIONS = 8
MAX_POPULATION = 128
METRICS = (
    "offspring_mean", "offspring_variance", "expected_population", "population_variance",
    "extinction_by_horizon", "survival_at_horizon", "expected_cumulative_population",
    "probability_mass",
)


def _evidence(refs: tuple[EvidenceRef, ...]) -> None:
    if not isinstance(refs, tuple) or not refs:
        raise ValueError("immutable nonempty evidence references required")
    for ref in refs:
        if not isinstance(ref, EvidenceRef):
            raise ValueError("typed evidence references required")
        _text(ref.kind)
        _text(ref.locator)


@dataclass(frozen=True)
class OffspringLaw:
    """P(K=k)=weight(k)/sum(weights); positive integer weights define exact ratios.

    The weights are selected model parameters, NOT claimed empirical counts.
    Unlisted outcomes have zero probability within this mathematical definition.
    """

    weights: tuple[tuple[int, int], ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        if not isinstance(self.weights, tuple) or not self.weights:
            raise ValueError("a nonempty immutable offspring law is required")
        counts = set()
        total = 0
        for pair in self.weights:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError("immutable (offspring_count, positive_integer_weight) pairs required")
            count, weight = pair
            if (type(count) is not int or not 0 <= count <= MAX_OFFSPRING
                    or type(weight) is not int or not 1 <= weight <= MAX_TOTAL_WEIGHT
                    or count in counts):
                raise ValueError("unique bounded offspring counts and positive bounded integer weights required")
            counts.add(count)
            total += weight
        if total > MAX_TOTAL_WEIGHT:
            raise ValueError("total offspring weight exceeds the backend bound")
        if not isinstance(self.decision, Decision):
            raise ValueError("offspring-law selection provenance required")
        _evidence(self.evidence)

    @property
    def max_offspring(self) -> int:
        return max(count for count, _ in self.weights)

    def digest(self) -> str:
        return digest_record(self)


@dataclass(frozen=True)
class BranchMetric:
    name: str
    unit: str = "1"

    def __post_init__(self):
        _name(self.name)
        if self.unit != "1":
            raise ValueError("branching metrics have explicit dimensionless units")


@dataclass(frozen=True)
class FiniteBranching:
    equation_id: str
    revision: str
    law: OffspringLaw
    constraints: tuple[Constraint, ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]
    assumptions: tuple[str, ...] = ()
    unknown_dependencies: tuple[str, ...] = ()
    engine: str = ENGINE_VERSION
    definition: str = BRANCHING_DEFINITION

    def __post_init__(self):
        _text(self.equation_id)
        _text(self.revision)
        if type(self.law) is not OffspringLaw or not isinstance(self.decision, Decision):
            raise ValueError("exact built-in offspring law and selection Decision required")
        if self.engine != ENGINE_VERSION or self.definition != BRANCHING_DEFINITION:
            raise ValueError("unsupported branching engine or process definition")
        _evidence(self.evidence)
        if not isinstance(self.constraints, tuple) or any(
            not isinstance(c, Constraint) for c in self.constraints
        ):
            raise ValueError("immutable typed applicability criteria required")
        self._description("schema-check")
        rules = {c.key: c for c in self.constraints}
        for key, value in (("offspring_law", self.law.digest()),
                           ("branching_definition", BRANCHING_DEFINITION)):
            r = rules.get(key)
            if r is None or r.domain is not Domain.RELATIONSHIPS or r.equals != value:
                raise ValueError(f"{key}: exact relationship criterion required")
        for key, upper in (("initial_population", MAX_INITIAL_POPULATION),
                           ("generation_horizon", MAX_GENERATIONS)):
            r = rules.get(key)
            if (r is None or r.domain is not Domain.CONTROL or r.equals is not None
                    or r.unit != "1" or not 0 <= r.lower <= r.upper <= upper):
                raise ValueError(f"{key}: explicit bounded dimensionless control criterion required")

    @property
    def inputs(self) -> tuple[InputPort, ...]:
        return (InputPort("initial", "initial_population", "1"),
                InputPort("generations", "generation_horizon", "1"))

    @property
    def outputs(self) -> tuple[BranchMetric, ...]:
        return tuple(BranchMetric(name) for name in METRICS + tuple(
            f"population_probability_{i}" for i in range(MAX_POPULATION + 1)
        ))

    @property
    def property(self) -> str:
        return "selected finite-generation branching population distribution and extinction probabilities"

    def digest(self) -> str:
        return digest_record(self)

    def _description(self, binding: str) -> Description:
        return Description(
            self.equation_id, f"{self.revision}@{binding}", self.property,
            self.constraints, self.decision, self.assumptions, self.unknown_dependencies,
        )

    def description(self) -> Description:
        return self._description(self.digest())


def _branch_input_problems(equation: FiniteBranching, inputs: Mapping[str, float]) -> list[str]:
    if set(inputs) != {"initial", "generations"}:
        return ["branching inputs must cover exactly initial and generations"]
    problems = []
    for key, maximum in (("initial", MAX_INITIAL_POPULATION), ("generations", MAX_GENERATIONS)):
        value = inputs[key]
        if not finite_number(value) or value != int(value) or not 0 <= value <= maximum:
            problems.append(f"{key}: bounded nonnegative integer required")
    if not problems:
        initial, generations = int(inputs["initial"]), int(inputs["generations"])
        if initial * equation.law.max_offspring ** generations > MAX_POPULATION:
            problems.append("complete finite-generation support exceeds backend bound; no tail truncation allowed")
    return problems


def _convolve(a: list[int], b: list[int]) -> list[int]:
    """Multiply probability polynomials without tail dropping or normalization."""
    terms = [0] * (len(a) + len(b) - 1)
    for i, left in enumerate(a):
        for j, right in enumerate(b):
            terms[i + j] += left * right
    return terms


def _power(poly: list[int], exponent: int) -> list[int]:
    result = [1]
    for _ in range(exponent):
        result = _convolve(result, poly)
    return result


def _population_distribution(
    equation: FiniteBranching, initial: int, generations: int,
) -> tuple[list[int], int]:
    if initial == 0:
        return [1], 1
    # PGF of generation zero descended from one founder is s, not 1.
    distribution, denominator = [0, 1], 1
    total_weight = sum(weight for _, weight in equation.law.weights)
    for _ in range(generations):
        terms = [0] * ((len(distribution) - 1) * equation.law.max_offspring + 1)
        for offspring, weight in equation.law.weights:
            scale = weight * denominator ** (equation.law.max_offspring - offspring)
            for i, coefficient in enumerate(_power(distribution, offspring)):
                terms[i] += scale * coefficient
        denominator = total_weight * denominator ** equation.law.max_offspring
        distribution = terms
    return _power(distribution, initial), denominator ** initial


def _calculate_branching(equation: FiniteBranching, inputs: Mapping[str, float]) -> dict[str, float]:
    """Private numerical primitive; execute() remains the supported lab path."""
    problems = _branch_input_problems(equation, inputs)
    if problems:
        raise ValueError("; ".join(problems))
    initial, generations = int(inputs["initial"]), int(inputs["generations"])
    numerators, denominator = _population_distribution(equation, initial, generations)
    if (type(denominator) is not int or denominator <= 0
            or not numerators or len(numerators) > MAX_POPULATION + 1
            or any(type(p) is not int or p < 0 for p in numerators)):
        raise ValueError("invalid or oversized population distribution")
    if sum(numerators) != denominator:
        raise ValueError("probability mass lost; no automatic renormalization")

    def ratio(numerator, divisor):
        value = numerator / divisor
        if not finite_number(value) or (numerator > 0 and value == 0):
            raise ValueError("positive exact quantity cannot be represented by the float output; underflow")
        return value

    population = [ratio(p, denominator) for p in numerators]
    total_weight = sum(w for _, w in equation.law.weights)
    mean_numerator = sum(k * w for k, w in equation.law.weights)
    second_offspring = sum(k * k * w for k, w in equation.law.weights)
    expected_numerator = sum(k * p for k, p in enumerate(numerators))
    second_population = sum(k * k * p for k, p in enumerate(numerators))
    mean = Fraction(mean_numerator, total_weight)
    cumulative = sum((initial * mean ** n for n in range(generations + 1)), Fraction(0))
    result = dict(
        offspring_mean=ratio(mean_numerator, total_weight),
        offspring_variance=ratio(second_offspring * total_weight - mean_numerator ** 2,
                                 total_weight ** 2),
        expected_population=ratio(expected_numerator, denominator),
        population_variance=ratio(second_population * denominator - expected_numerator ** 2,
                                  denominator ** 2),
        extinction_by_horizon=population[0],
        # Sum exact surviving states, rather than canceling tiny survival in 1-q.
        survival_at_horizon=ratio(sum(numerators[1:]), denominator),
        expected_cumulative_population=ratio(cumulative.numerator, cumulative.denominator),
        probability_mass=1.0,
    )
    result.update({
        f"population_probability_{k}": population[k] if k < len(population) else 0.0
        for k in range(MAX_POPULATION + 1)
    })
    return result
