"""Second fixed-case audit: metric scope, singularity and reference validity.

The closed arithmetic engine calculates error metrics, NOT sine or pendulum
dynamics. math.sin supplies synthetic inputs; independent rational alternating
Taylor bounds check that reference before gated execution. No physical data.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

from ..applicability.mapping import (
    Condition, ConditionBasis, Constraint, Context, Decision, Domain,
)
from ..equations.adapter import Equation, EquationRegistry, InputPort, OutputPort
from ..equations.substitution import (
    BoundaryProtocol, Experiment, ExperimentalDiagnostics, ValidationPlan,
    execute, substitute,
)
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..gates.l0_closure import (
    BoundaryAccounting, Direction, Exchange, QuantityAccount, ValueProvenance,
)
from ..reference.anchor import AnchorState
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase
from .tolman_process import numeric_differences, plain, sha


ROOT = Path(__file__).resolve().parents[3]
CASE = "experimental/scope_audit_lab/reviews/physics-cases"
SOURCE = "experimental/playground/audits/pendulum-source-review.json"
VERSION = "pendulum-process-pilot/0.1"
NUMERIC_TOLERANCE = 1e-14  # computation comparison, never physical uncertainty
PINNED = {
    f"{CASE}/README.md": "fa2f1ac390dd70fbc257cd6f59719f88d444a365d8575361e1dd192a57bd0cc1",
    f"{CASE}/compute_review.py": "18b505fd3cfd780b9736de5ca9f17e6bbfb8be1c3d94bec376729cc1e70aa4ec",
    f"{CASE}/results.json": "58557d50a72da50ae697792f2de28bbe111a193f5be422edfdd72f47852ea894",
    "experimental/scope_audit_lab/schemas/draft-0.1/evidence.schema.json": "db9d9902bd943e80cdccc660b22dbb12192732adc5bfcd5aecb0c4f801975775",
    "experimental/scope_audit_lab/examples/schema-draft-0.1/records.json": "4d152cf48c629ff0e96857fe40716844669ef445f6f6d472fcac57c5192e9f90",
    "experimental/scope_audit_lab/requirements/scope-audit-lab-0.2.md": "50a1bf3d5b556cdb08c4367b5e442cdd512b7f2fbda9498383645b4c8e57a10d",
    SOURCE: "9f32fc42edd996673836df09b7d894c7cd2dccf3c6c7eec40986123f64ba8b10",
}
DECISION = Decision(
    "attributed-second-audit-process-pilot",
    "Challenge metric ambiguity and output transfer, not repeat a whole-paper verdict.",
    "Preserved review; explicit denominator, zero-domain exclusion, independent reference bounds and diagnostic-gated arithmetic.",
)


def evidence():
    return (EvidenceRef("preserved-authoring-review", f"{CASE}/README.md", PINNED[f"{CASE}/README.md"]),
            EvidenceRef("attributed-source-inspection", SOURCE, PINNED[SOURCE]))


def verify_snapshot(root=ROOT):
    actual = {name: sha(root / name) for name in PINNED}
    if actual != PINNED:
        raise ValueError("Snapshot changed; explicit reinspection required")
    return actual


def sine_bounds(theta):
    """Exact bounds on sine of a BINARY radian input, not exact degree*pi/180.

    On [0, 0.6], alternating sine terms decrease. The degree-23 partial sum
    ends negative (lower); adding degree 25 gives the upper. Fraction arithmetic
    does not use math.sin, math.pi or a fitted expectation.
    """
    if type(theta) is not float or not math.isfinite(theta) or not 0 <= theta <= 0.6:
        raise ValueError("oracle requires a finite float radian input in [0, 0.6]")
    x = Fraction.from_float(theta)
    lower = sum(((-1)**n * x**(2*n+1) / math.factorial(2*n+1)
                 for n in range(12)), Fraction(0))
    return lower, lower + x**25 / math.factorial(25)


def outward(bounds):
    return [math.nextafter(float(bounds[0]), -math.inf),
            math.nextafter(float(bounds[1]), math.inf)]


def reference_check(theta, sine):
    bounds = sine_bounds(theta)
    lo, hi = outward(bounds)
    ok = type(sine) is float and math.isfinite(sine) and lo <= sine <= hi
    record = FailureRecord()
    if not ok:
        record = record.with_finding(Finding(
            Axis.INSTRUMENT, Status.FAILED, "PENDULUM_SINE_REFERENCE_MISMATCH",
            "Synthetic sine reference disagrees with independent rational Taylor bounds.",
            "audits.pendulum_process.reference_check", evidence(),
        ))
    return record, bounds


def metric_bounds(theta, sine_interval, denominator):
    if denominator not in ("sine", "angle"):
        raise ValueError("an explicit supported denominator is required")
    if theta == 0:
        return None  # no silent continuous extension at a zero denominator
    t = Fraction.from_float(theta)
    lo, hi = sine_interval
    if denominator == "sine":
        return t / hi - 1, t / lo - 1
    return 1 - hi / t, 1 - lo / t


def criterion(bounds, strict=False):
    if bounds is None:
        return "UNDEFINED"
    lo, hi = bounds
    tolerance = Fraction(1, 100)
    if (hi < tolerance if strict else hi <= tolerance):
        return "MET"
    if (lo >= tolerance if strict else lo > tolerance):
        return "NOT_MET"
    return "UNRESOLVED_NUMERIC_BOUND"


def formal_experiment(degrees, *, sine_override=None, convention="radians",
                      output_quantity="restoring-term-relative-error"):
    if type(degrees) not in (int, float) or not math.isfinite(degrees) or not 0 <= degrees <= 30:
        raise ValueError("selected synthetic degree input must be finite and in [0, 30]")
    theta = math.radians(degrees)
    sine = math.sin(theta) if sine_override is None else sine_override
    reference, bounds = reference_check(theta, sine)
    anchor = AnchorState.from_maps(
        "formal-case-weight-only", {"case_weight": 1.0},
        ("Bookkeeping for a mathematical fixture, not pendulum energy or a measured reference.",),
    )
    categories = (
        ("boundary", Domain.BOUNDARY, "selected-synthetic-restoring-term-comparison"),
        ("observer", Domain.OBSERVER, output_quantity),
        ("environment", Domain.ENVIRONMENT, "mathematical-inputs-no-pendulum-observations"),
        ("angle_convention", Domain.RELATIONSHIPS, convention),
        ("metric_domain", Domain.RELATIONSHIPS,
         "positive-nonzero" if theta else "undefined-zero-denominator"),
        ("criterion", Domain.CONTROL, "selected-inclusive-error<=1/100"),
        ("uncertainty", Domain.UNCERTAINTY, "computational-bounds-not-physical-error-bars"),
        ("anchor", Domain.ANCHOR, anchor.label),
    )
    context = Context(
        "pendulum-restoring-term", "1", "Synthetic comparison, not a pendulum experiment.",
        anchor.digest(), tuple(
            Condition(k, d, v, ConditionBasis.SELECTED, DECISION) for k, d, v in categories
        ) + (
            Condition("theta", Domain.CONTROL, theta, ConditionBasis.SELECTED, DECISION, "1", 0.0),
            Condition("sine", Domain.OBSERVER, sine, ConditionBasis.DERIVED, DECISION, "1", 0.0, evidence()),
        ),
        "Zero input half-width identifies selected binary values only. Sine reference is independently checked; output/physical uncertainty is not established. Radian conversion is not an interval enclosure of exact degree*pi/180.",
    )
    # Fixed intended rules, never inferred from the supplied context's labels.
    desired = dict((k, v) for k, _, v in categories)
    desired.update(angle_convention="radians", observer="restoring-term-relative-error",
                   metric_domain="positive-nonzero")
    rules = tuple(Constraint(k, d, DECISION, equals=desired[k]) for k, d, _ in categories) + (
        Constraint("theta", Domain.CONTROL, DECISION, lower=0, upper=0.6, unit="1"),
        Constraint("sine", Domain.OBSERVER, DECISION, lower=0, upper=1, unit="1"),
    )
    account = QuantityAccount(
        "case_weight", 1.0, 1.0, ValueProvenance.SPECIFIED, ValueProvenance.SPECIFIED,
        (Exchange("case_weight", Direction.INFLOW, 0.0, "selected-input",
                  ValueProvenance.SPECIFIED, "control:angle"),
         Exchange("case_weight", Direction.OUTFLOW, 0.0, "selected-readout",
                  ValueProvenance.SPECIFIED, "observer:metric")), 0.0,
    )
    ledger = BoundaryAccounting(desired["boundary"], (account,), True,
                                ("control:angle", "observer:metric"))
    protocol = BoundaryProtocol(
        context.digest(), anchor.digest(), ledger, (("case_weight", "1"),),
        (("control:angle", "theta"), ("observer:metric", "observer")), DECISION,
    )
    diagnostics = (ExperimentalDiagnostics(context.digest(), reference, DECISION, evidence()),)
    return Experiment(context, anchor, protocol, diagnostics), rules, bounds


def models(rules):
    return tuple(Equation(
        f"pendulum-{kind}-denominator", "1",
        f"Restoring-term relative error with explicit {kind} denominator, not period error.",
        (InputPort("t", "theta", "1"), InputPort("s", "sine", "1")),
        (OutputPort("error", expression, "1"),), rules, DECISION, evidence(),
    ) for kind, expression in (("sine", "(t-s)/s"), ("angle", "(t-s)/t")))


def plan(model, experiment):
    sine_denominator = model.equation_id == "pendulum-sine-denominator"
    return ValidationPlan(
        f"{model.equation_id}-arithmetic-fidelity", model.digest(), experiment.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            label, {"t": t, "s": s}, {"error": answer}, {"error": NUMERIC_TOLERANCE},
            "Hand-stated arithmetic expectation; inputs are not claimed to satisfy s=sin(t).",
        ) for label, t, s, answer in (
            ("ratio-one", 1.0, 0.5, 1.0 if sine_denominator else 0.5),
            ("ratio-half", 0.75, 0.5, 0.5 if sine_denominator else 1/3),
        )),
        (NullCase.from_maps(
            "zero-deviation-nonzero-denominator", {"t": 0.5, "s": 0.5},
            {"error": 0.0}, {"error": 0.0}, "No discrepancy, not zero angle or physical absence.",
        ),),
        (("t", "1"), ("s", "1")), (("error", "1"),), DECISION, evidence(),
    )


def run_pair(experiment, rules):
    a, b = models(rules)
    registry = EquationRegistry()
    registry.register(a)
    registry.register(b)
    first = execute(registry, a.equation_id, a.revision, experiment, plan(a, experiment), DECISION)
    second = substitute(first, registry, b.equation_id, b.revision, plan(b, experiment), DECISION)
    return first, second


def inspect_process():
    cases = []
    for degrees in (0, 10, 14, 14.5, 30):
        experiment, rules, sine_interval = formal_experiment(degrees)
        runs = run_pair(experiment, rules)
        theta = next(c.value for c in experiment.context.conditions if c.key == "theta")
        metrics = {}
        for denominator, run in zip(("sine", "angle"), runs):
            bounds = metric_bounds(theta, sine_interval, denominator)
            if bounds is not None:
                if not run.outputs:
                    raise ValueError("Expected a diagnostic-qualified metric calculation")
                lo, hi = outward(bounds)
                value = run.outputs[0].value
                if not lo - NUMERIC_TOLERANCE <= value <= hi + NUMERIC_TOLERANCE:
                    raise ValueError("Metric calculation disagrees with independent reference bounds")
            metrics[denominator] = {
                "metric_definition": "(theta-sin(theta))/sin(theta)" if denominator == "sine"
                                     else "(theta-sin(theta))/theta",
                "exact_binary_radian_error_bounds": None if bounds is None else [str(v) for v in bounds],
                "error_bounds_outward_float": None if bounds is None else outward(bounds),
                "inclusive_selected_criterion": criterion(bounds),
                "strict_comparison_under_this_denominator": criterion(bounds, strict=True),
                "run": run.to_dict(),
            }
        cases.append({"selected_degrees": degrees, "selected_binary_radians": theta, "metrics": metrics})
    probes = {}
    for label, kwargs in (
        ("period-transfer", {"output_quantity": "period-relative-error"}),
        ("angle-convention-change", {"convention": "degrees"}),
        ("corrupt-reference", {"sine_override": 0.5}),
    ):
        experiment, rules, _ = formal_experiment(10, **kwargs)
        probes[label] = {
            "input_kind": "PLANTED_NOT_OBSERVED", "runs": [r.to_dict() for r in run_pair(experiment, rules)],
        }
    return {
        "cases": cases, "probes": probes,
        "source_claim_status": "UNDETERMINED_AS_WRITTEN_METRIC_NOT_SPECIFIED",
        "physical_status": "UNTESTED", "claim_support_promoted": False,
        "physical_experiment_constructed": False, "whole_source_verdict": "NOT_ISSUED",
        "missing_physical": ["pendulum observations", "instrument calibration", "physical boundary and energy accounting",
                             "damping/geometry/environment", "measurement covariance and propagated uncertainty"],
        "exact_threshold_controls": [
            {"error": str(v), "inclusive": criterion((v, v)), "strict": criterion((v, v), strict=True)}
            for v in (Fraction(999, 100000), Fraction(1, 100), Fraction(1001, 100000))
        ],
    }


def markdown_report(report):
    rows = []
    for case in report["inspection"]["cases"]:
        values = []
        for metric in case["metrics"].values():
            outputs = metric["run"]["outputs"]
            values.append("undefined" if not outputs else f'{100*outputs[0]["value"]:.6f}%')
            values.append(metric["inclusive_selected_criterion"])
        rows.append(f'| {case["selected_degrees"]} | ' + " | ".join(values) + " |")
    return """# Pendulum audit-process pilot

