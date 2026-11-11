"""The continuity matrix: system persistence versus configuration persistence.

Two questions, answered separately, never merged:

- Did the system return to its anchor state? (system persistence)
- Did the system's configuration — its declared arrangement and
  relationships — persist through the perturbation? (configuration
  persistence)

A system can return to its anchor state while its configuration changed,
and a system can change its state while its configuration persists. The
four cells of the matrix are distinct outcomes, not a ranking, and an
indeterminate component yields an indeterminate cell — the classification
refuses to project an incomplete observation onto a definite cell.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Mapping


class SystemPersistence(enum.Enum):
    PERSISTED = "persisted"
    CHANGED = "changed"
    INDETERMINATE = "indeterminate"


class ConfigurationPersistence(enum.Enum):
    PERSISTED = "persisted"
    CHANGED = "changed"
    INDETERMINATE = "indeterminate"


class ContinuityCell(enum.Enum):
    CONTINUOUS = "continuous"
    RETURN_WITH_RECONFIGURATION = "return-with-reconfiguration"
    DRIFT_WITH_STABLE_CONFIGURATION = "drift-with-stable-configuration"
    DISCONTINUOUS = "discontinuous"
    INDETERMINATE = "indeterminate"


_CELL: dict[
    tuple[SystemPersistence, ConfigurationPersistence], ContinuityCell
] = {
    (SystemPersistence.PERSISTED, ConfigurationPersistence.PERSISTED): (
        ContinuityCell.CONTINUOUS
    ),
    (SystemPersistence.PERSISTED, ConfigurationPersistence.CHANGED): (
        ContinuityCell.RETURN_WITH_RECONFIGURATION
    ),
    (SystemPersistence.CHANGED, ConfigurationPersistence.PERSISTED): (
        ContinuityCell.DRIFT_WITH_STABLE_CONFIGURATION
    ),
    (SystemPersistence.CHANGED, ConfigurationPersistence.CHANGED): (
        ContinuityCell.DISCONTINUOUS
    ),
}


def classify_continuity(
    system: SystemPersistence, configuration: ConfigurationPersistence
) -> ContinuityCell:
    """Classify the continuity cell from the two persistence questions.

    Any indeterminate component yields INDETERMINATE; the classification
    never projects an incomplete observation onto a definite cell.
    """
    if system is SystemPersistence.INDETERMINATE or (
        configuration is ConfigurationPersistence.INDETERMINATE
    ):
        return ContinuityCell.INDETERMINATE
    return _CELL[(system, configuration)]


@dataclass(frozen=True)
class ConfigurationObservation:
    """A declared configuration: the arrangement and relationships, as recorded."""

    label: str
    entries: tuple[tuple[str, str], ...]

    @classmethod
    def from_map(
        cls, label: str, entries: Mapping[str, str]
    ) -> "ConfigurationObservation":
        return cls(label=label, entries=tuple(sorted(entries.items())))

    def as_dict(self) -> dict[str, str]:
        return dict(self.entries)


def compare_configurations(
    before: ConfigurationObservation, after: ConfigurationObservation
) -> ConfigurationPersistence:
    """Same keys and values -> persisted; any difference -> changed.

    A difference is a recorded fact about the configuration, not a failure.
    """
    if before.entries == after.entries:
        return ConfigurationPersistence.PERSISTED
    return ConfigurationPersistence.CHANGED
