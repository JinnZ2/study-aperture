"""CONSTRUCTED denominator-change audit, not a real cohort or physical experiment.

Trace the two supported ratio forms to finite membership records. Equal
counts, equal rates and matching declarations do not establish equal selection
policies. All claims are local to this closed constructed procedure.
"""

from __future__ import annotations

import argparse
import enum
import hashlib
import json
import math
import sys
from dataclasses import asdict, dataclass, replace
from fractions import Fraction
from pathlib import Path

from ..applicability.mapping import Condition, ConditionBasis, Constraint, Decision, Domain
from ..equations.adapter import Equation, EquationRegistry, InputPort, OutputPort, digest_record
from ..equations.example import fixture_equation, fixture_experiment
from ..equations.measurand import ComparisonState, Measurand, compare_substitution
from ..equations.substitution import (
    ExperimentalDiagnostics, RunState, ValidationPlan, execute, substitute,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.l0_closure import QuantityAccount, ValueProvenance
from ..reference.anchor import AnchorState
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase


DECISION = Decision(
    "constructed-denominator-audit",
    "Test whether numerical coincidence or a shared false label launders a denominator change.",
    "Preserve procedure, membership, source bindings and independent failure axes.",
)


class Policy(str, enum.Enum):
    INITIAL = "per initially enrolled member"
    SURVIVING = "per surviving member at selected window end"

    @property
    def context_key(self):
        return "enrolled_count" if self is Policy.INITIAL else "surviving_count"


@dataclass(frozen=True)
class Census:
    cohort_id: str
    window: str
    enrolled: tuple[str, ...]
    surviving: tuple[str, ...] | None
    outcome_members: tuple[str, ...]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        for value in (self.cohort_id, self.window):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("explicit cohort and window identifiers required")
        for name in ("enrolled", "surviving", "outcome_members"):
            value = getattr(self, name)
            if name == "surviving" and value is None:
                continue
            if not isinstance(value, tuple) or any(
                not isinstance(member, str) or not member.strip() for member in value
            ):
                raise ValueError("immutable member-ID tuples required; only survivors may be unknown")
        if not isinstance(self.decision, Decision):
            raise ValueError("census selection provenance required")
        if (not isinstance(self.evidence, tuple) or not self.evidence or any(
            not isinstance(e, EvidenceRef) or not isinstance(e.kind, str) or not e.kind.strip()
            or not isinstance(e.locator, str) or not e.locator.strip()
            or (e.digest is not None and (
                not isinstance(e.digest, str) or not e.digest.strip()))
            for e in self.evidence
        )):
            raise ValueError("immutable nonempty census evidence required")

    def digest(self):
        return digest_record(self)

    def members(self, policy):
        if not isinstance(policy, Policy):
            raise ValueError("explicit typed selection policy required")
        return self.enrolled if policy is Policy.INITIAL else self.surviving


def fixture_census(*, surviving=("A", "B", "C", "D"), outcomes=("A", "B"), window="t0-to-t1"):
    return Census(
        "constructed-fixed-cohort", window, ("A", "B", "C", "D"), surviving,
        outcomes, DECISION, (EvidenceRef("constructed-census", "denominator_process:fixture_census"),),
    )


def evidence(census):
    return (EvidenceRef("constructed-census", census.cohort_id, census.digest()),)


def finding(census, code, message, severity=Status.FAILED):
    return Finding(Axis.DETERMINATION, severity, code, message,
                   "audits.denominator_process", evidence(census))


def census_record(census):
    record = FailureRecord()
    for name in ("enrolled", "surviving", "outcome_members"):
        members = getattr(census, name)
        if members is not None and len(set(members)) != len(members):
            record = record.with_finding(finding(
                census, "DENOM_DUPLICATE_MEMBER", f"{name}: duplicate member IDs"))
    for name in ("surviving", "outcome_members"):
        members = getattr(census, name)
        if members is not None and not set(members) <= set(census.enrolled):
            record = record.with_finding(finding(
                census, "DENOM_FOREIGN_MEMBER", f"{name}: member outside the fixed enrolled cohort"))
    return record


def experiment(census, *, count_overrides=None):
    """Construct the complete experiment; overrides are planted inconsistencies."""
    base = fixture_experiment()
    enrolled = len(census.enrolled)
    anchor = AnchorState.from_maps(
        base.anchor.label, {"energy": 2.0, "enrolled_count": enrolled},
        ("CONSTRUCTED frozen enrollment count; membership is bound separately by census digest",),
    )
    cohort_account = QuantityAccount(
        "enrolled_count", enrolled, enrolled, ValueProvenance.SPECIFIED,
        ValueProvenance.SPECIFIED, (), 0.0,
    )
    accounting = replace(base.boundary.accounting,
                         accounts=base.boundary.accounting.accounts + (cohort_account,))
    values = {
        "outcome_count": len(census.outcome_members),
        "enrolled_count": enrolled,
        "surviving_count": None if census.surviving is None else len(census.surviving),
    }
    values.update(count_overrides or {})
    conditions = tuple(
        Condition(key, Domain.RELATIONSHIPS, value, ConditionBasis.DERIVED,
                  DECISION, "1", None if value is None else 0.0, evidence(census))
        for key, value in values.items()
    ) + tuple(
        Condition(key, domain, value, ConditionBasis.SELECTED, DECISION,
                  evidence=evidence(census))
        for key, domain, value in (
            ("census_digest", Domain.RELATIONSHIPS, census.digest()),
            ("cohort_id", Domain.RELATIONSHIPS, census.cohort_id),
            ("census_window", Domain.CONTROL, census.window),
        )
    )
    context = replace(
        base.context, context_id="constructed-denominator-cohort",
        anchor_digest=anchor.digest(), conditions=base.context.conditions + conditions,
        uncertainty_notes="CONSTRUCTED exact finite membership counts; no real sampling, detection or survival measurement.",
    )
    boundary = replace(
        base.boundary, context_digest=context.digest(), anchor_digest=anchor.digest(),
        accounting=accounting,
        quantity_units=base.boundary.quantity_units + (("enrolled_count", "1"),),
    )
    record = census_record(census)
    diagnostics = () if not record.findings else (
        ExperimentalDiagnostics(context.digest(), record, DECISION, evidence(census)),)
    return replace(base, context=context, anchor=anchor, boundary=boundary, diagnostics=diagnostics)


def identity(census, exp, declared_policy):
    if declared_policy is not None and not isinstance(declared_policy, Policy):
        raise ValueError("typed declared policy or None required")
    return Measurand(
        "constructed selected outcome count per selected cohort member",
        "constructed cohort outcomes", None if declared_policy is None else declared_policy.value,
        census.cohort_id, census.window, exp.boundary.accounting.boundary_label,
        exp.anchor.digest(), "constructed finite-member counting and ratio",
        DECISION, evidence(census),
    )


def model(census, exp, policy, declared_policy, *, revision, expression="n/d"):
    if not isinstance(policy, Policy):
        raise ValueError("typed actual input-selection policy required")
    base = fixture_equation()
    rules = base.constraints + (
        Constraint("outcome_count", Domain.RELATIONSHIPS, DECISION, lower=0, upper=100, unit="1"),
        Constraint(policy.context_key, Domain.RELATIONSHIPS, DECISION, lower=1, upper=100, unit="1"),
    ) + tuple(
        Constraint(key, domain, DECISION, equals=value)
        for key, domain, value in (
            ("census_digest", Domain.RELATIONSHIPS, census.digest()),
            ("cohort_id", Domain.RELATIONSHIPS, census.cohort_id),
            ("census_window", Domain.CONTROL, census.window),
        )
    )
    return Equation(
        "constructed-cohort-rate", revision, "selected outcomes per selected cohort member",
        (InputPort("n", "outcome_count", "1"), InputPort("d", policy.context_key, "1")),
        (OutputPort("rate", expression, "1", identity(census, exp, declared_policy)),),
        rules, DECISION, evidence(census),
    )


def plan(eq, exp):
    # Independent hand-stated arithmetic cases, not expectations from eq.
    return ValidationPlan(
        "constructed-ratio-plan", eq.digest(), exp.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            label, {"n": n, "d": d}, {"rate": value}, {"rate": 0.0},
            "CONSTRUCTED hand-stated ratio expectation",
        ) for label, n, d, value in (
            ("half", 2.0, 4.0, 0.5), ("one", 2.0, 2.0, 1.0))),
        (NullCase.from_maps("zero-outcomes", {"n": 0.0, "d": 4.0},
                           {"rate": 0.0}, {"rate": 0.0}),),
        (("n", "1"), ("d", "1")), (("rate", "1"),), DECISION, eq.evidence,
    )


