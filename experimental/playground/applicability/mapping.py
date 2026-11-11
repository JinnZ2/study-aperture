"""Map recorded assessments to exact contexts without manufacturing support.

Membership in a declared domain is not physical adequacy. Adequacy judgments
are explicit assessor inputs with evidence references, not computed from
equations, diagnostic success, boundary choices, or neighbouring map cells.
Numeric uncertainty uses bounded intervals, not probabilities. Matching uses
explicit units, no conversions, no interpolation, and no universal ranking.
"""

from __future__ import annotations

import enum
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Mapping

from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..lifecycle.reevaluation import stale_reliance
from ..lifecycle.unknown_expiry import UnknownState


class Domain(str, enum.Enum):
    BOUNDARY = "boundary"
    CONTROL = "control"
    OBSERVER = "observer"
    ENVIRONMENT = "environment"
    RELATIONSHIPS = "relationships"
    UNCERTAINTY = "uncertainty"
    ANCHOR = "anchor"


class ConditionBasis(str, enum.Enum):
    SELECTED = "selected"
    ASSUMED = "assumed"
    MEASURED = "measured"
    DERIVED = "derived"


class ScopeState(str, enum.Enum):
    INSIDE = "inside-declared-domain"
    OUTSIDE = "outside-declared-domain"
    UNKNOWN = "unresolved-domain-membership"


class ApplicabilityState(str, enum.Enum):
    SUPPORTED = "supported-within-recorded-context"
    CONTRADICTED = "contradicted-within-recorded-context"
    CONFLICTING = "conflicting-evidence"
    UNKNOWN = "unknown"
    OUTSIDE = "outside-declared-domain"
    BLOCKED = "blocked-determination"


class EvidenceKind(str, enum.Enum):
    MATHEMATICAL = "mathematical-consistency"
    DIAGNOSTIC = "diagnostic-validity"
    PHYSICAL = "physical-adequacy"
    EMPIRICAL = "empirical-agreement"


class Judgment(str, enum.Enum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    UNRESOLVED = "unresolved"


def _text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be nonempty text")


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _unique(values: tuple, field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"duplicate {field}")


def _tuple_of(values: tuple, item_type: type, field: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(v, item_type) for v in values):
        raise ValueError(f"{field} must be an immutable tuple of {item_type.__name__}")


def _evidence(values: tuple[EvidenceRef, ...]) -> None:
    _tuple_of(values, EvidenceRef, "evidence")
    for ref in values:
        _text(ref.kind, "evidence kind")
        _text(ref.locator, "evidence locator")


@dataclass(frozen=True)
class Decision:
    """Who selected this scope, why, and according to which criteria."""

    chosen_by: str
    rationale: str
    criteria: str

    def __post_init__(self) -> None:
        for name in ("chosen_by", "rationale", "criteria"):
            _text(getattr(self, name), name)


@dataclass(frozen=True)
class Condition:
    key: str
    domain: Domain
    value: str | float | None
    basis: ConditionBasis
    decision: Decision
    unit: str = ""
    uncertainty: float | None = None  # numeric bounded half-width; None is unknown
    evidence: tuple[EvidenceRef, ...] = ()

    def __post_init__(self) -> None:
        _text(self.key, "condition key")
        if not isinstance(self.decision, Decision):
            raise ValueError("condition selection requires a Decision")
        _evidence(self.evidence)
        if not isinstance(self.domain, Domain) or not isinstance(self.basis, ConditionBasis):
            raise ValueError("condition domain and basis must be typed enums")
        if self.value is not None and not isinstance(self.value, str) and not _number(self.value):
            raise ValueError("condition value must be text, finite number, or None")
        if self.uncertainty is not None:
            if not _number(self.value) or not _number(self.uncertainty) or self.uncertainty < 0:
                raise ValueError("uncertainty requires a finite numeric value and nonnegative bound")
        if _number(self.value) and self.uncertainty is not None:
            if not all(math.isfinite(v) for v in (
                self.value - self.uncertainty, self.value + self.uncertainty
            )):
                raise ValueError("uncertainty interval must be finite")
        if self.basis in (ConditionBasis.MEASURED, ConditionBasis.DERIVED) and not self.evidence:
            raise ValueError("measured/derived conditions require evidence references")


@dataclass(frozen=True)
class Context:
    context_id: str
    revision: str
    system_description: str
    anchor_digest: str
    conditions: tuple[Condition, ...]
    uncertainty_notes: str

    def __post_init__(self) -> None:
        for name in ("context_id", "revision", "system_description", "anchor_digest",
                     "uncertainty_notes"):
            _text(getattr(self, name), name)
        _tuple_of(self.conditions, Condition, "conditions")
        _unique(tuple(c.key for c in self.conditions), "context keys")

    def digest(self) -> str:
        """Bind content, provenance, scope, uncertainty and anchor, not just a label."""
        payload = asdict(self)
        payload["conditions"] = sorted(payload["conditions"], key=lambda c: c["key"])
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()).hexdigest()


