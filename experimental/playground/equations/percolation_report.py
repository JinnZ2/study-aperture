"""Views over completed gated runs, not another graph execution entry point."""

from __future__ import annotations

from dataclasses import asdict, replace

from ..applicability.mapping import Decision
from ..validation.numeric_contract import finite_number
from .adapter import digest_record
from .percolation import BondPercolation
from .substitution import EquationRun, RunState


LIMITS = (
    "The graph, its boundary sets, and occupation law are selected mathematical definitions, not physical facts.",
    "A disconnected supplied mask does not establish absent physical coupling or observer sensitivity.",
    "The independent uniform bond ensemble is not a sampling provenance claim about the supplied mask.",
    "Enumeration covers all masks of this finite graph; floating-point arithmetic and input uncertainty remain.",
    "No physical transition, thermodynamic threshold, continuity, or permanent organization is inferred.",
)


def _completed(run: EquationRun) -> None:
    if (not isinstance(run, EquationRun) or type(run.equation) is not BondPercolation
            or run.state is not RunState.COMPUTED):
        raise ValueError("a completed diagnostic-gated finite-bond run is required")


def percolation_report(run: EquationRun) -> dict:
    """Recover labeled components from the backend's recorded outputs only."""
    _completed(run)
    values = {v.name: v.value for v in run.outputs}
    graph = run.equation.graph
    groups: dict[int, list[str]] = {}
    for i, node in enumerate(graph.nodes):
        groups.setdefault(int(values[f"component_{i}"]), []).append(node)
    return {
        "schema": "playground/finite-bond-report/1",
        "run_digest": run.digest(),
        "graph_digest": graph.digest(),
        "realization": {
            "occupation_mask": dict(run.inputs)["mask"],
            "components": list(groups.values()),
            "spanning": bool(values["spanning"]),
            "component_count": values["component_count"],
            "largest_component_size": values["largest_component_size"],
            "occupied_edge_count": values["occupied_edge_count"],
        },
        "independent_bond_ensemble": {
            "p": dict(run.inputs)["p"],
            "enumerated_states": 1 << len(graph.edges),
            "spanning_probability": values["spanning_probability"],
            "expected_component_count": values["expected_component_count"],
            "expected_largest_component_size": values["expected_largest_component_size"],
        },
        "applicability": run.applicability.state.value,
        "physical_status": run.record.physical.value,
        "output_uncertainty": None,
        "limits": list(LIMITS),
    }


def _fixed_experiment_digest(run: EquationRun) -> str:
    context = replace(run.experiment.context, conditions=tuple(
        replace(c, value=0.0) if c.key == "bond_probability" else c
        for c in run.experiment.context.conditions
    ))
    return digest_record(replace(
        run.experiment, context=context,
        boundary=replace(run.experiment.boundary, context_digest=context.digest()),
        diagnostics=tuple(replace(d, context_digest=context.digest())
                          for d in run.experiment.diagnostics),
    ))


def finite_transition_bracket(
    runs: tuple[EquationRun, ...], target: float, selection: Decision,
) -> dict:
    """Bracket a SELECTED finite-ensemble probability level on the supplied grid.

    This does not calculate new graph points, interpolate, estimate an infinite-
    size critical point, or promote the per-point physical assessments.
    Runs must differ only in nominal p; nonzero p uncertainty is not propagated
    and is therefore rejected here rather than hidden in a crisp bracket.
    """
    if not isinstance(runs, tuple) or len(runs) < 2:
        raise ValueError("at least two immutable gated grid points required")
    if not finite_number(target) or not 0 < target < 1 or not isinstance(selection, Decision):
        raise ValueError("an explicit interior probability criterion and selection provenance required")
    for run in runs:
        _completed(run)
        condition = next(c for c in run.experiment.context.conditions if c.key == "bond_probability")
        if condition.uncertainty != 0:
            raise ValueError("finite-grid brackets do not propagate p uncertainty")
    equation_digest = runs[0].equation.digest()
    fixed_digest = _fixed_experiment_digest(runs[0])
    if any(run.equation.digest() != equation_digest
           or _fixed_experiment_digest(run) != fixed_digest
           or run.dependency_states != runs[0].dependency_states for run in runs):
        raise ValueError("grid points must retain the same adapter and experiment except nominal p")
    points = tuple((dict(r.inputs)["p"], {v.name: v.value for v in r.outputs}[
        "spanning_probability"
    ]) for r in runs)
    if any(a[0] >= b[0] for a, b in zip(points, points[1:])):
        raise ValueError("probability grid must be strictly increasing without duplicates")
    if any(a[1] > b[1] + 1e-12 for a, b in zip(points, points[1:])):
        raise ValueError("nonmonotone outputs contradict this backend's declared ensemble")
    bracket = None
    if points[0][1] >= target:
        status = "criterion-already-met-at-grid-start"
    else:
        status = "criterion-not-reached-on-supplied-grid"
        for a, b in zip(points, points[1:]):
            if a[1] < target <= b[1]:
                bracket = [a[0], b[0]]
                status = "finite-grid-bracket"
                break
    return {
        "schema": "playground/finite-bond-grid-bracket/1",
        "status": status,
        "selected_spanning_probability": target,
        "selection": asdict(selection),
        "p_bracket": bracket,
        "points": [{"p": p, "spanning_probability": q} for p, q in points],
        "run_digests": [r.digest() for r in runs],
        "equation_digest": equation_digest,
        "fixed_experiment_digest": fixed_digest,
        "uncertainty_propagated": False,
        "limits": list(LIMITS) + [
            "The bracket is a grid resolution, not a confidence interval.",
            "No interpolation, extrapolation, threshold uniqueness, or physical adequacy is established.",
            "An unmet criterion is not proof that a transition or physical connection is absent.",
        ],
    }
