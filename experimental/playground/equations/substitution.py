"""Fail-closed equation substitution through the laboratory diagnostic layers.

Fresh validation is mandatory on every call. No caller-supplied PASS flags,
cached certificates, unbound inputs, or arbitrary Python callables are accepted.
Numerical execution does not change physical support, assert absence, or infer
system continuity. This supported API is not a sandbox against hostile Python.
"""

from __future__ import annotations

import enum
import json
from dataclasses import asdict, dataclass
from typing import Mapping

from ..applicability.mapping import (
    ApplicabilityResult, ApplicabilityState, Assessment, ConditionBasis, Context,
    Decision, Domain, ScopeState, assess,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.gate_results import GateOutcome, GateResult
from ..gates.l0_closure import (
    BoundaryAccounting, Direction, ValueProvenance, l0_closure_gate,
)
from ..lifecycle.unknown_expiry import UnknownState
from ..reference.anchor import AnchorState
from ..validation.known_answer import (
    InstrumentValidation, KnownAnswerCase, validate_known_answers,
)
from ..validation.null_harness import NullCase, NullValidation, validate_nulls
from ..validation.numeric_contract import finite_number, validate_case_data
from .adapter import Equation, EquationRegistry, _calculate, _input_problems, digest_record
from .branching import FiniteBranching
from .percolation import BondPercolation


Adapter = Equation | BondPercolation | FiniteBranching


def _pairs(values: tuple, name: str) -> dict:
    if not isinstance(values, tuple) or any(
        not isinstance(p, tuple) or len(p) != 2 for p in values
    ):
        raise ValueError(f"{name}: immutable pairs required")
    result = dict(values)
    if len(result) != len(values) or any(
        not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip()
        for k, v in result.items()
    ):
        raise ValueError(f"{name}: unique nonempty text pairs required")
    return result


def _record_contract(record: FailureRecord) -> None:
    if not isinstance(record, FailureRecord) or not isinstance(record.findings, tuple):
        raise ValueError("diagnostic findings must be an immutable FailureRecord")
    for f in record.findings:
        if (not isinstance(f, Finding) or not isinstance(f.axis, Axis)
                or not isinstance(f.severity, Status) or not isinstance(f.evidence, tuple)):
            raise ValueError("typed immutable diagnostic findings required")


@dataclass(frozen=True)
class BoundaryProtocol:
    context_digest: str
    anchor_digest: str
    accounting: BoundaryAccounting
    quantity_units: tuple[tuple[str, str], ...]
    intervention_conditions: tuple[tuple[str, str], ...]
    decision: Decision
    boundary_key: str = "boundary"
    anchor_key: str = "anchor"

    def __post_init__(self):
        if not isinstance(self.decision, Decision):
            raise ValueError("boundary protocol requires selection provenance")
        _pairs(self.quantity_units, "quantity_units")
        _pairs(self.intervention_conditions, "intervention_conditions")
        if not isinstance(self.accounting, BoundaryAccounting):
            raise ValueError("boundary protocol requires BoundaryAccounting")
        if type(self.accounting.declared_complete) is not bool:
            raise ValueError("ledger completeness must be an explicit boolean")
        if not isinstance(self.accounting.accounts, tuple) or not self.accounting.accounts:
            raise ValueError("a nonempty immutable boundary ledger is required")
        if not isinstance(self.accounting.registered_interventions, tuple):
            raise ValueError("interventions must be immutable")
        names = [a.quantity for a in self.accounting.accounts]
        if len(set(names)) != len(names):
            raise ValueError("duplicate ledger quantities")
        if set(dict(self.quantity_units)) != set(names):
            raise ValueError("every ledger quantity must have a declared unit")
        for a in self.accounting.accounts:
            if not all(finite_number(v) for v in (a.initial, a.final, a.tolerance)):
                raise ValueError("ledger endpoints and tolerances must be finite numbers")
            if a.tolerance < 0 or not isinstance(a.exchanges, tuple):
                raise ValueError("nonnegative tolerance and immutable exchanges required")
            if not all(isinstance(p, ValueProvenance) for p in (
                a.initial_provenance, a.final_provenance
            )):
                raise ValueError("typed value provenance required")
            for e in a.exchanges:
                if (e.quantity != a.quantity or not finite_number(e.magnitude)
                        or e.magnitude < 0 or not isinstance(e.direction, Direction)
                        or not isinstance(e.provenance, ValueProvenance)):
                    raise ValueError("invalid/misassigned boundary exchange")


@dataclass(frozen=True)
class ExperimentalDiagnostics:
    """Measurement/design findings that remain with the fixed experiment."""

    context_digest: str
    record: FailureRecord
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        if (not isinstance(self.context_digest, str) or not self.context_digest.strip()
                or not isinstance(self.decision, Decision)):
            raise ValueError("experimental diagnostic scope, findings, and provenance required")
        _record_contract(self.record)
        if not isinstance(self.evidence, tuple) or not self.evidence or any(
            not isinstance(e, EvidenceRef) or not e.kind.strip() or not e.locator.strip()
            for e in self.evidence
        ):
            raise ValueError("experimental diagnostics require evidence references")


@dataclass(frozen=True)
class Experiment:
    context: Context
    anchor: AnchorState
    boundary: BoundaryProtocol
    diagnostics: tuple[ExperimentalDiagnostics, ...] = ()

    def __post_init__(self):
        if (not isinstance(self.context, Context) or not isinstance(self.anchor, AnchorState)
                or not isinstance(self.boundary, BoundaryProtocol)):
            raise ValueError("typed experimental context, frozen anchor and protocol required")
        if (not isinstance(self.anchor.quantities, tuple)
                or not isinstance(self.anchor.conditions, tuple)
                or any(not isinstance(v, str) for v in self.anchor.conditions)):
            raise ValueError("anchor quantities and conditions must be immutable")
        names = []
        for pair in self.anchor.quantities:
            if (not isinstance(pair, tuple) or len(pair) != 2
                    or not isinstance(pair[0], str) or not pair[0].strip()
                    or not finite_number(pair[1])):
                raise ValueError("anchor needs unique names and finite numeric quantities")
            names.append(pair[0])
        if len(set(names)) != len(names):
            raise ValueError("duplicate anchor quantities")
        if not isinstance(self.diagnostics, tuple) or any(
            not isinstance(d, ExperimentalDiagnostics) for d in self.diagnostics
        ):
            raise ValueError("experimental diagnostics must be an immutable typed snapshot")


@dataclass(frozen=True)
class ValidationPlan:
    plan_id: str
    equation_digest: str
    context_digest: str
    known_answers: tuple[KnownAnswerCase, ...]
    nulls: tuple[NullCase, ...]
    input_units: tuple[tuple[str, str], ...]
    output_units: tuple[tuple[str, str], ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        for value in (self.plan_id, self.equation_digest, self.context_digest):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("plan ID and exact content bindings required")
        if not isinstance(self.decision, Decision):
            raise ValueError("validation criteria require selection provenance")
        _pairs(self.input_units, "input_units")
        _pairs(self.output_units, "output_units")
        if not isinstance(self.evidence, tuple) or not self.evidence or any(
            not isinstance(e, EvidenceRef) or not e.kind.strip() or not e.locator.strip()
            for e in self.evidence
        ):
            raise ValueError("diagnostic criteria require evidence references")
        for cases, case_type in ((self.known_answers, KnownAnswerCase), (self.nulls, NullCase)):
            if not isinstance(cases, tuple) or any(not isinstance(c, case_type) for c in cases):
                raise ValueError("typed immutable case sets required")
            if len({c.case_id for c in cases}) != len(cases) or any(
                not isinstance(c.case_id, str) or not c.case_id.strip() for c in cases
            ):
                raise ValueError("case IDs must be nonempty and unique within each harness")
            for c in cases:
                if not isinstance(c.description, str):
                    raise ValueError("case description must be immutable text")
                outputs = c.expected if isinstance(c, KnownAnswerCase) else c.null_outputs
                validate_case_data(c.inputs, outputs, c.tolerances)

    def digest(self) -> str:
        return digest_record(self)


@dataclass(frozen=True)
class ScopedDiagnostics:
    """Additional equation-specific diagnostics; not a measurement/design record."""

    description_digest: str
    context_digest: str
    record: FailureRecord

    def __post_init__(self):
        if not self.description_digest or not self.context_digest:
            raise ValueError("scoped diagnostic bindings and typed findings required")
        _record_contract(self.record)


class RunState(str, enum.Enum):
    BLOCKED = "blocked-before-experimental-calculation"
    COMPUTED = "diagnostically-qualified-calculation"
    ERROR = "instrument-calculation-error"


@dataclass(frozen=True)
class CalculatedValue:
    name: str
    value: float
    unit: str
    uncertainty: None = None  # deliberately unpropagated, not zero


@dataclass(frozen=True)
class EquationRun:
    state: RunState
    equation: Adapter
    experiment: Experiment
    plan: ValidationPlan
    selection: Decision
    stages: tuple[str, ...]
    record: FailureRecord
    l0: GateResult | None
    known_answer: InstrumentValidation | None
    null: NullValidation | None
    applicability: ApplicabilityResult | None
    supplied_assessments: tuple[Assessment, ...]
    extra_diagnostics: ScopedDiagnostics | None
    dependency_states: tuple[tuple[str, str], ...]
    inputs: tuple[tuple[str, float], ...]
    outputs: tuple[CalculatedValue, ...]
    parent_run_digest: str | None
    notes: tuple[str, ...]

    def digest(self) -> str:
        return digest_record(self)

    def to_dict(self) -> dict:
        return json.loads(json.dumps(
            dict(asdict(self), equation_digest=self.equation.digest(),
                 description_digest=self.equation.description().digest(),
                 context_digest=self.experiment.context.digest(),
                 plan_digest=self.plan.digest()),
            allow_nan=False,
            default=lambda value: value.value if isinstance(value, enum.Enum) else value,
        ))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, allow_nan=False)


def _determination(code: str, message: str) -> Finding:
    return Finding(Axis.DETERMINATION, Status.FAILED, code, message,
                   "equations.substitution")


def _protocol_problems(experiment: Experiment) -> list[str]:
    c, anchor, protocol = experiment.context, experiment.anchor, experiment.boundary
    accounting = protocol.accounting
    problems = []
    if protocol.context_digest != c.digest():
        problems.append("boundary protocol belongs to a different context")
    if protocol.anchor_digest != anchor.digest() or c.anchor_digest != anchor.digest():
        problems.append("anchor content binding differs")
    conditions = {v.key: v for v in c.conditions}
    for key, expected, domain in (
        (protocol.boundary_key, accounting.boundary_label, Domain.BOUNDARY),
        (protocol.anchor_key, anchor.label, Domain.ANCHOR),
    ):
        condition = conditions.get(key)
        if condition is None or condition.domain is not domain or condition.value != expected:
            problems.append(f"{key}: selected boundary/anchor does not match protocol")
    if not accounting.declared_complete:
        problems.append("boundary ledger is not declared complete")
    registered = accounting.registered_interventions
    if not registered or len(set(registered)) != len(registered):
        problems.append("nonempty unique intervention registration required")
    links = dict(protocol.intervention_conditions)
    if set(links) != set(registered):
        problems.append("every registered intervention needs an explicit context condition")
    for intervention, key in links.items():
        condition = conditions.get(key)
        if condition is None or condition.domain not in (Domain.CONTROL, Domain.OBSERVER):
            problems.append(f"{intervention}: control/observer context condition missing")
    for a in accounting.accounts:
        if a.quantity not in anchor.as_dict() or a.initial != anchor.as_dict()[a.quantity]:
            problems.append(f"{a.quantity}: ledger initial value is not the frozen anchor value")
        condition = conditions.get(a.quantity)
        if condition is not None and condition.unit != dict(protocol.quantity_units)[a.quantity]:
            problems.append(f"{a.quantity}: ledger/context units differ")
        for e in a.exchanges:
            if e.registered_by not in registered:
                problems.append(f"{e.label}: exchange source absent from intervention registry")
    for d in experiment.diagnostics:
        if d.context_digest != c.digest():
            problems.append("experimental diagnostic snapshot belongs to another context")
    return problems


def _plan_problems(equation: Adapter, context: Context, plan: ValidationPlan) -> list[str]:
    problems = []
    if plan.equation_digest != equation.digest() or plan.context_digest != context.digest():
        problems.append("validation plan belongs to a different equation/context")
    inputs = {p.name: p.unit for p in equation.inputs}
    outputs = {p.name: p.unit for p in equation.outputs}
    if dict(plan.input_units) != inputs or dict(plan.output_units) != outputs:
        problems.append("validation port/unit contract differs from adapter")
    for c in plan.known_answers + plan.nulls:
        asserted = c.expected if isinstance(c, KnownAnswerCase) else c.null_outputs
        if set(dict(c.inputs)) != set(inputs) or set(dict(asserted)) != set(outputs):
            problems.append(f"{c.case_id}: case does not cover exactly the adapter ports")
        problems.extend(f"{c.case_id}: {p}" for p in _input_problems(equation, dict(c.inputs)))
    rules = {r.key: r for r in equation.constraints}
    for port in equation.inputs:
        rule = rules.get(port.context_key)
        if rule is None or rule.equals is not None or rule.unit != port.unit:
            problems.append(f"{port.name}: input needs an explicit numeric applicability criterion")
    return problems


def _branch_cohort_problems(experiment: Experiment) -> list[str]:
    """The initial founder cohort must be anchored, not a free scalar override."""
    initial = next((c.value for c in experiment.context.conditions
                    if c.key == "initial_population"), None)
    account = next((a for a in experiment.boundary.accounting.accounts
                    if a.quantity == "founder_count"), None)
    if (not finite_number(initial) or account is None
            or experiment.anchor.as_dict().get("founder_count") != initial
            or account.initial != initial or account.final != initial
            or dict(experiment.boundary.quantity_units).get("founder_count") != "1"
            or any(e.magnitude != 0 for e in account.exchanges)):
        return ["branching requires an anchored founder_count ledger matching initial_population, "
                "with dimensionless units and zero founder exchanges"]
    return []


class _HarnessAdapter:
    """Only supplied internally after boundary and applicability preflight."""

    def __init__(self, equation: Adapter):
        self._equation = equation
        self.instrument_id = f"{equation.equation_id}@{equation.digest()}"

    def run(self, inputs):
        return _calculate(self._equation, inputs)


def execute(
    registry: EquationRegistry,
    equation_id: str,
    revision: str,
    experiment: Experiment,
    plan: ValidationPlan,
    selection: Decision,
    assessments: tuple[Assessment, ...] = (),
    dependency_states: Mapping[str, UnknownState] | None = None,
    diagnostics: ScopedDiagnostics | None = None,
    *,
    _parent_run_digest: str | None = None,
) -> EquationRun:
    """Run the complete diagnostic path afresh for an explicitly selected adapter.

    With no adequacy evidence, calculation can proceed only as provisional
    numerical exploration in a resolved candidate domain. A blocked/conflicting/
    contradicted adequacy record, unresolved prerequisites, or a failed diagnostic
    cannot be bypassed by choosing another equation.
    """
    if not isinstance(selection, Decision):
        raise ValueError("substitution needs who/why/criteria selection provenance")
    if not isinstance(assessments, tuple) or any(not isinstance(a, Assessment) for a in assessments):
        raise ValueError("assessments must be an immutable typed tuple")
    for a in assessments:
        _record_contract(a.record)
    equation = registry.select(equation_id, revision)
    context, description = experiment.context, equation.description()
    states = dict(dependency_states or {})
    if any(not isinstance(k, str) or not isinstance(v, UnknownState) for k, v in states.items()):
        raise ValueError("typed dependency-state snapshot required")
    record = FailureRecord()
    stages: list[str] = []
    l0 = ka = nu = app = None
    inputs: dict[str, float] = {}
    notes = (
        "Calculation only: no physical support, claim support, absence, continuity, or lifecycle state is promoted.",
        "Input uncertainty is retained in the context but is not propagated; output uncertainty is UNKNOWN, not zero.",
        "Harness success covers only the supplied cases; no general numerical or physical adequacy is established.",
        "Declared units and source references are retained, not independently verified.",
        "The equation harnesses do not establish observer validity or detection sensitivity.",
    )

    def finish(state: RunState, outputs=()):
        final_record = app.record if app is not None else record
        return EquationRun(
            state, equation, experiment, plan, selection, tuple(stages), final_record,
            l0, ka, nu, app, assessments, diagnostics,
            tuple(sorted((k, v.value) for k, v in states.items())),
            tuple(sorted(inputs.items())), tuple(outputs), _parent_run_digest, notes,
        )

    problems = _protocol_problems(experiment)
    if type(equation) is FiniteBranching:
        problems.extend(_branch_cohort_problems(experiment))
    for d in experiment.diagnostics:
        if d.context_digest == context.digest():
            record = record.merge(d.record)
    if diagnostics is not None:
        if not isinstance(diagnostics, ScopedDiagnostics):
            raise ValueError("unbound diagnostic records are not accepted")
        if (diagnostics.description_digest != description.digest()
                or diagnostics.context_digest != context.digest()):
            problems.append("external diagnostics belong to a different equation/context")
        else:
            record = record.merge(diagnostics.record)
    if problems:
        record = record.with_finding(_determination("EQ_PROTOCOL_BINDING", "; ".join(problems)))
        stages.append("protocol-binding:blocked")
        return finish(RunState.BLOCKED)
    stages.append("protocol-binding:pass")

    # L0 is recomputed; a caller cannot pass a fabricated GateResult.
    l0 = l0_closure_gate(experiment.boundary.accounting)
    record = record.merge(l0.record)
    stages.append(f"l0:{l0.outcome.value}")
    if l0.outcome is not GateOutcome.PASS:
        return finish(RunState.BLOCKED)

    app = assess(description, context, assessments, record, states)
    provisional = (app.state is ApplicabilityState.UNKNOWN and app.unresolved == (
        "no bound physical/empirical adequacy assessment",
    ))
    if (app.scope is not ScopeState.INSIDE
            or not (app.state is ApplicabilityState.SUPPORTED or provisional)):
        stages.append("applicability:blocked")
        return finish(RunState.BLOCKED)
    stages.append("applicability:candidate-domain" if provisional else "applicability:recorded-support")
    # Do not merge APP_UNRESOLVED (lack of physical evidence) into the
    # instrument's diagnostics; it remains present in the applicability result.

    values = {c.key: c for c in context.conditions}
    problems = _plan_problems(equation, context, plan)
    for port in equation.inputs:
        condition = values.get(port.context_key)
        if (condition is None or not finite_number(condition.value)
                or condition.unit != port.unit or condition.uncertainty is None
                or condition.basis is ConditionBasis.ASSUMED):
            problems.append(f"{port.name}: context-bound numeric input/unit/uncertainty missing")
        else:
            inputs[port.name] = condition.value
    problems.extend(_input_problems(equation, inputs))
    if type(equation) is BondPercolation:
        mask = values.get("occupation_mask")
        if mask is not None and mask.uncertainty != 0:
            problems.append("a selected discrete occupation mask requires zero declared uncertainty")
    if type(equation) is FiniteBranching:
        for key in ("initial_population", "generation_horizon"):
            condition = values.get(key)
            if condition is not None and condition.uncertainty != 0:
                problems.append(f"{key}: selected discrete branching input requires zero declared uncertainty")
    if problems:
        record = record.with_finding(_determination("EQ_PLAN_OR_INPUT_BINDING", "; ".join(problems)))
        app = assess(description, context, assessments, record, states)
        stages.append("validation-plan:blocked")
        return finish(RunState.BLOCKED)
    stages.append("validation-plan:pass")

    instrument = _HarnessAdapter(equation)
    ka = validate_known_answers(instrument, plan.known_answers)
    record = record.merge(ka.record)
    stages.append("known-answer:pass" if ka.validated_within_tested_cases else "known-answer:blocked")
    # Both harnesses are required. Empty case sets are indeterminate, never
    # vacuous validation. A failed known-answer test stops before null/nominal.
    if not ka.validated_within_tested_cases:
        app = assess(description, context, assessments, record, states)
        return finish(RunState.BLOCKED)
    nu = validate_nulls(instrument, plan.nulls)
    record = record.merge(nu.record)
    stages.append("null:pass" if nu.clean_within_tested_cases else "null:blocked")
    if not nu.clean_within_tested_cases:
        app = assess(description, context, assessments, record, states)
        return finish(RunState.BLOCKED)

    try:
        got = _calculate(equation, inputs)
    except Exception as exc:
        record = record.with_finding(Finding(
            Axis.INSTRUMENT, Status.FAILED, "EQ_CALCULATION_ERROR",
            f"{type(exc).__name__}: {exc}", "equations.substitution",
            (EvidenceRef("equation-definition", equation.equation_id, equation.digest()),),
        ))
        app = assess(description, context, assessments, record, states)
        stages.append("calculation:error")
        return finish(RunState.ERROR)
    app = assess(description, context, assessments, record, states)
    stages.append("calculation:computed")
    return finish(RunState.COMPUTED, tuple(
        CalculatedValue(p.name, got[p.name], p.unit) for p in equation.outputs
    ))


def substitute(
    previous: EquationRun,
    registry: EquationRegistry,
    equation_id: str,
    revision: str,
    plan: ValidationPlan,
    selection: Decision,
    assessments: tuple[Assessment, ...] = (),
    dependency_states: Mapping[str, UnknownState] | None = None,
    diagnostics: ScopedDiagnostics | None = None,
) -> EquationRun:
    """Keep the experiment fixed, select a new adapter, rerun every diagnostic.

    Experiment-level diagnostic snapshots are preserved with the experiment;
    equation-specific diagnostics must be supplied for the replacement.
    Neither support, outputs, dependency states, nor harness results are
    inherited. The parent digest preserves the earlier run without mutation.
    """
    return execute(
        registry, equation_id, revision, previous.experiment, plan, selection,
        assessments, dependency_states, diagnostics, _parent_run_digest=previous.digest(),
    )