@dataclass(frozen=True)
class Constraint:
    """Exactly one categorical equality or a closed numeric interval.

    Limits are selected applicability conditions, not independently established
    physical facts. Units must match literally; callers perform and document
    conversions before constructing the context.
    """

    key: str
    domain: Domain
    decision: Decision
    equals: str | None = None
    lower: float | None = None
    upper: float | None = None
    unit: str = ""

    def __post_init__(self) -> None:
        _text(self.key, "constraint key")
        if not isinstance(self.decision, Decision):
            raise ValueError("constraint selection requires a Decision")
        if not isinstance(self.domain, Domain):
            raise ValueError("constraint domain must be a Domain")
        if self.equals is not None:
            _text(self.equals, "equals")
            if self.lower is not None or self.upper is not None:
                raise ValueError("equality and numeric bounds are mutually exclusive")
        elif not _number(self.lower) or not _number(self.upper) or self.lower > self.upper:
            raise ValueError("numeric constraints need finite ordered lower and upper bounds")

    def cessation(self) -> str:
        rule = repr(self.equals) if self.equals is not None else (
            f"[{self.lower:g}, {self.upper:g}] {self.unit}"
        )
        return f"Reassess if {self.domain.value}:{self.key} leaves {rule} or its uncertainty changes."


@dataclass(frozen=True)
class Description:
    model_id: str
    revision: str
    property: str  # the particular behaviour/property being assessed
    constraints: tuple[Constraint, ...]
    decision: Decision
    assumptions: tuple[str, ...] = ()
    unknown_dependencies: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("model_id", "revision", "property"):
            _text(getattr(self, name), name)
        if not isinstance(self.decision, Decision):
            raise ValueError("description selection requires a Decision")
        _tuple_of(self.constraints, Constraint, "constraints")
        _tuple_of(self.assumptions, str, "assumptions")
        _tuple_of(self.unknown_dependencies, str, "unknown_dependencies")
        for text in self.assumptions + self.unknown_dependencies:
            _text(text, "assumption/dependency")
        _unique(tuple(c.key for c in self.constraints), "constraint keys")
        _unique(self.unknown_dependencies, "dependency IDs")

    def digest(self) -> str:
        payload = asdict(self)
        payload["constraints"] = sorted(payload["constraints"], key=lambda c: c["key"])
        return hashlib.sha256(json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()).hexdigest()


@dataclass(frozen=True)
class Assessment:
    """An explicit, scoped judgment, never a judgment inferred by this module."""

    assessment_id: str
    description_digest: str
    context_digest: str
    kind: EvidenceKind
    judgment: Judgment
    decision: Decision
    evidence: tuple[EvidenceRef, ...]
    uncertainty: str
    record: FailureRecord = FailureRecord()

    def __post_init__(self) -> None:
        for name in ("assessment_id", "description_digest", "context_digest", "uncertainty"):
            _text(getattr(self, name), name)
        if not isinstance(self.decision, Decision) or not isinstance(self.record, FailureRecord):
            raise ValueError("assessment requires a Decision and FailureRecord")
        _evidence(self.evidence)
        if not isinstance(self.kind, EvidenceKind) or not isinstance(self.judgment, Judgment):
            raise ValueError("assessment kind and judgment must be typed enums")
        if not self.evidence:
            raise ValueError("assessments require nonempty evidence references")


@dataclass(frozen=True)
class ConditionMatch:
    constraint: Constraint
    condition: Condition | None
    state: ScopeState
    reason: str