def trace_denominator(run, census):
    """Check a closed ratio/input contract against the retained finite member IDs."""
    record = census_record(census)
    checks = []

    def add(code, message, severity=Status.FAILED):
        nonlocal record
        record = record.with_finding(finding(census, code, message, severity))
        checks.append(message)

    values = {c.key: c for c in run.experiment.context.conditions}
    ports = {p.name: p for p in run.equation.inputs}
    policy = None
    if (type(run.equation) is not Equation or set(ports) != {"n", "d"}
            or ports["n"].context_key != "outcome_count"
            or len(run.equation.outputs) != 1 or run.equation.outputs[0].name != "rate"
            or any(p.unit != "1" for p in run.equation.inputs + run.equation.outputs)
            or run.equation.outputs[0].expression not in ("n/d", "n*(1/d)")):
        add("DENOM_UNSUPPORTED_PROCEDURE", "outside the two explicit ratio procedures",
            Status.INDETERMINATE)
    else:
        policy = next((p for p in Policy if p.context_key == ports["d"].context_key), None)
        if policy is None:
            add("DENOM_UNKNOWN_INPUT_POLICY", "denominator input has no supported membership policy",
                Status.INDETERMINATE)
    for key, expected in (("census_digest", census.digest()),
                          ("cohort_id", census.cohort_id), ("census_window", census.window)):
        condition = values.get(key)
        if (condition is None or condition.value != expected
                or evidence(census)[0] not in condition.evidence):
            add("DENOM_SOURCE_BINDING", f"{key}: trace census does not match the run")
    members = None if policy is None else census.members(policy)
    actual_value = None
    declaration = (run.equation.outputs[0].measurand
                   if type(run.equation) is Equation and run.equation.outputs else None)
    if policy is not None:
        condition = values.get(policy.context_key)
        actual_value = None if condition is None else condition.value
        if members is None:
            add("DENOM_MEMBERSHIP_UNKNOWN", "selected denominator membership remains unknown",
                Status.INDETERMINATE)
        elif not members:
            add("DENOM_EMPTY", "selected denominator is explicitly empty; rate is undefined",
                Status.INDETERMINATE)
        if condition is None or evidence(census)[0] not in condition.evidence:
            add("DENOM_OPERAND_PROVENANCE", "denominator operand lacks this census evidence binding")
        if members is not None and actual_value != len(members):
            add("DENOM_VALUE_MISMATCH", "denominator input differs from the selected membership cardinality")
        if declaration is None or declaration.normalizer is None:
            add("DENOM_DECLARATION_UNKNOWN", "normalizer declaration remains unknown",
                Status.INDETERMINATE)
        elif declaration.normalizer != policy.value:
            add("DENOM_DECLARATION_MISMATCH", "declared normalizer differs from the actual input-selection policy")
    numerator = values.get("outcome_count")
    if (numerator is None or numerator.value != len(census.outcome_members)
            or evidence(census)[0] not in numerator.evidence):
        add("DENOM_NUMERATOR_BINDING", "shared outcome numerator lacks its exact membership/count binding")
    if run.state is RunState.COMPUTED and policy is not None:
        inputs = dict(run.inputs)
        if inputs != {"n": len(census.outcome_members), "d": actual_value}:
            add("DENOM_EXECUTED_INPUTS", "retained executed operands differ from their bound context")
        if members:
            oracle = float(Fraction(len(census.outcome_members), len(members)))
            if (len(run.outputs) != 1 or run.outputs[0].name != "rate"
                    or not math.isclose(run.outputs[0].value, oracle, rel_tol=1e-12, abs_tol=0.0)):
                add("DENOM_POINT_ORACLE", "retained point differs from the independent finite-count ratio oracle")
    if declaration is not None:
        expected = {
            "population": census.cohort_id, "time_window": census.window,
            "reference_state": run.experiment.anchor.digest(),
            "spatial_scope": run.experiment.boundary.accounting.boundary_label,
        }
        for key, value in expected.items():
            supplied = getattr(declaration, key)
            if supplied is None:
                add("DENOM_SCOPE_UNKNOWN", f"declared {key} remains unknown", Status.INDETERMINATE)
            elif supplied != value:
                add("DENOM_SCOPE_MISMATCH", f"declared {key} differs from procedure scope")
    qualified = not record.findings
    if qualified:
        record = record.with_finding(finding(
            census, "DENOM_TRACE_CONSISTENT",
            "Closed constructed ratio inputs, selection policy and membership record are consistent",
            Status.OK))
    return {
        "run_digest": run.digest(), "run_state": run.state.value, "census_digest": census.digest(),
        "policy": None if policy is None else policy.value,
        "declared_normalizer": None if declaration is None else declaration.normalizer,
        "members": members, "denominator_value": actual_value,
        "oracle_rate": (str(Fraction(len(census.outcome_members), len(members)))
                        if qualified and members else None),
        "qualified_within_constructed_scope": qualified,
        "unresolved_or_failed_checks": tuple(checks),
        "record": record,
    }


