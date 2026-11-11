"""Third fixed-case pilot: a numerical comparison is not a licensed conclusion.

Published GUM illustrative data remain illustrative. A narrow two-input,
first-order Type A variance is calculated through the existing gated executor.
Calibration/boundary/prediction probes are conditional fixtures, never evidence
that a real instrument was calibrated or a physical description was validated.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from ..applicability.mapping import Condition, ConditionBasis, Constraint, Context, Decision, Domain
from ..equations.adapter import Equation, EquationRegistry, InputPort, OutputPort
from ..equations.substitution import (
    BoundaryProtocol, Experiment, ExperimentalDiagnostics, RunState, ValidationPlan, execute, substitute,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.l0_closure import BoundaryAccounting, Direction, Exchange, QuantityAccount, ValueProvenance
from ..reference.anchor import AnchorState
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase
from .tolman_process import plain, sha
from .tolman_process import PINNED as TOLMAN_PINNED
from .pendulum_process import PINNED as PENDULUM_PINNED


ROOT = Path(__file__).resolve().parents[3]
SOURCE = "experimental/playground/audits/gum-measurement-source.json"
SOURCE_SHA256 = "0a8f7c8e5b6f2e8adf47b736a90d17259409fa244799b210464c0e39816c7806"
PRIOR_PINNED = {**TOLMAN_PINNED, **PENDULUM_PINNED}
VERSION = "measurement-process-pilot/0.1"
DECISION = Decision(
    "attributed-third-audit-process-pilot",
    "Test what additional information licenses, without turning a worked example into empirical evidence.",
    "Retain pairing, covariance, calibration scope, boundary inventory, prediction provenance and explicit decision rule.",
)
REQUIRED_TERMS = ("voltage-across-component-terminals", "current-through-component",
                  "bypass-current-explicitly-assumed-zero-for-fixture")


def evidence():
    return (EvidenceRef("published-illustrative-example", SOURCE, SOURCE_SHA256),)


def finding(axis, severity, code, message):
    return Finding(axis, severity, code, message, "audits.measurement_process", evidence())


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def read_source(root=ROOT):
    if sha(root / SOURCE) != SOURCE_SHA256:
        raise ValueError("Source record changed; explicit reinspection required")
    return json.loads((root / SOURCE).read_text())


def paired_statistics(source):
    """Exact decimal/rational covariance OF MEANS, using n*(n-1), not n-1."""
    rows = source["rows"]
    if len(rows) != 5 or len({r["pair_id"] for r in rows}) != 5:
        raise ValueError("Five unique source-paired rows required; do not zip unpaired marginals")
    if source["source_units"] != {"voltage": "V", "current": "mA", "phase": "rad"}:
        raise ValueError("Source unit contract changed")
    v = tuple(Fraction(r["voltage"]) for r in rows)
    i = tuple(Fraction(r["current"]) / 1000 for r in rows)
    n = len(v)
    mv, mi = sum(v) / n, sum(i) / n
    vv = sum((x-mv)**2 for x in v) / (n*(n-1))
    ii = sum((x-mi)**2 for x in i) / (n*(n-1))
    vi = sum((x-mv)*(y-mi) for x, y in zip(v, i)) / (n*(n-1))
    # Independent computation: project each centered pair, then its variance.
    projected = tuple((x-mv)/mi - mv*(y-mi)/mi**2 for x, y in zip(v, i))
    oracle = sum(x*x for x in projected) / (n*(n-1))
    ratios = tuple(x/y for x, y in zip(v, i))
    mean_ratios = sum(ratios) / n
    ratio_mean_variance = sum((x-mean_ratios)**2 for x in ratios) / (n*(n-1))
    return dict(v=mv, i=mi, vv=vv, ii=ii, cov=vi, oracle_variance=oracle,
                ratio_of_means=mv/mi, mean_of_ratios=mean_ratios,
                mean_of_ratios_variance=ratio_mean_variance)


def covariance_record(vv, ii, cov):
    record = FailureRecord()
    if cov is None:
        return record.with_finding(finding(
            Axis.DETERMINATION, Status.INDETERMINATE, "INPUT_COVARIANCE_MISSING",
            "Missing V/I covariance is not zero covariance; no propagated variance is licensed.",
        ))
    if (not all(finite(x) for x in (vv, ii, cov)) or vv < 0 or ii < 0
            or Fraction(cov)**2 > Fraction(vv)*Fraction(ii)):
        return record.with_finding(finding(
            Axis.DETERMINATION, Status.FAILED, "INVALID_INPUT_COVARIANCE",
            "Covariance must be finite, nonnegative on the diagonal and positive semidefinite; no clipping.",
        ))
    return record


def formal_experiment(stats, covariance="paired", *, observer="component-terminal-ratio"):
    if covariance not in ("paired", "missing", "explicit-zero"):
        raise ValueError("Explicit covariance selection required")
    values = {k: float(stats[k]) for k in ("v", "i", "vv", "ii")}
    values["cov"] = None if covariance == "missing" else (
        0.0 if covariance == "explicit-zero" else float(stats["cov"]))
    anchor = AnchorState.from_maps(
        "formal-published-case-weight", {"case_weight": 1.0},
        ("Formal record bookkeeping only; not physical charge or energy closure.",),
    )
    categories = (
        ("boundary", Domain.BOUNDARY, "declared-component-terminals-not-independently-established"),
        ("observer", Domain.OBSERVER, observer),
        ("environment", Domain.ENVIRONMENT, "published-illustrative-simultaneous-pairs"),
        ("relationships", Domain.RELATIONSHIPS, "ratio-of-means-first-order-type-a"),
        ("uncertainty", Domain.UNCERTAINTY, "type-a-only-calibration-not-supplied"),
        ("covariance_basis", Domain.RELATIONSHIPS,
         {"paired": "derived-from-published-simultaneous-pairs",
          "missing": "MISSING_NOT_ZERO",
          "explicit-zero": "PLANTED_ZERO_COVARIANCE_COUNTERFACTUAL"}[covariance]),
        ("anchor", Domain.ANCHOR, anchor.label),
    )
    units = dict(v="V", i="A", vv="V^2", ii="A^2", cov="V*A")
    context = Context(
        "gum-impedance-comparison", f"1-{covariance}", "Published worked example, not new bench data.",
        anchor.digest(), tuple(
            Condition(k, d, value, ConditionBasis.SELECTED, DECISION) for k, d, value in categories
        ) + tuple(Condition(
            k, Domain.CONTROL, value,
            ConditionBasis.SELECTED if k == "cov" and covariance == "explicit-zero" else ConditionBasis.DERIVED,
            DECISION, units[k],
            None if value is None else 0.0, evidence(),
        ) for k, value in values.items()),
        "Zero half-width identifies selected statistical input values only; variance terms carry the Type A budget. No output measurement uncertainty or calibration completeness is asserted.",
    )
    rules = tuple(Constraint(
        k, d, DECISION, equals="component-terminal-ratio" if k == "observer" else value,
    ) for k, d, value in categories) + tuple(
        Constraint(k, Domain.CONTROL, DECISION, lower=lo, upper=hi, unit=units[k])
        for k, lo, hi in (("v", 0, 10), ("i", 0.001, 0.1), ("vv", 0, 1),
                          ("ii", 0, 1), ("cov", -1, 1))
    )
    account = QuantityAccount(
        "case_weight", 1.0, 1.0, ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
        (Exchange("case_weight", Direction.INFLOW, 0.0, "published-input-selection",
                  ValueProvenance.SPECIFIED, "control:inputs"),
         Exchange("case_weight", Direction.OUTFLOW, 0.0, "calculation-readout",
                  ValueProvenance.SPECIFIED, "observer:readout")), 0.0,
    )
    ledger = BoundaryAccounting(categories[0][2], (account,), True,
                                ("control:inputs", "observer:readout"))
    protocol = BoundaryProtocol(
        context.digest(), anchor.digest(), ledger, (("case_weight", "1"),),
        (("control:inputs", "v"), ("observer:readout", "observer")), DECISION,
    )
    diagnostic = ExperimentalDiagnostics(
        context.digest(), covariance_record(values["vv"], values["ii"], values["cov"]),
        DECISION, evidence(),
    )
    return Experiment(context, anchor, protocol, (diagnostic,)), rules


def model(rules):
    return Equation(
        "gum-impedance-type-a", "1", "Impedance magnitude and first-order random-only variance",
        tuple(InputPort(k, k, unit) for k, unit in (
            ("v", "V"), ("i", "A"), ("vv", "V^2"), ("ii", "A^2"), ("cov", "V*A"))),
        (OutputPort("impedance", "v/i", "ohm"),
         OutputPort("variance", "vv/i**2+v**2*ii/i**4-2*v*cov/i**3", "ohm^2")),
        rules, DECISION, evidence(),
    )


def plan(equation, experiment):
    return ValidationPlan(
        "gum-ratio-and-covariance-fidelity", equation.digest(), experiment.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            label, dict(v=v, i=i, vv=vv, ii=ii, cov=cov),
            dict(impedance=z, variance=variance), dict(impedance=1e-12, variance=1e-12),
            "Hand-stated arithmetic answers, not generated by the adapter.",
        ) for label, v, i, vv, ii, cov, z, variance in (
            ("covariance-cross-term", 2, 1, 0.04, 0.01, 0.01, 2, 0.04),
            ("diagonal-budget", 4, 2, 0.04, 0.01, 0, 2, 0.02),
        )),
        (NullCase.from_maps(
            "zero-random-variation-not-perfect-measurement", dict(v=2, i=1, vv=0, ii=0, cov=0),
            dict(impedance=2, variance=0), dict(impedance=0, variance=0),
            "Zero Type A contribution does not mean zero total measurement uncertainty.",
        ),),
        tuple((p.name, p.unit) for p in equation.inputs),
        tuple((p.name, p.unit) for p in equation.outputs), DECISION, evidence(),
    )


def run_case(stats, covariance="paired", **kwargs):
    experiment, rules = formal_experiment(stats, covariance, **kwargs)
    equation = model(rules)
    registry = EquationRegistry()
    registry.register(equation)
    return execute(registry, equation.equation_id, equation.revision, experiment,
                   plan(equation, experiment), DECISION)


@dataclass(frozen=True)
class CalibrationFixture:
    context_digest: str
    correction_bound: float
    unit: str = "ohm"
    basis: str = "PLANTED_OUTPUT_EQUIVALENT_BOUND_NOT_A_CALIBRATION_CERTIFICATE"


@dataclass(frozen=True)
class BoundaryFixture:
    context_digest: str
    included_terms: tuple[str, ...]
    unresolved_terms: tuple[str, ...] = ()
    basis: str = "PLANTED_BOUNDARY_INVENTORY_NOT_AN_ESTABLISHED_PHYSICAL_FACT"


def retained_fixture(value):
    if value is None:
        return None
    try:
        return plain(value)
    except (TypeError, ValueError):
        # Preserve an invalid input without emitting NaN/Infinity JSON numbers
        # or silently replacing its unknown/invalid magnitude with zero.
        return {"rejected_non_json_input_repr": repr(value),
                "meaning": "Rejected input retained as text, not a numerical substitute"}


def bounded_rule(residual, variance, bound, k):
    """Exact comparison of RECORDED binary values, not an ideal-real enclosure."""
    if (not all(finite(x) for x in (residual, variance, bound, k))
            or variance <= 0 or bound < 0 or k <= 0):
        raise ValueError("Finite residual, positive variance/k and nonnegative bound required")
    r, v, b, factor = map(Fraction, (abs(residual), variance, bound, k))
    threshold_squared = factor*factor*v
    if (r+b)**2 <= threshold_squared:
        return "WITHIN_SELECTED_RULE_FOR_ALL_DECLARED_CORRECTIONS"
    if max(0, r-b)**2 > threshold_squared:
        return "OUTSIDE_SELECTED_RULE_FOR_ALL_DECLARED_CORRECTIONS"
    return "UNRESOLVED_WITHIN_CALIBRATION_BOUND"


def compare(run, *, cross_covariance=None, calibration=None, boundary=None,
            prediction=253.8, prediction_u=0.05, k=2.0):
    """A selected k*u compatibility rule, NOT a p-value or claimed coverage.

    Cross-covariance is between the Type A impedance estimate and the planted
    prediction. A bounded output-equivalent calibration correction is NOT
    another standard uncertainty; all allowed corrections must meet the rule.
    """
    record = run.record
    reasons = []
    numeric = None
    scoped = "UNRESOLVED"
    if not all(finite(x) for x in (prediction, prediction_u, k)) or prediction_u < 0 or k <= 0:
        raise ValueError("Finite prediction, nonnegative standard uncertainty and positive k required")
    pvar = prediction_u*prediction_u
    if not finite(pvar):
        raise ValueError("Prediction variance must remain finite")
    if (not run.outputs or run.state is not RunState.COMPUTED
            or run.record.instrument is not Status.OK or run.record.conclusion_blocked):
        reasons.append("no diagnostically qualified Type A estimate")
    else:
        outputs = {x.name: x.value for x in run.outputs}
        if ({x.name: x.unit for x in run.outputs} != {"impedance": "ohm", "variance": "ohm^2"}
                or not all(finite(x) for x in outputs.values())):
            raise ValueError("Finite impedance/variance outputs in explicit ohm/ohm^2 units required")
        variance = outputs["variance"]
        if variance < 0:
            raise ValueError("Negative variance is never clipped")
        if cross_covariance is None:
            reasons.append("estimate/prediction covariance missing; independence not inferred")
        elif (not finite(cross_covariance)
              or Fraction(cross_covariance)**2 > Fraction(variance)*Fraction(prediction_u)**2):
            record = record.with_finding(finding(
                Axis.DETERMINATION, Status.FAILED, "INVALID_RESIDUAL_COVARIANCE",
                "Estimate/prediction covariance violates the finite PSD contract.",
            ))
            reasons.append("invalid estimate/prediction covariance")
        else:
            residual_variance = variance + pvar - 2*cross_covariance
            if not finite(residual_variance):
                raise ValueError("Residual variance must remain finite")
            if residual_variance <= 0:
                reasons.append("standardized residual denominator is zero or invalid")
            else:
                standard_u = math.sqrt(residual_variance)
                residual = outputs["impedance"] - prediction
                threshold = k*standard_u
                if not finite(residual) or not finite(threshold) or not finite(abs(residual)/standard_u):
                    raise ValueError("Comparison arithmetic must remain finite")
                numeric = dict(
                    units=dict(prediction="ohm", prediction_standard_u="ohm",
                               residual="ohm", residual_variance="ohm^2", cross_covariance="ohm^2"),
                    prediction=prediction, prediction_standard_u=prediction_u,
                    prediction_basis="PLANTED_TEST_PREDICTION_NOT_SOURCE_OR_INDEPENDENT_VALIDATION",
                    cross_covariance=cross_covariance,
                    covariance_basis="EXPLICIT_CONDITIONAL_INPUT_NOT_AUTOMATIC_INDEPENDENCE",
                    residual=residual, residual_variance=residual_variance,
                    random_only_standard_u=standard_u, conditional_normalized_residual=abs(residual)/standard_u,
                    k=k, rule="abs(residual+calibration_correction) <= k*standard_u",
                    rule_arithmetic="Exact rational comparison of recorded finite binary residual/variance/bound/k; not an enclosure of ideal decimal inputs or nonlinear truncation error.",
                    raw_random_only_rule="MET" if bounded_rule(
                        residual, residual_variance, 0.0, k).startswith("WITHIN_") else "NOT_MET",
                    meaning="Conditional random-only comparison, not calibrated compatibility, physical adequacy, significance or 95% coverage.",
                )
    calibration_ok = isinstance(calibration, CalibrationFixture) and (
        calibration.context_digest == run.experiment.context.digest()
        and calibration.unit == "ohm" and finite(calibration.correction_bound)
        and calibration.correction_bound >= 0
        and calibration.basis == CalibrationFixture.__dataclass_fields__["basis"].default)
    boundary_ok = isinstance(boundary, BoundaryFixture) and (
        boundary.context_digest == run.experiment.context.digest()
        and isinstance(boundary.included_terms, tuple)
        and all(isinstance(t, str) for t in boundary.included_terms)
        and len(set(boundary.included_terms)) == len(boundary.included_terms)
        and set(REQUIRED_TERMS).issubset(boundary.included_terms)
        and boundary.unresolved_terms == ()
        and boundary.basis == BoundaryFixture.__dataclass_fields__["basis"].default)
    if not calibration_ok:
        reasons.append("output-equivalent calibration bound missing, invalid or out of scope")
        if calibration is not None:
            record = record.with_finding(finding(
                Axis.DETERMINATION, Status.FAILED, "INVALID_CALIBRATION_FIXTURE",
                "Supplied conditional calibration input violates its scope, unit, bound or provenance contract.",
            ))
    if not boundary_ok:
        reasons.append("relevant component-terminal/bypass-current inventory missing or unresolved")
        if boundary is not None and (
                not isinstance(boundary, BoundaryFixture)
                or boundary.context_digest != run.experiment.context.digest()
                or boundary.basis != BoundaryFixture.__dataclass_fields__["basis"].default):
            record = record.with_finding(finding(
                Axis.DETERMINATION, Status.FAILED, "INVALID_BOUNDARY_FIXTURE_SCOPE",
                "Supplied conditional boundary input belongs to another context or provenance.",
            ))
    if numeric is not None and calibration_ok and boundary_ok:
        r, b = abs(numeric["residual"]), calibration.correction_bound
        scoped = bounded_rule(r, numeric["residual_variance"], b, k)
        if scoped == "UNRESOLVED_WITHIN_CALIBRATION_BOUND":
            reasons.append("allowed calibration corrections cross the selected rule boundary")
    if reasons:
        record = record.with_finding(finding(
            Axis.DETERMINATION, Status.INDETERMINATE, "MEASUREMENT_BRIDGE_INCOMPLETE", "; ".join(reasons),
        ))
    # A functioning software harness is not an independently calibrated sensor.
    record = record.with_finding(finding(
        Axis.INSTRUMENT, Status.INDETERMINATE, "ACTUAL_CALIBRATION_NOT_ESTABLISHED",
        "Software fidelity is checked; real measurement calibration is not established by conditional fixtures.",
    )).with_finding(finding(
        Axis.DETERMINATION, Status.INDETERMINATE, "ILLUSTRATIVE_SOURCE_NOT_EMPIRICAL_BRIDGE",
        "Source data are a worked example. Prediction/calibration/boundary probes cannot authenticate empirical provenance.",
    ))
    return dict(
        numeric_comparison=numeric, conditional_scoped_rule=scoped, unresolved=reasons,
        record=plain(record), axis_statuses={axis.value: record.status_for(axis).value for axis in Axis},
        supplied_calibration=retained_fixture(calibration),
        supplied_boundary=retained_fixture(boundary),
        empirical_support="NOT_PROMOTED", physical_status=record.physical.value,
        input_kind="PUBLISHED_ILLUSTRATIVE_INPUTS_WITH_PLANTED_CONDITIONAL_PROBES",
    )


def inspect_process(source):
    stats = paired_statistics(source)
    missing = run_case(stats, "missing")
    paired = run_case(stats)
    diagonal = run_case(stats, "explicit-zero")
    outputs = {v.name: v.value for v in paired.outputs}
    if not math.isclose(outputs["variance"], float(stats["oracle_variance"]), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("Gated variance disagrees with independent centered-pair projection")
    def fixtures(run):
        digest = run.experiment.context.digest()
        return CalibrationFixture(digest, 0.01), BoundaryFixture(digest, REQUIRED_TERMS)
    cal, boundary = fixtures(paired)
    dcal, dboundary = fixtures(diagonal)
    complete = compare(paired, cross_covariance=0.0, calibration=cal, boundary=boundary)
    native_model = missing.equation
    replacement = Equation(
        "gum-equivalent-ratio-form", "1", native_model.property, native_model.inputs,
        (OutputPort("impedance", "v*(1/i)", "ohm"), native_model.outputs[1]),
        native_model.constraints, DECISION, evidence(),
    )
    registry = EquationRegistry()
    registry.register(replacement)
    substituted = substitute(missing, registry, replacement.equation_id, replacement.revision,
                             plan(replacement, missing.experiment), DECISION)
    return dict(
        exact_statistics={k: str(v) for k, v in stats.items()},
        published_rounded_checks=source["reported_rounded_checks"],
        runs={"missing_input_covariance": missing.to_dict(), "paired_covariance": paired.to_dict(),
              "explicit_zero_covariance_probe": diagonal.to_dict(),
              "missing_covariance_substitution_probe": substituted.to_dict()},
        bridge_cases={
            "input_covariance_missing": compare(missing),
            "paired_covariance_only": compare(paired),
            "calibration_and_boundary_supplied_but_cross_covariance_missing": compare(
                paired, calibration=cal, boundary=boundary),
            "cross_covariance_explicit_but_calibration_missing": compare(paired, cross_covariance=0.0, boundary=boundary),
            "calibration_supplied_but_boundary_term_missing": compare(
                paired, cross_covariance=0.0, calibration=cal,
                boundary=BoundaryFixture(paired.experiment.context.digest(), REQUIRED_TERMS[:2],
                                         ("bypass-current",))),
            "fully_supplied_conditional_fixture": complete,
            "zero_covariance_counterfactual_fixture": compare(
                diagonal, cross_covariance=0.0, calibration=dcal, boundary=dboundary),
        },
        source_provenance="PUBLISHED_WORKED_EXAMPLE_NOT_INDEPENDENT_RAW_MEASUREMENTS",
        uncertainty_scope="First-order Type A random variation only; not a complete calibration budget.",
        physical_experiment_constructed=False, physical_adequacy="UNTESTED",
        claim_support_promoted=False, whole_source_verdict="NOT_ISSUED",
    )


def markdown_report(report):
    inspection = report["inspection"]
    run = inspection["runs"]["paired_covariance"]
    outputs = {x["name"]: x["value"] for x in run["outputs"]}
    lines = [f'| {name} | {case["conditional_scoped_rule"]} |'
             for name, case in inspection["bridge_cases"].items()]
    return f"""# Measurement-to-conclusion audit-process pilot

