"""CONSTRUCTED shared-context regression of existing audit paths, not a new model.

Two separate linked pairs share a selected context/anchor/ledger. Their
quantities and populations are not asserted to be physically linked.
"""

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

from ..applicability.mapping import Decision
from ..equations.adapter import EquationRegistry
from ..equations.substitution import ExperimentalDiagnostics, execute, substitute
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from . import denominator_process as denominator
from . import distribution_mean_process as mean


DECISION = Decision(
    "constructed-cross-audit-regression",
    "Check that denominator, mean-substitution and missing-scope findings remain distinct in a shared context.",
    "Preserve separate linked pairs and original findings; no transfer of certificates or physical support.",
)
REFERENCE = (EvidenceRef("constructed-regression", "audits.cross_audit_regression"),)


def shared_experiment(denominator_experiment, mean_experiment, *, physical_finding=False):
    """Explicitly rebind source diagnostics to a freshly constructed context.

    This is composition of two known synthetic fixtures, not a general-purpose
    merger of arbitrary experimental contexts. Common conditions must agree.
    """
    if type(physical_finding) is not bool:
        raise ValueError("explicit boolean physical-finding flag required")
    allowed_source_codes = (
        {"DENOM_DUPLICATE_MEMBER", "DENOM_FOREIGN_MEMBER"},
        {"MEAN_NEGATIVE_WEIGHT", "MEAN_SOURCE_UNKNOWN", "MEAN_EMPTY_MASS"},
    )
    for component, allowed in zip((denominator_experiment, mean_experiment), allowed_source_codes):
        if (component.context.anchor_digest != component.anchor.digest()
                or component.boundary.anchor_digest != component.anchor.digest()
                or component.boundary.context_digest != component.context.digest()
                or any(d.context_digest != component.context.digest() for d in component.diagnostics)):
            raise ValueError("stale component binding cannot be requalified by composition")
        if any(f.axis is not Axis.DETERMINATION or f.code not in allowed
               for d in component.diagnostics for f in d.record.findings):
            raise ValueError("only source-structural diagnostics may be rebound")
    den_quantities = dict(denominator_experiment.anchor.quantities)
    if (mean_experiment.anchor.label != denominator_experiment.anchor.label
            or any(den_quantities.get(key) != value for key, value in mean_experiment.anchor.quantities)
            or any(account not in denominator_experiment.boundary.accounting.accounts
                   for account in mean_experiment.boundary.accounting.accounts)
            or mean_experiment.boundary.accounting.boundary_label
            != denominator_experiment.boundary.accounting.boundary_label
            or mean_experiment.boundary.accounting.declared_complete
            != denominator_experiment.boundary.accounting.declared_complete
            or mean_experiment.boundary.accounting.registered_interventions
            != denominator_experiment.boundary.accounting.registered_interventions
            or any(dict(denominator_experiment.boundary.quantity_units).get(key) != unit
                   for key, unit in mean_experiment.boundary.quantity_units)
            or mean_experiment.boundary.boundary_key != denominator_experiment.boundary.boundary_key
            or mean_experiment.boundary.anchor_key != denominator_experiment.boundary.anchor_key
            or mean_experiment.boundary.intervention_conditions
            != denominator_experiment.boundary.intervention_conditions):
        raise ValueError("incompatible component reference or boundary bookkeeping")
    conditions = list(denominator_experiment.context.conditions)
    existing = {c.key: c for c in conditions}
    for condition in mean_experiment.context.conditions:
        if condition.key in existing:
            if existing[condition.key] != condition:
                raise ValueError(f"conflicting shared condition: {condition.key}")
        else:
            conditions.append(condition)
    context = replace(
        denominator_experiment.context, context_id="constructed-cross-audit-regression",
        system_description="CONSTRUCTED shared protocol context; independent denominator and marginal-distribution questions",
        conditions=tuple(conditions),
        uncertainty_notes="Shared synthetic enrollment anchor/ledger; source-specific unknowns retained. No physical population linkage.",
    )
    diagnostics = tuple(
        replace(d, context_digest=context.digest())
        for exp in (denominator_experiment, mean_experiment) for d in exp.diagnostics
    )
    if physical_finding:
        record = FailureRecord((Finding(
            Axis.PHYSICAL, Status.FAILED, "CROSS_PLANTED_PHYSICAL_FINDING",
            "Independent constructed physical-axis finding; not a real observation",
            "audits.cross_audit_regression", REFERENCE),))
        diagnostics += (ExperimentalDiagnostics(
            context.digest(), record, DECISION, REFERENCE),)
    return replace(
        denominator_experiment, context=context, diagnostics=diagnostics,
        boundary=replace(denominator_experiment.boundary, context_digest=context.digest()),
    )