def _match(rule: Constraint, value: Condition | None) -> ConditionMatch:
    state = ScopeState.UNKNOWN
    reason = "condition not declared or value unresolved"
    if value is not None and value.value is not None:
        if value.domain is not rule.domain or value.unit != rule.unit:
            reason = "domain/unit mismatch; no implicit conversion"
        elif rule.equals is not None:
            if not isinstance(value.value, str):
                reason = "categorical constraint cannot compare numeric value"
            else:
                state = ScopeState.INSIDE if value.value == rule.equals else ScopeState.OUTSIDE
                reason = "literal categorical comparison"
        elif not _number(value.value):
            reason = "numeric constraint cannot compare categorical value"
        elif value.uncertainty is None:
            reason = "numeric uncertainty bound not established"
        else:
            lo, hi = value.value - value.uncertainty, value.value + value.uncertainty
            if rule.lower <= lo and hi <= rule.upper:
                state, reason = ScopeState.INSIDE, "entire uncertainty interval inside bounds"
            elif hi < rule.lower or lo > rule.upper:
                state, reason = ScopeState.OUTSIDE, "entire uncertainty interval outside bounds"
            else:
                reason = "uncertainty interval straddles applicability boundary"
    return ConditionMatch(rule, value, state, reason)


@dataclass(frozen=True)
class ApplicabilityResult:
    description: Description
    context: Context
    scope: ScopeState
    state: ApplicabilityState
    matches: tuple[ConditionMatch, ...]
    assessments: tuple[Assessment, ...]
    excluded_assessment_ids: tuple[str, ...]
    record: FailureRecord
    unresolved: tuple[str, ...]
    dependency_states: tuple[tuple[str, str], ...]
    # These indicate possible revision triggers, not physical transition events.
    ceases_to_hold: tuple[str, ...]


def _finding(code: str, severity: Status, message: str) -> Finding:
    return Finding(Axis.DETERMINATION, severity, code, message, "applicability.mapping")


def assess(
    description: Description,
    context: Context,
    assessments: tuple[Assessment, ...] = (),
    diagnostics: FailureRecord = FailureRecord(),
    dependency_states: Mapping[str, UnknownState] | None = None,
) -> ApplicabilityResult:
    """Evaluate one property, description revision and exact experimental context.

    UNKNOWN dependencies remain unresolved even when someone supplies a
    favourable assessment. Missing dependencies also remain unknown. Expired
    dependencies block the determination, without declaring the model false.
    Diagnostics must belong to this invocation/context; supplied records are
    retained verbatim and are never interpreted as empirical support.
    """
    _unique(tuple(a.assessment_id for a in assessments), "assessment IDs")
    values = {c.key: c for c in context.conditions}
    matches = tuple(_match(rule, values.get(rule.key)) for rule in description.constraints)
    unresolved = [
        f"{m.constraint.key}: {m.reason}" for m in matches if m.state is ScopeState.UNKNOWN
    ]
    # Every determination coordinate must be explicit. An empty rule set is
    # not an implicit universally applicable description.
    for domain in Domain:
        if not any(c.domain is domain for c in context.conditions):
            unresolved.append(f"context has no {domain.value} coordinate")
        if not any(c.domain is domain for c in description.constraints):
            unresolved.append(f"description has no {domain.value} applicability criterion")
    assumptions = [
        f"assumed condition {c.key}={c.value!r}"
        for c in context.conditions if c.basis is ConditionBasis.ASSUMED
    ]
    unresolved.extend(assumptions)
    unresolved.extend(f"unresolved model assumption: {a}" for a in description.assumptions)
    unresolved.extend(
        f"condition {c.key}: value unresolved"
        for c in context.conditions if c.value is None
    )
    scope = (
        ScopeState.OUTSIDE if any(m.state is ScopeState.OUTSIDE for m in matches)
        else ScopeState.UNKNOWN if unresolved else ScopeState.INSIDE
    )

    dd, cd = description.digest(), context.digest()
    bound = tuple(a for a in assessments if a.description_digest == dd and a.context_digest == cd)
    excluded = tuple(a.assessment_id for a in assessments if a not in bound)
    record = diagnostics
    for a in bound:
        record = record.merge(a.record)
    states = dependency_states or {}
    current = {}
    for dep in description.unknown_dependencies:
        if dep not in states:
            unresolved.append(f"dependency {dep}: state not supplied")
        else:
            if not isinstance(states[dep], UnknownState):
                raise ValueError("dependency states must be UnknownState values")
            current[dep] = states[dep]
            if states[dep] is UnknownState.UNKNOWN:
                unresolved.append(f"dependency {dep}: still UNKNOWN")
    record = record.merge(stale_reliance(current))

    if scope is ScopeState.OUTSIDE:
        state = ApplicabilityState.OUTSIDE
        record = record.with_finding(_finding(
            "APP_OUTSIDE_DOMAIN", Status.OK,
            "Outside selected domain; no physical failure or global model verdict follows.",
        ))
    elif record.conclusion_blocked:
        state = ApplicabilityState.BLOCKED
    else:
        if record.physical is Status.FAILED:
            unresolved.append("physical failure finding requires scoped reconciliation")
        for axis in Axis:
            if record.status_for(axis) is Status.INDETERMINATE:
                unresolved.append(f"{axis.value} diagnostic remains indeterminate")
        if unresolved:
            state = ApplicabilityState.UNKNOWN
        else:
            # Neither mathematical nor diagnostic judgments can promote a model.
            relevant = tuple(a for a in bound if a.kind in (
                EvidenceKind.PHYSICAL, EvidenceKind.EMPIRICAL
            ))
            signs = {a.judgment for a in relevant}
            if Judgment.SUPPORTS in signs and Judgment.OPPOSES in signs:
                state = ApplicabilityState.CONFLICTING
            elif Judgment.UNRESOLVED in signs:
                unresolved.append("physical/empirical assessment remains unresolved")
                state = ApplicabilityState.UNKNOWN
            elif Judgment.OPPOSES in signs:
                state = ApplicabilityState.CONTRADICTED
            elif Judgment.SUPPORTS in signs:
                state = ApplicabilityState.SUPPORTED
            else:
                unresolved.append("no bound physical/empirical adequacy assessment")
                state = ApplicabilityState.UNKNOWN
        if state in (ApplicabilityState.UNKNOWN, ApplicabilityState.CONFLICTING):
            record = record.with_finding(_finding(
                "APP_UNRESOLVED", Status.INDETERMINATE,
                "; ".join(unresolved) or "Bound assessments conflict; no tie-break or ranking applied.",
            ))

    return ApplicabilityResult(
        description, context, scope, state, matches, bound, excluded, record,
        tuple(unresolved),
        tuple((dep, states[dep].value if dep in current else "not-supplied")
              for dep in description.unknown_dependencies),
        tuple(c.cessation() for c in description.constraints) + (
            "Reassess if model revision, property, context, anchor, evidence, or dependencies change.",
            "Evidence is bound to this exact context; no interpolation or extrapolation is established.",
        ),
    )