This third fixed-case test examines whether supplying covariance, calibration
scope and boundary information licenses only the conclusions those inputs support.
It does not turn a worked measurement example into an actual experiment.

## Source and provenance

The [GUM Annex H introduction and H.2 example]({report["source"]["source_url"]})
give five paired voltage/current indications, but warn that illustrative data
need not describe real measurements. H.2 considers random variation only;
systematic-effect uncertainties would also contribute in practice
([GUM H.2]({report["source"]["source_url"]})).
The pinned source record is an attributed transcription, not a full archive,
independent authentication or newly acquired bench data.

The selected measurand is impedance magnitude Z, not resistance R. Explicit mA
to A normalization and preserved pair IDs precede the calculation. The proposed
253.8 ohm prediction, its 0.05 ohm standard uncertainty, zero estimate/prediction
covariance, calibration correction bound and boundary inventory are labeled
conditional test fixtures, not supplied by the source.

## What the arithmetic establishes

The gated ratio of means is {outputs["impedance"]:.9f} ohm. Its first-order
Type A standard uncertainty is {math.sqrt(outputs["variance"]):.9f} ohm.
An independent exact-rational centered-pair projection checks that variance.
The source reports rounded values of 254.260 ohm and 0.236 ohm
([GUM Table H.3]({report["source"]["source_url"]})).
Mean of individual ratios is retained separately; nonlinear estimators are
not forced into byte or exact numerical equivalence. The source prefers the
mean-of-individual-results approach for its set-collected data; this pilot
selects the ratio-of-means approach to inspect first-order covariance, not to
overrule that procedural preference
([GUM H.2.3-H.2.4]({report["source"]["source_url"]})).