def run_case(census, source, question, *, calculation, change_denominator=True,
             false_shared_label=False, mean_overrides=None, fail_mean_instrument=False,
             physical_finding=False, reverse_execution=False):
    for flag in (change_denominator, false_shared_label, fail_mean_instrument,
                 physical_finding, reverse_execution):
        if type(flag) is not bool:
            raise ValueError("explicit boolean regression flags required")
    if not isinstance(calculation, mean.Purpose):
        raise ValueError("explicit candidate calculation required")
    den_exp = denominator.experiment(census)
    mean_exp = mean.experiment(source, question, overrides=mean_overrides)
    exp = shared_experiment(den_exp, mean_exp, physical_finding=physical_finding)
    right_policy = denominator.Policy.SURVIVING if change_denominator else denominator.Policy.INITIAL
    declared = denominator.Policy.INITIAL if false_shared_label else right_policy
    den_a = denominator.model(census, exp, denominator.Policy.INITIAL,
                              denominator.Policy.INITIAL, revision="previous")
    den_b = denominator.model(census, exp, right_policy, declared, revision="replacement")
    mean_a = mean.model(source, question, exp, calculation, False)
    mean_b = mean.model(source, question, exp, calculation, True)
    registry = EquationRegistry()
    for equation in (den_a, den_b, mean_a, mean_b):
        registry.register(equation)
    den_plans = (denominator.plan(den_a, exp), denominator.plan(den_b, exp))
    mean_plans = (mean.plan(mean_a, exp, calculation, False),
                  mean.plan(mean_b, exp, calculation, True))
    if fail_mean_instrument:
        replacement_plan = mean_plans[1]
        bad_case = replace(replacement_plan.known_answers[0], expected=(("response", 99.0),))
        mean_plans = (mean_plans[0], replace(
            replacement_plan, known_answers=(bad_case,) + replacement_plan.known_answers[1:]))

    def pair(first, second, plans):
        previous = execute(registry, first.equation_id, first.revision, exp, plans[0], DECISION)
        replacement = substitute(previous, registry, second.equation_id, second.revision,
                                 plans[1], DECISION)
        return previous, replacement

    if reverse_execution:
        mean_runs = pair(mean_a, mean_b, mean_plans)
        den_runs = pair(den_a, den_b, den_plans)
    else:
        den_runs = pair(den_a, den_b, den_plans)
        mean_runs = pair(mean_a, mean_b, mean_plans)
    denominator_view = denominator.audit_pair(*den_runs, census)
    mean_view = mean.audit_pair(*mean_runs, source, question, calculation)
    union = denominator_view["record"].merge(mean_view["record"])
    return {
        "selection": DECISION, "shared_context_digest": exp.context.digest(),
        "shared_anchor_digest": exp.anchor.digest(), "shared_experiment": exp,
        "component_source_contexts": {
            "denominator": den_exp.context.digest(), "distribution_mean": mean_exp.context.digest(),
        },
        "execution_order": ("mean", "denominator") if reverse_execution else ("denominator", "mean"),
        "denominator": denominator_view, "distribution_mean": mean_view,
        "finding_union": union,
        "axis_statuses": {axis.value: union.status_for(axis).value for axis in Axis},
        "union_semantics": "retained findings only; not a new model verdict or a transferred certificate",
        "physical_population_linkage": "NOT_ESTABLISHED",
        "joint_estimator_adequacy": "NOT_TESTED",
        "empirical_support": "NOT_PROMOTED",
    }


