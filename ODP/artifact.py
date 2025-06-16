# artifact.py
from dataclasses import dataclass, field
from typing import List, Any, Tuple
from .behavior import CommunityRole


@dataclass(frozen=True)
class Property:
    """
    Represents a property of an artifact.
    """

    name: str
    type_hint: Any

    def __repr__(self):
        return f"Property(name={self.name!r}, type_hint={self.type_hint!r})"

    def __str__(self):
        return f"{self.name} ({self.type_hint})"


@dataclass(frozen=True)
class Artifact:
    """
    A role (with respect to that action) in which the enterprise object fulfilling
    the role is referenced in the action. That object may be called an artefact. (Clause 6.3.3)
    """

    name: str
    parties: Tuple[CommunityRole, ...] = field(default_factory=tuple)
    properties: Tuple[Property, ...] = field(default_factory=tuple)

    def __repr__(self):
        return f"Artifact(name={self.name!r}, parties={self.parties!r}, properties={self.properties!r})"

    def __str__(self):
        return f"{self.name}"
