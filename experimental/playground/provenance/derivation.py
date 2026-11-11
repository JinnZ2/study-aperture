"""Derivations: every step is justified or explicitly an assumption.

The failure mode this module guards against is the unstated assumption: a
step that looks derived but has no recorded justification or source.
validate() returns the problems rather than raising, so an incomplete
derivation is recorded as incomplete, not silently rejected or accepted.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DerivationStep:
    statement: str
    justification: str | None = None
    source: str | None = None
    is_assumption: bool = False

    def __post_init__(self) -> None:
        if self.is_assumption and (self.justification or self.source):
            raise ValueError(
                "An assumption is not justified; mark it as derived instead."
            )


@dataclass(frozen=True)
class Derivation:
    steps: tuple[DerivationStep, ...] = ()

    def validate(self) -> tuple[str, ...]:
        problems: list[str] = []
        for i, step in enumerate(self.steps):
            if step.is_assumption:
                continue
            if not step.justification or not step.source:
                problems.append(
                    f"step {i} ('{step.statement}') has no recorded "
                    f"justification/source and is not marked as an assumption"
                )
        return tuple(problems)

    def assumptions(self) -> tuple[DerivationStep, ...]:
        return tuple(s for s in self.steps if s.is_assumption)

    def cited_sources(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(s.source for s in self.steps if s.source))