@dataclass(frozen=True)
class ApplicabilityMap:
    """Independent cells; overlapping support is not a universal hierarchy."""

    cells: tuple[ApplicabilityResult, ...]

    def to_dict(self) -> dict:
        """Inspectable stdlib-JSON-compatible report, including evidence and unknowns."""
        payload = {
            "schema": "playground/applicability-map/0.1",
            "limits": [
                "Recorded assessments, not an automated physics verdict.",
                "No ranking, interpolation, extrapolation, or inferred physical transition.",
                "Evidence references are retained but their truth and independence are not verified.",
            ],
            "cells": [
                dict(asdict(c), description_digest=c.description.digest(),
                     context_digest=c.context.digest())
                for c in self.cells
            ],
        }
        return json.loads(json.dumps(
            payload, allow_nan=False,
            default=lambda value: value.value if isinstance(value, enum.Enum) else value,
        ))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, allow_nan=False)


def build_map(
    descriptions: tuple[Description, ...],
    contexts: tuple[Context, ...],
    assessments: tuple[Assessment, ...] = (),
    diagnostics: Mapping[tuple[str, str], FailureRecord] | None = None,
    dependency_states: Mapping[str, UnknownState] | None = None,
) -> ApplicabilityMap:
    """Cartesian product of independently evaluated, digest-bound cells.

    Diagnostic keys are (description.digest(), context.digest()). Cells do
    not inherit evidence or failures from each other. Order is input order,
    not fitness order; multiple descriptions can be supported simultaneously.
    """
    _unique(tuple(d.digest() for d in descriptions), "descriptions")
    _unique(tuple(c.digest() for c in contexts), "contexts")
    _unique(tuple(a.assessment_id for a in assessments), "assessment IDs")
    diagnostics = diagnostics or {}
    return ApplicabilityMap(tuple(
        assess(d, c, assessments, diagnostics.get((d.digest(), c.digest()), FailureRecord()),
               dependency_states)
        for c in contexts for d in descriptions
    ))
