"""Declared measurand identity, separate from calculation and physical adequacy.

Names, units, values and diagnostic PASS results cannot define a measurand.
This module compares explicit declarations on linked diagnostic-gated runs;
it neither executes equations nor authenticates the declarations physically.
"""

from __future__ import annotations

import enum
import json
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from ..applicability.mapping import ApplicabilityState, Decision, ScopeState
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.gate_results import GateOutcome
from ..validation.numeric_contract import finite_number

if TYPE_CHECKING:
    from .substitution import EquationRun


IDENTITY_FIELDS = (
    "quantity", "object_of", "normalizer", "population", "time_window",
    "spatial_scope", "reference_state",
)
_SENTINELS = frozenset((
    "unknown", "undeclared", "unmeasured", "unmapped", "pending", "none", "n/a",
))


@dataclass(frozen=True)
class Measurand:
    """Selected identity coordinates; None is unknown, never an implicit raw value.

    Use the explicit normalizer "raw" for an unnormalized quantity. Protocol
    is a declared route, not an identity coordinate; changing it does not by
    itself establish that the quantity changed, or that the routes are valid.
    """

    quantity: str | None
    object_of: str | None
    normalizer: str | None
    population: str | None
    time_window: str | None
    spatial_scope: str | None
    reference_state: str | None
    protocol: str | None
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        for key in IDENTITY_FIELDS + ("protocol",):
            value = getattr(self, key)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
                or value.strip().casefold() in _SENTINELS
            ):
                raise ValueError(f"{key}: nonempty declared text or None required")
        if not isinstance(self.decision, Decision):
            raise ValueError("measurand selection provenance required")
        if (not isinstance(self.evidence, tuple) or not self.evidence
                or any(not isinstance(e, EvidenceRef)
                       or not isinstance(e.kind, str) or not e.kind.strip()
                       or not isinstance(e.locator, str) or not e.locator.strip()
                       or (e.digest is not None and (
                           not isinstance(e.digest, str) or not e.digest.strip()))
                       for e in self.evidence)):
            raise ValueError("immutable nonempty measurand evidence references required")

    def digest(self) -> str:
        from .adapter import digest_record
        return digest_record(self)


class IdentityState(str, enum.Enum):
    MATCH = "same-declared-measurand"
    MISMATCH = "different-declared-measurands"
    UNKNOWN = "measurand-identity-unknown"


class RouteState(str, enum.Enum):
    SAME = "same-declared-route"
    DIFFERENT = "different-declared-routes"
    UNKNOWN = "route-unknown"


class ComparisonState(str, enum.Enum):
    ELIGIBLE = "declared-point-comparison"
    VOID = "void-comparison-different-measurands"
    WITHHELD = "comparison-withheld"


@dataclass(frozen=True)
class MeasurandComparison:
    previous: EquationRun
    replacement: EquationRun
    previous_output: str
    replacement_output: str
    selection: Decision
    identity: IdentityState
    route: RouteState
    state: ComparisonState
    differing_fields: tuple[str, ...]
    unresolved: tuple[str, ...]
    point_difference: float | None
    record: FailureRecord
    notes: tuple[str, ...]

    def to_dict(self) -> dict:
        value = json.loads(json.dumps(
            asdict(self), allow_nan=False,
            default=lambda v: v.value if isinstance(v, enum.Enum) else v,
        ))
        value.update(
            schema="playground/measurand-comparison/1",
            previous_run_digest=self.previous.digest(),
            replacement_run_digest=self.replacement.digest(),
            axis_statuses={axis.value: self.record.status_for(axis).value for axis in Axis},
        )
        return value


def _qualified(run: EquationRun) -> bool:
    """Check recorded execution prerequisites, not caller-supplied PASS flags."""
    from .substitution import RunState
    app = run.applicability
    return (
        run.state is RunState.COMPUTED
        and run.l0 is not None and run.l0.outcome is GateOutcome.PASS
        and run.known_answer is not None and run.known_answer.validated_within_tested_cases
        and run.null is not None and run.null.clean_within_tested_cases
        and app is not None and app.scope is ScopeState.INSIDE
        and (app.state is ApplicabilityState.SUPPORTED or (
            app.state is ApplicabilityState.UNKNOWN
            and app.unresolved == ("no bound physical/empirical adequacy assessment",)
        ))
        and run.plan.equation_digest == run.equation.digest()
        and run.plan.context_digest == run.experiment.context.digest()
        and app.description.digest() == run.equation.description().digest()
        and app.context.digest() == run.experiment.context.digest()
    )