def inspect_regression():
    census = denominator.fixture_census(surviving=("A", "B"))
    source = mean.fixture_distribution()
    linear = mean.fixture_question(mean.Purpose.LINEAR)
    square = mean.fixture_question(mean.Purpose.SQUARE)
    def case(*, c=census, s=source, q=square, calculation=mean.Purpose.SQUARE, **kwargs):
        return run_case(c, s, q, calculation=calculation, **kwargs)
    cases = {
        "both_controls": case(q=linear, calculation=mean.Purpose.LINEAR, change_denominator=False),
        "denominator_change_mean_control": case(q=linear, calculation=mean.Purpose.LINEAR),
        "mean_loss_denominator_control": case(change_denominator=False),
        "both_findings_known": case(),
        "false_shared_label_and_mean_loss": case(false_shared_label=True),
        "multiple_coincidences": case(
            c=denominator.fixture_census(),
            s=mean.fixture_distribution(values=(1, 1), source_id="point-at-one")),
        "missing_window_known_policy_change": case(q=replace(square, window=None)),
        "missing_purpose_not_inferred": case(q=replace(square, purpose=None)),
        "missing_scope_and_membership": case(
            c=denominator.fixture_census(surviving=None), q=replace(square, window=None)),
        "shared_unknown_gate_even_for_same_policy": case(
            q=replace(square, window=None), change_denominator=False),
        "inconsistent_mean_binding": case(mean_overrides={"m": 2.0}),
        "independent_instrument_failure": case(fail_mean_instrument=True),
        "independent_physical_failure": case(physical_finding=True),
        "known_mismatch_and_unknown_scope": case(
            q=replace(square, population="another population", window=None)),
        "empty_survivor_denominator_and_mean_loss": case(
            c=denominator.fixture_census(surviving=(), outcomes=())),
    }
    return mean.plain({
        "schema": "playground/cross-audit-regression/1",
        "status": "CONSTRUCTED_SHARED_CONTEXT_REGRESSION",
        "implementation": {
            "python": sys.version,
            "source_hashes": {
                name: hashlib.sha256((Path(__file__).resolve().parents[1] / name).read_bytes()).hexdigest()
                for name in (
                    "audits/cross_audit_regression.py", "audits/denominator_process.py",
                    "audits/distribution_mean_process.py", "equations/adapter.py",
                    "equations/substitution.py", "equations/measurand.py", "failures.py",
                )
            },
        },
        "cases": cases,
        "limits": (
            "Regression expectations are enforced by test_cross_audit_regression, not inferred from a clean rollup.",
            "Two separate audit pairs share a constructed protocol context, not an asserted joint physical population.",
            "No sequentially composed denominator/mean estimator, causal relation or physical adequacy is tested.",
            "Unknown shared context can withhold both calculations while known policy differences remain visible.",
        ),
    })


def markdown_report(report):
    rows = []
    for name, case in report["cases"].items():
        rows.append(
            f'| {name} | {case["denominator"]["audited_comparison"]} | '
            f'{case["distribution_mean"]["conclusion"]} |')
    return (
        "# Cross-audit regression pass\n\n"
        "Status: CONSTRUCTED shared-context regression. Expected blocked or failed "
        "determinations are diagnostic specimens, not failures of the regression pass "
        "and not physical findings. A separately planted physical finding is labeled as such.\n\n"
        "Two separately linked audit pairs share one frozen selected context, enrollment "
        "anchor and ledger. All four runs use the existing executor and substitution gates. "
        "Neither audit can clear the other's findings or lend it a certificate.\n\n"
        "| Scenario | Denominator comparison | Mean-substitution determination |\n"
        "|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Known denominator changes remain void beside mean information loss. "
        "Missing scope can block both calculations through the existing conservative "
        "shared-context gate; it does not erase a known denominator-policy mismatch. "
        "Source moments remain inspectable, but no qualified mean-target loss is "
        "asserted where its scope is missing.\n\n"
        "## This does not establish\n\n"
        "This is an orchestration and diagnostic regression, not a new jointly "
        "composed estimator or proof that the two source populations are linked. "
        "No physical adequacy, empirical support, stationarity, ergodicity, equilibrium "
        "or physical absence follows. The JSON retains both audit views, all original "
        "findings, source records, complete runs, scope decisions and unresolved conditions.\n"
    )


def run_regression(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    report = inspect_regression()
    (output_dir / "cross-audit-regression.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "cross-audit-regression.md").write_text(markdown_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    report = run_regression(args.output_dir)
    print(f'{report["status"]}: {len(report["cases"])} scenarios; no physical adequacy asserted')
