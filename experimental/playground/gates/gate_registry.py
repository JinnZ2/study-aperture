"""Registry of gates and the pipeline stages they guard."""

from __future__ import annotations

from dataclasses import dataclass

from ..failures import Axis

PIPELINE_STAGES: tuple[str, ...] = (
    "experimental_definition",
    "anchor_freeze",
    "boundary_specification",
    "control_specification",
    "l0_closure",
    "known_answer_and_null_harness",
    "equation_selection",
    "experimental_execution",
    "observer_regime_assessment",
    "uncertainty_and_claim_provenance",
    "boundary_and_transition_analysis",
    "return_to_anchor",
    "misclosure_calculation",
    "context_dependent_applicability",
)
"""Ordered stages of the gated workflow. Informational in milestone 1."""


@dataclass(frozen=True)
class GateSpec:
    gate_id: str
    stage: str
    question: str
    can_emit: tuple[Axis, ...]
    module: str


_REGISTRY: dict[str, GateSpec] = {}


def register(spec: GateSpec) -> GateSpec:
    if spec.gate_id in _REGISTRY:
        raise ValueError(f"gate '{spec.gate_id}' is already registered")
    if spec.stage not in PIPELINE_STAGES:
        raise ValueError(f"unknown pipeline stage '{spec.stage}'")
    _REGISTRY[spec.gate_id] = spec
    return spec


def get(gate_id: str) -> GateSpec:
    return _REGISTRY[gate_id]  # KeyError is the honest failure


def all_gates() -> tuple[GateSpec, ...]:
    return tuple(_REGISTRY.values())