def compare_substitution(
    previous: EquationRun,
    replacement: EquationRun,
    previous_output: str,
    replacement_output: str,
    selection: Decision,
) -> MeasurandComparison:
    """Qualify a point comparison, never physical agreement or a ratio.

    Both runs remain unchanged. A mismatch fails only the comparison's
    determination axis, not either model's physical or instrument axis.
    Unknown fields do not hide a known mismatch in another coordinate.
    """
    from .adapter import digest_record
    from .substitution import EquationRun

    if not isinstance(previous, EquationRun) or not isinstance(replacement, EquationRun):
        raise ValueError("two retained equation runs required")
    if not isinstance(selection, Decision):
        raise ValueError("comparison output mapping requires selection provenance")
    if any(not isinstance(p, str) or not p.strip()
           for p in (previous_output, replacement_output)):
        raise ValueError("explicit nonempty output names required")
    record = previous.record.merge(replacement.record)
    unresolved: list[str] = []

    def finding(code, severity, message):
        nonlocal record
        record = record.with_finding(Finding(
            Axis.DETERMINATION, severity, code, message, "equations.measurand",
            (EvidenceRef("previous-run", previous.equation.equation_id, previous.digest()),
             EvidenceRef("replacement-run", replacement.equation.equation_id, replacement.digest())),
        ))

    binding_ok = True
    if (replacement.parent_run_digest != previous.digest()
            or digest_record(previous.experiment) != digest_record(replacement.experiment)):
        binding_ok = False
        unresolved.append("substitution lineage or fixed experimental snapshot differs")
        finding("MEASURAND_RUN_BINDING", Status.FAILED, unresolved[-1])
    if not _qualified(previous) or not _qualified(replacement):
        binding_ok = False
        unresolved.append("both runs require completed diagnostic-gated calculations")
        finding("MEASURAND_RUN_UNQUALIFIED", Status.INDETERMINATE, unresolved[-1])

    ports = []
    outputs = []
    for label, run, name in (
        ("previous", previous, previous_output),
        ("replacement", replacement, replacement_output),
    ):
        port = next((p for p in run.equation.outputs if p.name == name), None)
        output = next((p for p in run.outputs if p.name == name), None)
        ports.append(port)
        outputs.append(output)
        if port is None:
            binding_ok = False
            unresolved.append(f"{label}: selected output is not declared")
            finding("MEASURAND_OUTPUT_UNBOUND", Status.FAILED, unresolved[-1])
        if output is None or port is None or (
            output.unit != port.unit or not finite_number(output.value)
        ):
            binding_ok = False
            unresolved.append(f"{label}: finite completed output with bound units required")
            finding("MEASURAND_OUTPUT_UNAVAILABLE", Status.INDETERMINATE, unresolved[-1])

    declarations = tuple(getattr(port, "measurand", None) for port in ports)
    differing = []
    missing_identity = []
    for field in IDENTITY_FIELDS:
        values = tuple(getattr(d, field) if d is not None else None for d in declarations)
        for label, value in zip(("previous", "replacement"), values):
            if value is None:
                missing_identity.append(f"{label}.{field}")
        if None not in values and values[0] != values[1]:
            differing.append(field)
    unresolved.extend(missing_identity)
    if differing:
        identity = IdentityState.MISMATCH
        finding("MEASURAND_IDENTITY_MISMATCH", Status.FAILED,
                "Unlike declared quantities; comparison is void: " + ", ".join(differing))
    elif missing_identity:
        identity = IdentityState.UNKNOWN
    else:
        identity = IdentityState.MATCH
    if missing_identity:
        finding("MEASURAND_IDENTITY_UNKNOWN", Status.INDETERMINATE,
                "Missing identity is not a match: " + ", ".join(missing_identity))

    protocols = tuple(d.protocol if d is not None else None for d in declarations)
    route = (RouteState.UNKNOWN if None in protocols else
             RouteState.SAME if protocols[0] == protocols[1] else RouteState.DIFFERENT)
    if route is RouteState.UNKNOWN:
        unresolved.append("one or both measurement routes are undeclared")
        finding("MEASURAND_ROUTE_UNKNOWN", Status.INDETERMINATE, unresolved[-1])
    units_match = all(p is not None for p in ports) and ports[0].unit == ports[1].unit
    if not units_match:
        unresolved.append("declared output units differ or are unavailable; no conversion performed")
        finding("MEASURAND_UNIT_BINDING", Status.FAILED, unresolved[-1])

    state = ComparisonState.VOID if differing else ComparisonState.WITHHELD
    difference = None
    if (identity is IdentityState.MATCH and route is not RouteState.UNKNOWN
            and binding_ok and units_match):
        candidate = outputs[1].value - outputs[0].value
        if finite_number(candidate):
            difference = candidate
            state = ComparisonState.ELIGIBLE
            finding("MEASURAND_DECLARED_POINT_COMPARISON", Status.OK,
                    "Declared identity matches; point difference only, no physical agreement established")
        else:
            unresolved.append("point difference is not finite")
            record = record.with_finding(Finding(
                Axis.INSTRUMENT, Status.FAILED, "MEASURAND_DIFFERENCE_NONFINITE",
                unresolved[-1], "equations.measurand",
            ))
    return MeasurandComparison(
        previous, replacement, previous_output, replacement_output, selection,
        identity, route, state, tuple(differing), tuple(unresolved), difference, record,
        (
            "Identity coordinates and routes are selected declarations, not independently established physical facts.",
            "Matching identity, units, numbers and harnesses does not establish calibration, observer validity or physical adequacy.",
            "Point difference is replacement minus previous; uncertainty is not propagated and no compatibility, ratio or empirical-support verdict is issued.",
            "Only exact declared identity and unit matching is implemented; no aliases, unit conversions, rebinning or reference transformations are inferred.",
            "Trusted immutable API records are inspected; this is not runtime attestation or a security boundary against hostile Python.",
        ),
    )
