"""CONSTRUCTED substitution challenge, not new measurements or physical evidence."""

import argparse
import json
from dataclasses import replace
from pathlib import Path

from ..applicability.example import DECISION
from ..failures import EvidenceRef
from ..validation.known_answer import KnownAnswerCase
from ..validation.null_harness import NullCase
from .adapter import EquationRegistry, OutputPort
from .example import fixture_equation, fixture_experiment, fixture_plan
from .measurand import Measurand, compare_substitution
from .substitution import execute, substitute


def declaration(experiment) -> Measurand:
    return Measurand(
        quantity="constructed finite-window response energy",
        object_of="selected-cell-A",
        normalizer="raw",
        population="selected-cell-A cohort",
        time_window="selected t0-to-t1 window",
        spatial_scope=experiment.boundary.accounting.boundary_label,
        reference_state=experiment.anchor.digest(),
        protocol="constructed arithmetic route A",
        decision=DECISION,
        evidence=(EvidenceRef("constructed-identity", "equations.measurand_example:declaration"),),
    )


def model(identity, *, expression="x", revision="base", output="y"):
    return replace(
        fixture_equation(expression, revision, "measurand-challenge"),
        outputs=(OutputPort(output, expression, "toy-energy-unit", identity),),
    )


def plan(equation, experiment, expected=(1.0, 2.0)):
    """Hand-selected expectations, not values calculated from the tested formula."""
    name = equation.outputs[0].name
    return replace(
        fixture_plan(equation, experiment),
        known_answers=tuple(
            KnownAnswerCase.from_maps(
                f"constructed-{x:g}", {"x": x}, {name: y}, {name: 0.0},
                "CONSTRUCTED hand-stated expectation, not empirical evidence",
            ) for x, y in zip((1.0, 2.0), expected)
        ),
        nulls=(NullCase.from_maps("zero", {"x": 0.0}, {name: 0.0}, {name: 0.0}),),
        output_units=((name, "toy-energy-unit"),),
    )


def run_pair(left, right, *, experiment=None, expression="x/2+x/2",
             expected=(1.0, 2.0), output="y"):
    experiment = fixture_experiment() if experiment is None else experiment
    first = model(left)
    second = model(right, expression=expression, revision="replacement", output=output)
    registry = EquationRegistry()
    registry.register(first)
    registry.register(second)
    a = execute(registry, first.equation_id, first.revision, experiment,
                plan(first, experiment), DECISION)
    b = substitute(a, registry, second.equation_id, second.revision,
                   plan(second, experiment, expected), DECISION)
    return a, b, compare_substitution(a, b, "y", output, DECISION)


def inspect_identity():
    experiment = fixture_experiment()
    original = declaration(experiment)
    cases = {}
    variants = {
        "same_identity_different_route": replace(original, protocol="constructed route B"),
        "different_quantity": replace(original, quantity="constructed stored energy"),
        "different_object": replace(original, object_of="sensor-assembly-A"),
        "different_normalizer": replace(original, normalizer="per selected member"),
        "different_population": replace(original, population="all registered cells"),
        "different_window": replace(original, time_window="selected t1-to-t2 window"),
        "different_spatial_scope": replace(original, spatial_scope="sensor footprint"),
        "different_reference": replace(original, reference_state="another selected reference"),
        "missing_normalizer": replace(original, normalizer=None),
        "same_identity_missing_route": replace(original, protocol=None),
        "known_mismatch_and_missing_field": replace(
            original, object_of="sensor-assembly-A", normalizer=None),
    }
    for name, variant in variants.items():
        cases[name] = run_pair(original, variant, experiment=experiment)[2].to_dict()
    cases["both_legacy_declarations_missing"] = run_pair(None, None)[2].to_dict()
    cases["renamed_output_same_identity"] = run_pair(
        original, original, output="renamed_response")[2].to_dict()
    cases["same_identity_different_point_value"] = run_pair(
        original, original, expression="2*x", expected=(2.0, 4.0))[2].to_dict()
    cases["failed_known_answer_not_comparable"] = run_pair(
        original, original, expression="2*x")[2].to_dict()
    return {
        "schema": "playground/measurand-substitution-probe/1",
        "status": "CONSTRUCTED_DIAGNOSTIC_INFRASTRUCTURE_TEST",
        "physical_adequacy": "UNTESTED",
        "empirical_support": "NOT_PROMOTED",
        "source_of_identity": "SELECTED_CONSTRUCTED_DECLARATIONS_NOT_PHYSICAL_AUTHENTICATION",
        "design_reference": {
            "url": "https://raw.githubusercontent.com/JinnZ2/Simulators/34eb3cfbf42d3947092858f6b8449da550eed125/measurement-fork/README.md",
            "usage": "DESIGN_INSPIRATION_ONLY_NO_CODE_IMPORTED_OR_RUNTIME_VERIFIED",
        },
        "cases": cases,
    }


def markdown_report(report):
    rows = []
    for name, case in report["cases"].items():
        rows.append(
            f'| {name} | {case["identity"]} | {case["state"]} | '
            f'{case["point_difference"] if case["point_difference"] is not None else "withheld"} |'
        )
    return (
        "# Measurand identity under equation substitution\n\n"
        "Status: CONSTRUCTED diagnostic-infrastructure test. No physical "
        "measurement, calibration or empirical support is established.\n\n"
        "Design motivation: [Simulators measurement-fork]("
        + report["design_reference"]["url"] + "). No source code is imported "
        "from it and this probe does not verify that repository's runtime.\n\n"
        "Each replacement uses substitute() and reruns the complete diagnostic "
        "path. Comparison eligibility is a separate determination; a void "
        "comparison does not erase either calculation.\n\n"
        "| Case | Declared identity | Comparison | Point difference |\n"
        "|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "Point difference means replacement minus previous, only where licensed. "
        "The full JSON retains both run snapshots, chosen identities, routes, "
        "diagnostics, decisions, evidence references, uncertainty and lineage.\n\n"
        "## This does not establish\n\n"
        "A shared declaration is not an independently established physical fact. "
        "Different routes are recorded, not proven equivalent or calibrated. "
        "No uncertainty propagation, compatibility verdict, ratio, permanent "
        "organization, absence, lifecycle transition or claim promotion follows.\n"
    )


def run_probe(output_dir):
    report = inspect_identity()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "measurand-substitution-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "measurand-substitution-report.md").write_text(
        markdown_report(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    report = run_probe(args.output_dir)
    print(f'{report["status"]}: {len(report["cases"])} cases; physical adequacy UNTESTED')
