# community.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .enterprise_object import EnterpriseObject
from .event import Event
from .artifact import Artifact
from .behavior import CommunityRole
from .policy import Rule, PolicyEnvelopeConfig


@dataclass
class Community(EnterpriseObject):
    """
    (Community Object) A composite enterprise object that represents a community.
    The components of a community object are objects of the community represented. (Clause 6.2.2)
    """

    name: str
    contract: Optional[str] = field(default=None, repr=False)
    objective: str = field(default_factory=str)
    imports: List[Import] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    roles: List[CommunityRole] = field(default_factory=list)
    rules: List["Rule"] = field(default_factory=list)

    def __post_init__(self) -> None:
        """
        Initializes the index dictionaries. They will be populated by build_indexes().
        """
        self._role_index: Dict[str, CommunityRole] = {}
        self._artifact_index: Dict[str, Artifact] = {}
        self._event_index: Dict[str, Event] = {}

    def build_indexes(self):
        """
        Populates the lookup indexes for roles, artifacts, and events.
        This should be called after the community's lists are fully populated.
        """
        # Clear existing indexes to be safe
        self._role_index.clear()
        self._artifact_index.clear()
        self._event_index.clear()

        # Build role index
        for role in self.roles:
            if role.name in self._role_index:
                raise ValueError(
                    f"Duplicate role name {role.name!r} in community {self.name!r}"
                )
            self._role_index[role.name] = role

        # Build artifact index
        for art in self.artifacts:
            if art.name in self._artifact_index:
                raise ValueError(
                    f"Duplicate artifact name {art.name!r} in community {self.name!r}"
                )
            self._artifact_index[art.name] = art

        # Build event index
        for ev in self.events:
            if ev.name in self._event_index:
                raise ValueError(
                    f"Duplicate event name {ev.name!r} in community {self.name!r}"
                )
            self._event_index[ev.name] = ev

    def get_role(self, name: str) -> Optional[CommunityRole]:
        return self._role_index.get(name)

    def get_artifact(self, name: str) -> Optional[Artifact]:
        return self._artifact_index.get(name)

    def get_event(self, name: str) -> Optional[Event]:
        return self._event_index.get(name)

    def __repr__(self) -> str:
        import_names = (
            [i.name for i in self.imports] if hasattr(self, "imports") else []
        )
        event_names = [e.name for e in self.events] if hasattr(self, "events") else []
        return (
            f"Community(name={self.name!r}, roles={[r.name for r in self.roles]!r}, "
            f"artifacts={[a.name for a in self.artifacts]!r}, "
            f"events={event_names!r}, "
            f"imports={import_names!r})"
        )

    def __str__(self) -> str:
        return self.name


@dataclass
class TokenAlias:
    """
    Represents a token alias in the context of an import.
    """

    name: str
    imported_name: str

    def __repr__(self) -> str:
        return f"TokenAlias(name={self.name!r}, imported_name={self.imported_name!r})"


@dataclass
class RoleFulfillment:
    """
    Represents role fulfillment in the context of an import.
    """

    role: CommunityRole
    imported_role: CommunityRole

    def __repr__(self) -> str:
        return (
            f"RoleFulfillment(role={self.role.name!r}, "
            f"imported_role={self.imported_role.name!r})"
        )


@dataclass
class Import:
    """
    Represents an import of a community or its components.
    """

    imported_community: Community  # This now works
    name: str
    role_fulfillment: List[RoleFulfillment] = field(default_factory=list)
    token_aliases: List[TokenAlias] = field(default_factory=list)
    policy_envelope: List[PolicyEnvelopeConfig] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Import(imported_community={self.imported_community.name!r}, "
            f"name={self.name!r}, "
            f"role_fulfillment={self.role_fulfillment!r}, "
            f"token_aliases={self.token_aliases!r}, "
            f"policy_envelope={self.policy_envelope!r})"
        )
