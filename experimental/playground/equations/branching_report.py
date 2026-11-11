"""Views of completed branching runs; no new process calculation or prediction."""

from __future__ import annotations

from dataclasses import asdict, replace

from ..applicability.mapping import Decision
from .adapter import digest_record
from .branching import MAX_POPULATION, FiniteBranching
from .substitution import EquationRun, RunState


LIMITS = (
    "Selected offspring independence and homogeneity are mathematical definitions, not empirical facts.",
    "These are finite-generation ensemble distributions, not an observed or simulated realized history.",
    "Extinction by this horizon is not observed physical extinction; survival to it is not permanent persistence.",
    "A stable expected population is not permanent organization, system continuity, or configuration continuity.",
    "No infinite-horizon survival, universal threshold, percolation equivalence, or physical adequacy is inferred.",
    "Stochastic variance is conditional on the selected law, not propagated parameter, measurement or model uncertainty.",
    "Internal integer ratios are exact; exported floats are rounded and positive underflow fails the instrument.",
)


def _completed(run: EquationRun) -> None:
    if (not isinstance(run, EquationRun) or type(run.equation) is not FiniteBranching
            or run.state is not RunState.COMPUTED):
        raise ValueError("a completed diagnostic-gated finite-branching run is required")


def branching_report(run: EquationRun) -> dict:
    _completed(run)
    values = {v.name: v.value for v in run.outputs}
    inputs = dict(run.inputs)
    law = run.equation.law
    weighted_count = sum(k * w for k, w in law.weights)
    total = sum(w for _, w in law.weights)
    relation = "equal-to-one" if weighted_count == total else (
        "less-than-one" if weighted_count < total else "greater-than-one"
    )
    return {
        "schema": "playground/finite-branching-report/1",
        "run_digest": run.digest(),
        "offspring_law_digest": law.digest(),
        "initial_population": inputs["initial"],
        "generation_horizon": inputs["generations"],
        "offspring_mean_relation_to_one": relation,
        "conditional_ensemble_metrics": {
            key: values[key] for key in (
                "offspring_mean", "offspring_variance", "expected_population", "population_variance",
                "extinction_by_horizon", "survival_at_horizon", "expected_cumulative_population", "probability_mass",
            )
        },
        "positive_population_probabilities": [
            {"population": k, "probability": values[f"population_probability_{k}"]}
            for k in range(MAX_POPULATION + 1) if values[f"population_probability_{k}"] > 0
        ],
        "applicability": run.applicability.state.value,
        "physical_status": run.record.physical.value,
        "output_uncertainty": None,
        "limits": list(LIMITS),
    }


def _fixed_experiment_digest(run: EquationRun) -> str:
    context = replace(run.experiment.context, conditions=tuple(
        replace(c, value=0.0) if c.key == "generation_horizon" else c
        for c in run.experiment.context.conditions
    ))
    return digest_record(replace(
        run.experiment, context=context,
        boundary=replace(run.experiment.boundary, context_digest=context.digest()),
        diagnostics=tuple(replace(d, context_digest=context.digest()) for d in run.experiment.diagnostics),
    ))


def generation_profile(runs: tuple[EquationRun, ...], selection: Decision) -> dict:
    """Compare consecutive finite horizons with all other conditions fixed."""
    if not isinstance(runs, tuple) or len(runs) < 2 or not isinstance(selection, Decision):
        raise ValueError("at least two immutable gated horizons and selection provenance required")
    for run in runs:
        _completed(run)
    fixed, adapter = _fixed_experiment_digest(runs[0]), runs[0].equation.digest()
    if any(_fixed_experiment_digest(r) != fixed or r.equation.digest() != adapter
           or r.dependency_states != runs[0].dependency_states for r in runs):
        raise ValueError("only the generation horizon may differ within a profile")
    reports = [branching_report(run) for run in runs]
    if any(b["generation_horizon"] != a["generation_horizon"] + 1
           for a, b in zip(reports, reports[1:])):
        raise ValueError("generation horizons must be consecutive and strictly increasing")
    if any(b["conditional_ensemble_metrics"]["extinction_by_horizon"] + 1e-12
           < a["conditional_ensemble_metrics"]["extinction_by_horizon"]
           for a, b in zip(reports, reports[1:])):
        raise ValueError("finite extinction is absorbing under this selected process definition")
    return {
        "schema": "playground/finite-branching-generation-profile/1",
        "selection": asdict(selection),
        "equation_digest": adapter,
        "fixed_experiment_digest": fixed,
        "points": reports,
        "limits": list(LIMITS) + [
            "Each point reran all diagnostics in its own bound context; no extrapolation or aggregated support.",
            "Changing an observation horizon is a determination change, not evidence of a physical transition.",
        ],
    }