def audit_pair(previous, replacement, census):
    generic = compare_substitution(previous, replacement, "rate", "rate", DECISION)
    left = trace_denominator(previous, census)
    right = trace_denominator(replacement, census)
    record = generic.record.merge(left["record"]).merge(right["record"])
    known_change = (left["policy"] is not None and right["policy"] is not None
                    and left["policy"] != right["policy"])
    same_members = (left["members"] is not None and right["members"] is not None
                    and set(left["members"]) == set(right["members"]))
    state = (ComparisonState.VOID
             if known_change or generic.state is ComparisonState.VOID
             else ComparisonState.WITHHELD)
    difference = None
    if known_change:
        record = record.with_finding(finding(
            census, "DENOM_POLICY_CHANGE",
            "Different membership-selection policies are not interchangeable, even at a coincident count or rate"))
    elif (left["qualified_within_constructed_scope"]
          and right["qualified_within_constructed_scope"] and same_members
          and generic.state is ComparisonState.ELIGIBLE):
        state, difference = ComparisonState.ELIGIBLE, generic.point_difference
    return {
        "census": census, "census_digest": census.digest(),
        "declaration_comparison": generic.to_dict(),
        "procedure_traces": (left, right),
        "audited_comparison": state.value, "point_difference": difference,
        "same_members_at_this_snapshot": same_members,
        "selection_policies_differ": known_change,
        "interchangeability_established": False,
        "record": record,
        "axis_statuses": {axis.value: record.status_for(axis).value for axis in Axis},
        "physical_adequacy": record.physical.value.upper(), "empirical_support": "NOT_PROMOTED",
    }