Missing covariance blocks variance calculation; it is never filled with zero.
Restoring the covariance from paired data licenses the random-only uncertainty,
not a full calibration budget or an empirical claim. Software known-answer
and null passes do not establish the measurement instrument's calibration.

## Supplying information does not license everything

| Labeled case | Conditional scoped rule |
|---|---|
""" + "\n".join(lines) + """

The fully supplied conditional fixture and explicit-zero-covariance
counterfactual can yield different rule outcomes without a software defect.
This selected k=2 rule is not a p-value, 95% coverage statement or model ranking.
Its inclusive boundary is compared using exact rational values of the recorded
binary residual, variance, bound and k, without square-root comparison rounding.
This is not an enclosure of ideal decimal inputs or nonlinear truncation error.
The output-equivalent calibration bound is a bound, not a standard uncertainty
silently added in quadrature. If allowed corrections straddle the rule, the
answer stays unresolved; no preferred correction is selected to force agreement.

## What this does not establish

No actual calibration certificate, independent physical boundary or complete
physical charge/energy ledger is manufactured. The executor's L0 ledger
accounts for formal case weight only. The missing bypass-current boundary term
is retained rather than silently treated as zero. The supplied complete inventory
states a conditional fixture assumption, not an independently established fact.

No cause of a discrepancy is selected, no absence is inferred and no physical
model is automatically failed or validated. Physical adequacy remains UNTESTED
and actual sensor calibration remains INDETERMINATE even when the software
functions and the conditional numerical rule is met.

