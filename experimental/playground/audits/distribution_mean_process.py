"""CONSTRUCTED finite-distribution to mean-only substitution audit.

Two weighted atoms, two closed target calculations, no temporal-process model.
No observed data, physical adequacy, stationarity, ergodicity or equilibrium.
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
from ..equations.substitution import ExperimentalDiagnostics, RunState, ValidationPlan, execute, substitute
from ..failures import Axis, EvidenceRef, FailureRecord, Finding, Status
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase


DECISION = Decision(
    "constructed-distribution-mean-audit",
    "Determine whether replacing a selected finite weighted distribution by its mean preserves a declared target.",
    "Scope the operation before evaluation; retain source atoms, weights, information loss and unresolved conditions.",
)


class Purpose(str, enum.Enum):
    LINEAR = "weighted mean of the response 2X"
    SQUARE = "weighted mean of the response X squared"


class Conclusion(str, enum.Enum):
    PRESERVED = "purpose-preserved-in-constructed-case"
    LOSS = "purpose-information-loss-in-constructed-case"
    WITHHELD = "determination-withheld"


def _text(value, *, optional=False):
    if optional and value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise ValueError("nonempty text or explicitly permitted None required")
    if value.strip().casefold() in ("unknown", "none", "undeclared", "n/a"):
        raise ValueError("use None for unknown, not a textual sentinel")


def _provenance(decision, evidence):
    if not isinstance(decision, Decision):
        raise ValueError("selection decision required")
    if not isinstance(evidence, tuple) or not evidence:
        raise ValueError("immutable nonempty evidence required")
    for item in evidence:
        if not isinstance(item, EvidenceRef):
            raise ValueError("typed evidence required")
        _text(item.kind)
        _text(item.locator)
        if item.digest is not None:
            _text(item.digest)


@dataclass(frozen=True)
class Atom:
    value: int | None
    weight: int | None

    def __post_init__(self):
        for value, bound in ((self.value, 10), (self.weight, 100)):
            if value is not None and (type(value) is not int or abs(value) > bound):
                raise ValueError("bounded integer or None required; booleans are not numbers")


@dataclass(frozen=True)
class Distribution:
    source_id: str
    population: str
    window: str
    domain: str
    atoms: tuple[Atom, Atom]
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        for value in (self.source_id, self.population, self.window, self.domain):
            _text(value)
        if (not isinstance(self.atoms, tuple) or len(self.atoms) != 2
                or any(type(a) is not Atom for a in self.atoms)):
            raise ValueError("exactly two immutable typed atoms required")
        _provenance(self.decision, self.evidence)

    def digest(self):
        return digest_record(self)


@dataclass(frozen=True)
class Question:
    purpose: Purpose | None
    population: str | None
    window: str | None
    domain: str | None
    conditions: tuple[str, ...] | None
    decision: Decision
    evidence: tuple[EvidenceRef, ...]

    def __post_init__(self):
        if self.purpose is not None and not isinstance(self.purpose, Purpose):
            raise ValueError("typed purpose or None required")
        for value in (self.population, self.window, self.domain):
            _text(value, optional=True)
        if self.conditions is not None:
            if not isinstance(self.conditions, tuple) or not self.conditions:
                raise ValueError("explicit immutable conditions or None required")
            for value in self.conditions:
                _text(value)
        _provenance(self.decision, self.evidence)

    def digest(self):
        return digest_record(self)


CONDITIONS = ("constructed dimensionless exact weighted atoms", "finite-window marginal only")
REFERENCE = (EvidenceRef("constructed-definition", "audits.distribution_mean_process:fixtures"),)


def fixture_distribution(*, values=(0, 2), weights=(1, 1), source_id="broad"):
    if len(values) != 2 or len(weights) != 2:
        raise ValueError("exactly two values and weights required")
    return Distribution(
        source_id, "selected constructed population", "selected finite window W",
        "selected dimensionless domain", tuple(Atom(v, w) for v, w in zip(values, weights)),
        DECISION, REFERENCE,
    )


def fixture_question(purpose):
    return Question(purpose, "selected constructed population", "selected finite window W",
                    "selected dimensionless domain", CONDITIONS, DECISION, REFERENCE)


def evidence(source, question):
    return (
        EvidenceRef("constructed-distribution", source.source_id, source.digest()),
        EvidenceRef("selected-question", "distribution-to-mean", question.digest()),
    )


def finding(source, question, code, message, severity=Status.FAILED):
    return Finding(Axis.DETERMINATION, severity, code, message,
                   "audits.distribution_mean_process", evidence(source, question))


def source_parameters(source):
    """Exact selected weights, not sample estimates or inferred probabilities."""
    weights = tuple(a.weight for a in source.atoms)
    values = tuple(a.value for a in source.atoms)
    total = None if None in weights else sum(weights)
    result = {"total_weight": total, "p": None, "m": None, "second": None, "variance": None}
    if None in weights or any(w < 0 for w in weights) or not total or None in values:
        return result
    p = Fraction(weights[0], total)
    mean = p * values[0] + (1 - p) * values[1]
    second = p * values[0] ** 2 + (1 - p) * values[1] ** 2
    return dict(result, p=p, m=mean, second=second, variance=second - mean ** 2)


def source_record(source, question):
    record = FailureRecord()
    for atom in source.atoms:
        if atom.weight is not None and atom.weight < 0:
            record = record.with_finding(finding(
                source, question, "MEAN_NEGATIVE_WEIGHT", "negative source mass is not an admissible weighted distribution"))
        if atom.weight is None or atom.value is None:
            record = record.with_finding(finding(
                source, question, "MEAN_SOURCE_UNKNOWN", "source value or weight remains unknown",
                Status.INDETERMINATE))
    if all(a.weight is not None for a in source.atoms) and sum(a.weight for a in source.atoms) == 0:
        record = record.with_finding(finding(
            source, question, "MEAN_EMPTY_MASS", "explicit total mass zero: normalized mean is undefined",
            Status.INDETERMINATE))
    return record


def experiment(source, question, *, overrides=None):
    base = fixture_experiment()
    parameters = source_parameters(source)
    numeric = {
        "x0": source.atoms[0].value, "x1": source.atoms[1].value,
        "p": None if parameters["p"] is None else float(parameters["p"]),
        "m": None if parameters["m"] is None else float(parameters["m"]),
    }
    numeric.update(overrides or {})
    conditions = tuple(
        Condition(key, Domain.RELATIONSHIPS, value, ConditionBasis.DERIVED, DECISION,
                  "1", None if value is None else 0.0, evidence(source, question))
        for key, value in numeric.items()
    ) + tuple(
        Condition(key, domain, value, ConditionBasis.SELECTED, DECISION,
                  evidence=evidence(source, question))
        for key, domain, value in (
            ("distribution_digest", Domain.RELATIONSHIPS, source.digest()),
            ("question_digest", Domain.CONTROL, question.digest()),
            ("selected_purpose", Domain.CONTROL, None if question.purpose is None else question.purpose.value),
            ("selected_population", Domain.RELATIONSHIPS, question.population),
            ("selected_window", Domain.CONTROL, question.window),
            ("selected_domain", Domain.ENVIRONMENT, question.domain),
            ("selected_conditions", Domain.CONTROL,
             None if question.conditions is None else json.dumps(question.conditions)),
        )
    )
    context = replace(
        base.context, context_id="constructed-distribution-to-mean",
        conditions=base.context.conditions + conditions,
        uncertainty_notes="Exact constructed weights/values, not measured data; float arithmetic tolerance is not physical uncertainty.",
    )
    record = source_record(source, question)
    diagnostics = () if not record.findings else (
        ExperimentalDiagnostics(context.digest(), record, DECISION, evidence(source, question)),)
    return replace(base, context=context,
                   boundary=replace(base.boundary, context_digest=context.digest()),
                   diagnostics=diagnostics)


FORMULAS = {
    (Purpose.LINEAR, False): "2*(p*x0+(1-p)*x1)",
    (Purpose.LINEAR, True): "2*m",
    (Purpose.SQUARE, False): "p*x0**2+(1-p)*x1**2",
    (Purpose.SQUARE, True): "m**2",
}


def model(source, question, exp, calculation, mean_only, *, expression=None, missing_identity=False):
    if not isinstance(calculation, Purpose) or type(mean_only) is not bool:
        raise ValueError("explicit typed candidate calculation and representation required")
    names = ("m",) if mean_only else ("x0", "x1", "p")
    formula = FORMULAS[calculation, mean_only] if expression is None else expression
    rules = fixture_equation().constraints + tuple(
        Constraint(name, Domain.RELATIONSHIPS, DECISION,
                   lower=0 if name == "p" else -10, upper=1 if name == "p" else 10, unit="1")
        for name in names
    ) + tuple(
        Constraint(key, domain, DECISION, equals=value)
        for key, domain, value in (
            ("distribution_digest", Domain.RELATIONSHIPS, source.digest()),
            ("question_digest", Domain.CONTROL, question.digest()),
            ("selected_purpose", Domain.CONTROL, calculation.value),
            ("selected_population", Domain.RELATIONSHIPS, source.population),
            ("selected_window", Domain.CONTROL, source.window),
            ("selected_domain", Domain.ENVIRONMENT, source.domain),
            ("selected_conditions", Domain.CONTROL, json.dumps(CONDITIONS)),
        )
    )
    declaration = None if missing_identity else Measurand(
        None if question.purpose is None else question.purpose.value,
        "selected finite weighted distribution response", "per total selected weight",
        question.population, question.window, exp.boundary.accounting.boundary_label,
        exp.anchor.digest(), "mean-only plug-in" if mean_only else "two-atom weighted sum",
        DECISION, evidence(source, question),
    )
    return Equation(
        "constructed-distribution-target", "mean-only" if mean_only else "full-distribution",
        "constructed candidate calculation: " + calculation.value,
        tuple(InputPort(name, name, "1") for name in names),
        (OutputPort("response", formula, "1", declaration),),
        rules, DECISION, evidence(source, question),
    )


def plan(eq, exp, calculation, mean_only):
    # These are hand-stated expectations, not values produced by eq.
    cases = (
        ("symmetric", {"x0": 0.0, "x1": 2.0, "p": 0.5, "m": 1.0}),
        ("unequal-weights", {"x0": -2.0, "x1": 2.0, "p": 0.25, "m": 1.0}),
    )
    expected = (2.0, 2.0) if calculation is Purpose.LINEAR else (
        (1.0, 1.0) if mean_only else (2.0, 4.0))
    def inputs(values):
        return {port.name: values[port.name] for port in eq.inputs}
    return ValidationPlan(
        "constructed-distribution-route-plan", eq.digest(), exp.context.digest(),
        tuple(KnownAnswerCase.from_maps(
            label, inputs(values), {"response": wanted}, {"response": 0.0},
            "CONSTRUCTED hand-stated implementation-fidelity expectation for this route",
        ) for (label, values), wanted in zip(cases, expected)),
        (NullCase.from_maps(
            "zero-response", inputs({"x0": 0.0, "x1": 0.0, "p": 0.5, "m": 0.0}),
            {"response": 0.0}, {"response": 0.0}),),
        tuple((p.name, "1") for p in eq.inputs), (("response", "1"),), DECISION, eq.evidence,
    )


def trace(run, source, question, calculation, mean_only):
    record = source_record(source, question)
    def add(code, message, severity=Status.FAILED):
        nonlocal record
        record = record.with_finding(finding(source, question, code, message, severity))
    parameters = source_parameters(source)
    values = {c.key: c for c in run.experiment.context.conditions}
    names = ("m",) if mean_only else ("x0", "x1", "p")
    expected = {
        "x0": source.atoms[0].value, "x1": source.atoms[1].value,
        "p": None if parameters["p"] is None else float(parameters["p"]),
        "m": None if parameters["m"] is None else float(parameters["m"]),
    }
    if (type(run.equation) is not Equation
            or tuple((p.name, p.context_key, p.unit) for p in run.equation.inputs)
            != tuple((name, name, "1") for name in names)
            or len(run.equation.outputs) != 1
            or (run.equation.outputs[0].name, run.equation.outputs[0].unit,
                run.equation.outputs[0].expression)
            != ("response", "1", FORMULAS[calculation, mean_only])):
        add("MEAN_UNSUPPORTED_PROCEDURE", "outside the closed representation/target calculation",
            Status.INDETERMINATE)
    for key, wanted in (
        ("distribution_digest", source.digest()), ("question_digest", question.digest()),
    ):
        condition = values.get(key)
        if (condition is None or condition.value != wanted
                or any(e not in condition.evidence for e in evidence(source, question))):
            add("MEAN_SOURCE_BINDING", f"{key}: supplied records do not match run provenance")
    # Check the entire reduction derivation, even where a route does not use m.
    for name, wanted in expected.items():
        condition = values.get(name)
        if wanted is None:
            add("MEAN_OPERAND_UNKNOWN", f"{name}: unresolved source-derived operand", Status.INDETERMINATE)
        elif (condition is None or condition.value != wanted or condition.unit != "1"
              or any(e not in condition.evidence for e in evidence(source, question))):
            add("MEAN_OPERAND_BINDING", f"{name}: operand disagrees with source derivation/provenance")
    if run.state is RunState.COMPUTED:
        if dict(run.inputs) != {name: expected[name] for name in names}:
            add("MEAN_EXECUTED_INPUTS", "retained executed operands disagree with the source reduction")
        if parameters["m"] is not None:
            mean = parameters["m"]
            oracle = (2 * mean if calculation is Purpose.LINEAR else (
                mean ** 2 if mean_only else parameters["second"]))
            if (len(run.outputs) != 1 or run.outputs[0].name != "response"
                    or not math.isclose(run.outputs[0].value, float(oracle), rel_tol=1e-12, abs_tol=1e-12)):
                add("MEAN_POINT_ORACLE", "retained point differs from the exact finite-weight route oracle")
    return {
        "run_digest": run.digest(), "source_digest": source.digest(), "question_digest": question.digest(),
        "representation": "mean-only" if mean_only else "full-distribution",
        "calculation": calculation.value, "qualified_within_constructed_scope": not record.findings,
        "record": record,
    }


def audit_pair(previous, replacement, source, question, calculation):
    generic = compare_substitution(previous, replacement, "response", "response", DECISION)
    traces = (trace(previous, source, question, calculation, False),
              trace(replacement, source, question, calculation, True))
    record = generic.record.merge(traces[0]["record"]).merge(traces[1]["record"])
    unresolved = []
    for key, wanted in (("population", source.population), ("window", source.window),
                        ("domain", source.domain), ("conditions", CONDITIONS), ("purpose", calculation)):
        supplied = getattr(question, key)
        if supplied is None:
            unresolved.append(key)
            record = record.with_finding(finding(
                source, question, "MEAN_SCOPE_UNKNOWN", f"{key}: undeclared; no default supplied",
                Status.INDETERMINATE))
        elif supplied != wanted:
            unresolved.append(key)
            record = record.with_finding(finding(
                source, question, "MEAN_SCOPE_MISMATCH", f"{key}: selected question differs from source/procedure"))
    state, usable, difference, exact_error = Conclusion.WITHHELD, None, None, None
    parameters = source_parameters(source)
    if (not unresolved and all(t["qualified_within_constructed_scope"] for t in traces)
            and generic.state is ComparisonState.ELIGIBLE):
        mean = parameters["m"]
        exact_error = Fraction(0) if calculation is Purpose.LINEAR else mean ** 2 - parameters["second"]
        difference = generic.point_difference
        usable = exact_error == 0
        state = Conclusion.PRESERVED if usable else Conclusion.LOSS
        record = record.with_finding(finding(
            source, question, "MEAN_PURPOSE_PRESERVED" if usable else "MEAN_PURPOSE_LOSS",
            "Mean-only substitution preserves this selected finite-sum target in this case"
            if usable else "Mean-only substitution does not preserve this selected finite-sum target in this case",
            Status.OK if usable else Status.FAILED))
    return {
        "source": source, "source_digest": source.digest(),
        "question": question, "question_digest": question.digest(),
        "operation": "replace selected weighted marginal by a point at its weighted mean",
        "candidate_calculation": calculation.value,
        "declaration_comparison": generic.to_dict(), "procedure_traces": traces,
        "conclusion": state.value, "usable_for_selected_target_in_this_case": usable,
        "audited_point_difference": difference,
        "exact_replacement_minus_reference": None if exact_error is None else str(exact_error),
        "source_moments": {k: None if v is None else str(v) for k, v in parameters.items()},
        "information_not_carried_by_replacement": (
            "original atom values and weights as separate calculation operands",
            "within-distribution spread and support structure beyond the mean",
        ),
        "temporal_order": "NOT_SUPPLIED", "joint_structure": "NOT_SUPPLIED",
        "property_inferences": {name: "NOT_ESTABLISHED" for name in (
            "stationarity", "ergodicity", "thermodynamic_equilibrium", "physical_absence")},
        "scope_unresolved_or_mismatched": tuple(unresolved),
        "universal_mean_sufficiency": "NOT_ESTABLISHED",
        "record": record, "axis_statuses": {a.value: record.status_for(a).value for a in Axis},
        "physical_adequacy": record.physical.value.upper(), "empirical_support": "NOT_PROMOTED",
    }


def run_case(source, question, *, calculation, overrides=None, expression=None, missing_identity=False):
    if not isinstance(calculation, Purpose):
        raise ValueError("candidate calculation must be explicit; never inferred from missing scope")
    exp = experiment(source, question, overrides=overrides)
    first = model(source, question, exp, calculation, False)
    second = model(source, question, exp, calculation, True, expression=expression,
                   missing_identity=missing_identity)
    registry = EquationRegistry()
    registry.register(first)
    registry.register(second)
    a = execute(registry, first.equation_id, first.revision, exp,
                plan(first, exp, calculation, False), DECISION)
    b = substitute(a, registry, second.equation_id, second.revision,
                   plan(second, exp, calculation, True), DECISION)
    return a, b, audit_pair(a, b, source, question, calculation)


def plain(value):
    return json.loads(json.dumps(value, allow_nan=False,
                                default=lambda v: v.value if isinstance(v, enum.Enum) else asdict(v)))


def inspect_process():
    broad = fixture_distribution()
    narrow = fixture_distribution(values=(1, 1), source_id="point-at-one")
    linear = fixture_question(Purpose.LINEAR)
    square = fixture_question(Purpose.SQUARE)
    def case(source, question, calculation, **kwargs):
        return run_case(source, question, calculation=calculation, **kwargs)[2]
    cases = {
        "broad_linear_control": case(broad, linear, Purpose.LINEAR),
        "same_mean_narrow_linear_control": case(narrow, linear, Purpose.LINEAR),
        "broad_second_moment_loss": case(broad, square, Purpose.SQUARE),
        "same_mean_degenerate_second_moment_coincidence": case(narrow, square, Purpose.SQUARE),
        "unequal_weights_second_moment_loss": case(
            fixture_distribution(values=(-2, 2), weights=(1, 3), source_id="asymmetric"),
            square, Purpose.SQUARE),
        "zero_mean_is_not_zero_response": case(
            fixture_distribution(values=(-1, 1), source_id="zero-mean"), square, Purpose.SQUARE),
        "zero_point_is_not_physical_absence": case(
            fixture_distribution(values=(0, 0), source_id="zero-point"), square, Purpose.SQUARE),
        "purpose_unknown_not_defaulted": case(broad, replace(square, purpose=None), Purpose.SQUARE),
        "window_unknown_not_defaulted": case(broad, replace(square, window=None), Purpose.SQUARE),
        "population_mismatch_preserved": case(
            broad, replace(square, population="another selected population"), Purpose.SQUARE),
        "unknown_weight_not_zero": case(
            fixture_distribution(weights=(1, None), source_id="unknown-weight"), square, Purpose.SQUARE),
        "zero_total_mass_undefined": case(
            fixture_distribution(weights=(0, 0), source_id="empty-mass"), square, Purpose.SQUARE),
        "false_mean_derivation": case(broad, square, Purpose.SQUARE, overrides={"m": 2.0}),
        "unsupported_equivalent_expression_withheld": case(
            broad, linear, Purpose.LINEAR, expression="m+m"),
    }
    return plain({
        "schema": "playground/distribution-to-mean-audit/1",
        "status": "CONSTRUCTED_DISTRIBUTION_TO_MEAN_AUDIT",
        "implementation": {
            "python": sys.version,
            "source_hashes": {
                name: hashlib.sha256((Path(__file__).resolve().parents[1] / name).read_bytes()).hexdigest()
                for name in ("audits/distribution_mean_process.py", "equations/adapter.py",
                             "equations/substitution.py", "equations/measurand.py",
                             "applicability/mapping.py", "failures.py")
            },
        },
        "cases": cases,
        "limits": (
            "Constructed two-atom marginal distributions; no observed samples or physical calibration.",
            "Arithmetic preservation is purpose- and case-qualified, not a universal model ranking.",
            "Marginal data supply neither temporal order nor joint dependence; those are not inferred absent.",
            "Stationarity, ergodicity and thermodynamic equilibrium are neither assumed nor established.",
            "Arithmetic tolerances do not quantify physical uncertainty; output uncertainty remains None.",
        ),
    })


def markdown_report(report):
    rows = []
    for name, case in report["cases"].items():
        rates = []
        for side in ("previous", "replacement"):
            outputs = case["declaration_comparison"][side]["outputs"]
            rates.append(str(outputs[0]["value"]) if outputs else "not computed")
        rows.append(f'| {name} | {rates[0]} | {rates[1]} | {case["conclusion"]} |')
    return (
        "# Distribution-to-mean substitution test\n\n"
        "Status: CONSTRUCTED finite-distribution audit. No physical adequacy or empirical support "
        "is established; stationarity, ergodicity and equilibrium are not inferred.\n\n"
        "Equal-weight distributions at (0, 2) and (1, 1) both have mean 1. "
        "For the selected response 2X, their weighted responses and mean-only replacements "
        "are all 2. For the selected response X squared, the full responses are 2 and 1 "
        "while both mean-only responses are 1. The degenerate coincidence does not "
        "license replacement for a distribution with spread.\n\n"
        "| Case | Full-distribution raw response | Mean-only raw response | Determination |\n"
        "|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Both routes retain the same declared target; the mean-only route is an attempted "
        "approximation, not a relabeling of the squared mean as the weighted second moment. "
        "Correct arithmetic can coexist with a failed substitution determination. The JSON "
        "retains complete runs, original atoms and weights, selected scope, decisions, "
        "exact moment diagnostics, provenance, comparisons and unresolved findings.\n\n"
        "## This does not establish\n\n"
        "This tests two closed calculations on constructed two-atom marginal distributions, "
        "not general sufficiency of a mean, a physical model hierarchy, causal validity, "
        "detector sensitivity or physical absence. No temporal or joint data are supplied; "
        "their absence from the record is not evidence that the physical dependencies are absent. "
        "A preserved target in one case is not future or universal equivalence.\n"
    )


def run_audit(output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    report = inspect_process()
    (output_dir / "distribution-to-mean-audit.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    (output_dir / "distribution-to-mean-audit.md").write_text(markdown_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run_audit(args.output_dir)
    print(f'{result["status"]}: {len(result["cases"])} cases; physical adequacy UNTESTED')
