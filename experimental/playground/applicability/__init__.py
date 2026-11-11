"""Context-dependent applicability records, not a physics oracle or ranking."""

from .mapping import (
    ApplicabilityMap, ApplicabilityResult, ApplicabilityState, Assessment,
    Condition, ConditionBasis, Constraint, Context, Decision, Description,
    Domain, EvidenceKind, Judgment, ScopeState, assess, build_map,
)

__all__ = [
    "ApplicabilityMap", "ApplicabilityResult", "ApplicabilityState", "Assessment",
    "Condition", "ConditionBasis", "Constraint", "Context", "Decision",
    "Description", "Domain", "EvidenceKind", "Judgment", "ScopeState",
    "assess", "build_map",
]