This second bounded audit inspects an approximation claim and its error contract,
not a pendulum experiment or an independent scientific replication.

## Source and preserved review

The [OpenStax pendulum section](https://openstax.org/books/university-physics-volume-1/pages/15-4-pendulums)
compares sine and radian angle below about 15 degrees using a less-than-1% statement,
without specifying the relative-error denominator. The
[preserved authoring review](https://github.com/JinnZ2/study-aperture/blob/main/experimental/scope_audit_lab/reviews/physics-cases/README.md)
already noted this ambiguity. Its synthetic arithmetic is replayed, not relabeled
as observed data; the original files remain unchanged. The attributed source
inspection note is not a full publication archive or independent authentication.

## Two explicit metrics, no universal ranking

The selected rule here is inclusive error <= 1/100; source wording is strict.
Both comparisons are retained separately. Percentages below concern the restoring
term only, not period error, detector sensitivity or a physical regime boundary.

| Selected degrees | Sine denominator | Inclusive criterion | Angle denominator | Inclusive criterion |
|---|---|---|---|---|
""" + "\n".join(rows) + """

At 14 degrees the two criteria disagree despite both implementations functioning.
At zero both relative metrics are undefined; an absolute difference of zero does
not authorize an unstated continuous extension. No single generic MODEL_FAILED
verdict or automatic physical finding is generated.

## Process and limits

The closed arithmetic engine computes metrics only. Synthetic sine inputs are
checked against independent rational alternating-Taylor bounds before execution.
The bounds concern the exact selected binary radian input, not an interval proof
of ideal degree*pi/180 conversion. A declared 1e-14 computation tolerance is not
a physical uncertainty. Hand-stated ratio tests check arithmetic independently.

For nonzero nominal cases, both runs traverse protocol binding, formal L0, applicability, a fresh
known-answer harness and a nonzero-denominator null harness. Substitution retains
the experiment and parent digest but inherits neither a passing plan nor evidence
of adequacy. The L0 case-weight ledger is formal bookkeeping, not pendulum energy.

Labeled planted probes block period-error transfer and angle-convention changes.
A corrupted sine reference remains an instrument failure across both equations,
not a physical failure. No measurements or new external evidence are claimed.

The source claim remains UNDETERMINED as written; the denominator, explanatory
cause and physical adequacy remain unresolved. One more bounded case with planted
probes does not establish general audit accuracy. The accompanying JSON retains
hashes, runtime, replay differences, exact rational bounds and all gated runs.
"""


def run_pilot(output_dir, root=ROOT):
    output_dir = Path(output_dir).resolve()
    if output_dir == root.resolve() or root.resolve() in output_dir.parents:
        raise ValueError("Output must be outside the repository")
    examined = verify_snapshot(root)
    code = {str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "experimental/playground").rglob("*.py"))}
    output_dir.mkdir(parents=True, exist_ok=False)
    result = subprocess.run([sys.executable, "-I", str(root / CASE / "compute_review.py")],
                            check=True, capture_output=True, text=True, timeout=120)
    fresh = json.loads(result.stdout)
    (output_dir / "legacy-replay.json").write_text(result.stdout)
    preserved = json.loads((root / CASE / "results.json").read_text())
    versions = {"preserved": preserved.pop("python_version"), "fresh": fresh.pop("python_version")}
    differences = numeric_differences(preserved, fresh)
    inspection = inspect_process()
    if verify_snapshot(root) != examined or any(sha(ROOT / p) != v for p, v in code.items()):
        raise ValueError("Snapshot or diagnostic code changed during pilot")
    report = {
        "schema": VERSION, "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "platform": platform.platform(),
        "pinned_sha256": examined, "diagnostic_code_sha256": code,
        "source_inspection": json.loads((root / SOURCE).read_text()), "selection": plain(DECISION),
        "original_snapshot_unchanged": True,
        "legacy_comparison": {
            "byte_identical": sha(output_dir / "legacy-replay.json") == PINNED[f"{CASE}/results.json"],
            "fresh_sha256": sha(output_dir / "legacy-replay.json"),
            "preserved_sha256": PINNED[f"{CASE}/results.json"],
            "numeric_differences": differences, "runtime_versions": versions,
            "policy": "Only python_version is excluded and retained separately; all remaining fields use float-replay/1 (absolute/relative 1e-12), exact structure/types/text/integers/bools.",
        },
        "oracle_policy": {
            "method": "Exact rational alternating sine series, degree-23 lower / degree-25 upper, on selected binary radians in [0,0.6].",
            "metric_computation_tolerance": NUMERIC_TOLERANCE,
            "meaning": "Computational comparisons only, never physical uncertainty, sensitivity, or a period-error bound.",
        },
        "inspection": inspection,
    }
    (output_dir / "pendulum-audit-process-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    (output_dir / "pendulum-audit-process-report.md").write_text(markdown_report(report))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report = run_pilot(args.output_dir)
    print(json.dumps({
        "report": str(args.output_dir / "pendulum-audit-process-report.json"),
        "legacy_comparison": report["legacy_comparison"],
        "cases": [{"degrees": c["selected_degrees"],
                   "criteria": {k: m["inclusive_selected_criterion"] for k, m in c["metrics"].items()}}
                  for c in report["inspection"]["cases"]],
        "source_claim_status": report["inspection"]["source_claim_status"],
        "physical_status": report["inspection"]["physical_status"],
    }, indent=2, allow_nan=False))