This test does not implement a general uncertainty engine, multivariate
calibration framework, likelihood test, universal hierarchy or demonstrated
general audit accuracy. The accompanying strict JSON retains all inputs,
decisions, exact statistics, gated runs, source/code hashes and unresolved scope.
"""


def run_pilot(output_dir, root=ROOT):
    output_dir = Path(output_dir).resolve()
    if any(output_dir == r.resolve() or r.resolve() in output_dir.parents for r in (root, ROOT)):
        raise ValueError("Output must be outside the repository")
    source = read_source(root)
    prior = {name: sha(root / name) for name in PRIOR_PINNED}
    if prior != PRIOR_PINNED:
        raise ValueError("Prior source/review pins changed; explicit reinspection required")
    code = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "experimental/playground").rglob("*.py"))}
    output_dir.mkdir(parents=True, exist_ok=False)
    inspection = inspect_process(source)
    if read_source(root) != source or any(sha(ROOT / name) != digest for name, digest in code.items()):
        raise ValueError("Source or diagnostic code changed during pilot")
    if any(sha(root / name) != digest for name, digest in prior.items()):
        raise ValueError("Prior source/review bytes changed during pilot")
    report = dict(
        schema=VERSION, executed_at_utc=datetime.now(timezone.utc).isoformat(),
        python_version=platform.python_version(), platform=platform.platform(),
        source=source, source_sha256=SOURCE_SHA256, diagnostic_code_sha256=code,
        selection=plain(DECISION), original_source_record_unchanged=True, inspection=inspection,
        prior_pilot_source_pins_unchanged=True, preserved_prior_records_sha256=prior,
    )
    (output_dir / "measurement-boundary-audit-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (output_dir / "measurement-boundary-audit-report.md").write_text(markdown_report(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run_pilot(args.output_dir)
    print(json.dumps(dict(
        report=str(args.output_dir / "measurement-boundary-audit-report.json"),
        source_provenance=report["inspection"]["source_provenance"],
        bridge_cases={name: dict(conditional_scoped_rule=case["conditional_scoped_rule"],
                                axis_statuses=case["axis_statuses"], empirical_support=case["empirical_support"])
                      for name, case in report["inspection"]["bridge_cases"].items()},
        physical_adequacy=report["inspection"]["physical_adequacy"],
    ), indent=2, allow_nan=False))
