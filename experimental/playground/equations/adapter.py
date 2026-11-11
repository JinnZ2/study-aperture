"""Versioned closed adapters; no eval, subclass plugins, or arbitrary callbacks.

Bounded arithmetic, finite bonds and finite branching are separately versioned.
This is not a dimensional-analysis engine.
Declared units and evidence references are recorded, not proved correct.
Only the substitution runner is the supported experimental execution API.
"""

from __future__ import annotations

import ast
import enum
import hashlib
import json
import operator
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Mapping

from ..applicability.mapping import Constraint, Decision, Description
from ..failures import EvidenceRef
from ..validation.numeric_contract import finite_number, finite_outputs

if TYPE_CHECKING:
    from .branching import FiniteBranching
    from .percolation import BondPercolation


ENGINE_VERSION = "bounded-arithmetic/1"
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow}


def digest_record(record: object) -> str:
    return hashlib.sha256(json.dumps(
        asdict(record), sort_keys=True, separators=(",", ":"), allow_nan=False,
        default=lambda value: value.value if isinstance(value, enum.Enum) else value,
    ).encode()).hexdigest()


def _name(value: str) -> None:
    if not isinstance(value, str) or not value.isidentifier() or value.startswith("_"):
        raise ValueError("ports require public identifier names")


def _text(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("nonempty text required")


def _expression(expression: str, names: set[str]) -> ast.expr:
    _text(expression)
    if len(expression) > 4096:
        raise ValueError("expression exceeds 4096 characters")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise ValueError("invalid arithmetic expression") from exc
    if len(tuple(ast.walk(tree))) > 256:
        raise ValueError("expression exceeds 256 AST nodes")

    def check(node, depth=0):
        if depth > 32:
            raise ValueError("expression exceeds nesting limit")
        if isinstance(node, ast.Constant) and finite_number(node.value):
            return
        if isinstance(node, ast.Name) and node.id in names:
            return
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            check(node.operand, depth + 1)
            return
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            check(node.left, depth + 1)
            check(node.right, depth + 1)
            return
        raise ValueError("only declared inputs and bounded real arithmetic are allowed")

    check(tree.body)
    return tree.body


@dataclass(frozen=True)
class InputPort:
    name: str
    context_key: str
    unit: str  # explicit "1" for dimensionless

    def __post_init__(self):
        _name(self.name)
        _text(self.context_key)
        _text(self.unit)


@dataclass(frozen=True)
class OutputPort:
    name: str
    expression: str
    unit: str

    def __post_init__(self):
        _name(self.name)
        _text(self.expression)
        _text(self.unit)


@dataclass(frozen=True)
class Equation:
    equation_id: str
    revision: str
    property: str
    inputs: tuple[InputPort, ...]
    outputs: tuple[OutputPort, ...]
    constraints: tuple[Constraint, ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]
    assumptions: tuple[str, ...] = ()
    unknown_dependencies: tuple[str, ...] = ()
    engine: str = ENGINE_VERSION

    def __post_init__(self):
        for value in (self.equation_id, self.revision, self.property):
            _text(value)
        if self.engine != ENGINE_VERSION:
            raise ValueError("unsupported arithmetic engine version")
        if not isinstance(self.decision, Decision):
            raise ValueError("equation selection needs a Decision")
        for values, kind in ((self.inputs, InputPort), (self.outputs, OutputPort),
                             (self.constraints, Constraint), (self.evidence, EvidenceRef)):
            if not isinstance(values, tuple) or not values or any(
                not isinstance(value, kind) for value in values
            ):
                raise ValueError(f"nonempty immutable tuple of {kind.__name__} required")
        for ref in self.evidence:
            _text(ref.kind)
            _text(ref.locator)
        for ports in (self.inputs, self.outputs):
            if len({p.name for p in ports}) != len(ports):
                raise ValueError("duplicate port names")
        for output in self.outputs:
            _expression(output.expression, {p.name for p in self.inputs})
        # Reuse the scoped description schema for constraint/provenance validation.
        self._description("schema-check")

    def digest(self) -> str:
        return digest_record(self)

    def _description(self, binding: str) -> Description:
        return Description(
            self.equation_id, f"{self.revision}@{binding}", self.property,
            self.constraints, self.decision, self.assumptions, self.unknown_dependencies,
        )

    def description(self) -> Description:
        """Bind physical assessments to the actual adapter definition, not just its label."""
        return self._description(self.digest())


class EquationRegistry:
    """Explicit selection only; no latest-version resolution or in-place replacement."""

    def __init__(self):
        self._equations: dict[tuple[str, str], Equation | BondPercolation | FiniteBranching] = {}

    def register(self, equation: Equation | BondPercolation | FiniteBranching) -> None:
        from .branching import FiniteBranching
        from .percolation import BondPercolation

        if type(equation) not in (Equation, BondPercolation, FiniteBranching):
            raise ValueError("only exact built-in declarative adapter types can be registered")
        key = (equation.equation_id, equation.revision)
        if key in self._equations:
            raise ValueError("equation identity/revision already registered; issue a new revision")
        self._equations[key] = equation

    def select(self, equation_id: str, revision: str) -> Equation | BondPercolation | FiniteBranching:
        return self._equations[(equation_id, revision)]


def _input_problems(
    equation: Equation | BondPercolation | FiniteBranching, inputs: Mapping[str, float],
) -> list[str]:
    """Additional closed-backend design criteria, checked before any evaluation."""
    from .branching import FiniteBranching, _branch_input_problems
    from .percolation import BondPercolation, _bond_input_problems

    if type(equation) is FiniteBranching:
        return _branch_input_problems(equation, inputs)
    if type(equation) is BondPercolation:
        return _bond_input_problems(equation, inputs)
    if type(equation) is not Equation:
        return ["unsupported adapter type"]
    return []


def _calculate(
    equation: Equation | BondPercolation | FiniteBranching, inputs: Mapping[str, float],
) -> dict[str, float]:
    """Private numerical primitive, not an alternate experimental execution path."""
    from .branching import FiniteBranching, _calculate_branching
    from .percolation import BondPercolation, _calculate_bonds

    if type(equation) is FiniteBranching:
        result = finite_outputs(_calculate_branching(equation, inputs))
        if set(result) != {p.name for p in equation.outputs}:
            raise ValueError("branching backend output names do not exactly cover its metric ports")
        return result
    if type(equation) is BondPercolation:
        result = finite_outputs(_calculate_bonds(equation, inputs))
        if set(result) != {p.name for p in equation.outputs}:
            raise ValueError("graph backend output names do not exactly cover its metric ports")
        return result
    if type(equation) is not Equation:
        raise ValueError("unsupported adapter type")
    if set(inputs) != {p.name for p in equation.inputs}:
        raise ValueError("input names do not exactly cover the adapter ports")
    if any(not finite_number(value) for value in inputs.values()):
        raise ValueError("non-finite/non-real input")
    values = {key: float(value) for key, value in inputs.items()}

    def compute(node):
        if isinstance(node, ast.Name):
            value = values[node.id]
        elif isinstance(node, ast.Constant):
            value = float(node.value)
        elif isinstance(node, ast.UnaryOp):
            operand = compute(node.operand)
            value = -operand if isinstance(node.op, ast.USub) else operand
        else:
            left, right = compute(node.left), compute(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("power exponent exceeds engine bound")
            value = _OPS[type(node.op)](left, right)
        if not finite_number(value):
            raise ValueError("non-finite or non-real intermediate")
        return float(value)

    return finite_outputs({
        output.name: compute(_expression(output.expression, set(values)))
        for output in equation.outputs
    })