def run_case(census, *, left_policy=Policy.INITIAL, right_policy=Policy.SURVIVING,
             left_declared=Policy.INITIAL, right_declared=Policy.SURVIVING,
             expression="n/d", count_overrides=None):
    exp = experiment(census, count_overrides=count_overrides)
    first = model(census, exp, left_policy, left_declared, revision="initial")
    second = model(census, exp, right_policy, right_declared, revision="replacement",
                   expression=expression)
    registry = EquationRegistry()
    registry.register(first)
    registry.register(second)
    a = execute(registry, first.equation_id, first.revision, exp, plan(first, exp), DECISION)
    b = substitute(a, registry, second.equation_id, second.revision, plan(second, exp), DECISION)
    return a, b, audit_pair(a, b, census)


def plain(value):
    return json.loads(json.dumps(
        value, allow_nan=False,
        default=lambda v: v.value if isinstance(v, enum.Enum) else asdict(v),
    ))


def inspect_process():
    no_loss = fixture_census()
    loss = fixture_census(surviving=("A", "B"), window="t1-to-t2")
    cases = {
        "coincident_positive_rates_no_attrition": run_case(no_loss)[2],
        "later_attrition_breaks_numeric_coincidence": run_case(loss)[2],
        "zero_outcomes_hide_different_counts": run_case(
            fixture_census(surviving=("A", "B"), outcomes=()))[2],
        "false_shared_label_at_coincidence": run_case(
            no_loss, right_declared=Policy.INITIAL)[2],
        "false_shared_label_after_attrition": run_case(
            loss, right_declared=Policy.INITIAL)[2],
        "both_labels_wrong_same_actual_policy": run_case(
            loss, left_policy=Policy.SURVIVING, left_declared=Policy.INITIAL,
            right_declared=Policy.INITIAL)[2],
        "same_policy_equivalent_ratio_route": run_case(
            loss, right_policy=Policy.INITIAL, right_declared=Policy.INITIAL,
            expression="n*(1/d)")[2],
        "survivor_policy_equivalent_ratio_route": run_case(
            loss, left_policy=Policy.SURVIVING, left_declared=Policy.SURVIVING,
            expression="n*(1/d)")[2],
        "both_survivor_memberships_unknown": run_case(
            fixture_census(surviving=None), left_policy=Policy.SURVIVING,
            left_declared=Policy.SURVIVING)[2],
        "consistent_initial_trace_broader_context_still_unknown": run_case(
            fixture_census(surviving=None), right_policy=Policy.INITIAL,
            right_declared=Policy.INITIAL)[2],
        "explicitly_empty_survivor_denominator": run_case(
            fixture_census(surviving=(), outcomes=()), left_policy=Policy.SURVIVING,
            left_declared=Policy.SURVIVING)[2],
        "equal_counts_include_unenrolled_members": run_case(
            fixture_census(surviving=("A", "B", "X", "Y")))[2],
        "survivor_count_claim_disagrees_with_membership": run_case(
            loss, right_declared=Policy.INITIAL,
            count_overrides={"surviving_count": 4})[2],
    }
    return plain({
        "schema": "playground/denominator-change-audit/1",
        "status": "CONSTRUCTED_DENOMINATOR_PROCEDURE_AUDIT",
        "implementation": {
            "python": sys.version,
            "source_hashes": {
                name: hashlib.sha256((Path(__file__).resolve().parents[1] / name).read_bytes()).hexdigest()
                for name in (
                    "audits/denominator_process.py", "equations/adapter.py",
                    "equations/substitution.py", "equations/measurand.py",
                    "failures.py", "applicability/mapping.py", "gates/l0_closure.py",
                    "reference/anchor.py", "validation/known_answer.py", "validation/null_harness.py",
                )
            },
            "hash_scope": "Explicit producer/dependency files only; hashes are not independent authentication.",
        },
        "cases": cases,
        "limits": (
            "Finite member IDs and outcomes are constructed, not observed or independently authenticated.",
            "Only n/d and n*(1/d) with the closed n,d input mapping are traced.",
            "A per-survivor denominator is not condemned or ranked below initial enrollment; it answers another question.",
            "Snapshot equality does not establish policy equivalence, permanent membership or future equality.",
            "No selection-bias estimate, causal inference, calibrated uncertainty, physical absence or claim support follows.",
        ),
    })


def markdown_report(report):
    rows = []
    for name, case in report["cases"].items():
        rates = []
        for side in ("previous", "replacement"):
            outputs = case["declaration_comparison"][side]["outputs"]
            rates.append(str(outputs[0]["value"]) if outputs else "not computed")
        rows.append(
            f'| {name} | {rates[0]} | {rates[1]} | {case["audited_comparison"]} |')
    return (
        "# Denominator-change audit\n\n"
        "Status: CONSTRUCTED finite-cohort procedure audit, not observed cohort data. "
        "All rates are illustrative; physical adequacy remains UNTESTED and empirical support is NOT_PROMOTED.\n\n"
        "Four initially enrolled members and four survivors give 2/4 under either "
        "policy. A separate later-window fixture has two survivors: the same two "
        "specified outcomes give 2/4 per initial member and 2/2 per survivor. "
        "Neither the first coincidence nor a shared false label licenses interchangeability.\n\n"
        "| Case | Initial-description raw rate | Replacement raw rate | Audited comparison |\n"
        "|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Raw rates are retained, not treated as valid cross-measurand comparisons. "
        "The JSON preserves the declaration-only result beside the procedure audit, "
        "both complete equation runs, member IDs, policies, source digests, decisions, "
        "diagnostics and unresolved findings.\n\n"
        "## This does not establish\n\n"
        "The census is constructed, not independently verified. Trace consistency "
        "is local to two supported ratio forms, not proof of actual enrollment or "
        "survival, general program semantics, absence, causality or physical adequacy. "
        "Per-survivor and per-initial-member quantities are not ranked universally. "
        "Even the same-policy control establishes only a scoped nominal point comparison.\n"
    )


def run_audit(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    report = inspect_process()
    (output_dir / "denominator-change-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "denominator-change-audit.md").write_text(
        markdown_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_audit(args.output_dir)
    print(f'{result["status"]}: {len(result["cases"])} cases; physical adequacy UNTESTED')
