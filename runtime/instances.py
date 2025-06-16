import uuid
from dataclasses import field, dataclass
from enum import auto, Enum
from typing import Dict, Any

from ODP.artifact import Artifact
from ODP.behavior import DeonticToken
from ODP.enterprise_object import Party


@dataclass
class ArtifactInstance:
    """Represents a live instance of an artifact in the simulation."""

    instance_id: str
    template: Artifact
    properties: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return f"ArtifactInstance(id='{self.instance_id}', type='{self.template.name}')"

    def __getattr__(self, name: str):
        if name in self.properties:
            return self.properties[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute or property '{name}'"
        )


class DeonticTokenState(Enum):
    """Enumeration of possible states for a deontic token."""

    INACTIVE = auto()
    ACTIVE = auto()
    DISCHARGED = auto()


@dataclass
class DeonticTokenInstance:
    """Represents a live, stateful deontic token held by a party."""

    template: DeonticToken
    owner: Party
    instance_id: str = field(default_factory=lambda: f"token-{uuid.uuid4().hex[:6]}")
    state: DeonticTokenState = DeonticTokenState.INACTIVE
    context: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self):
        return (
            f"DeonticTokenInstance(id='{self.instance_id}', template='{self.template.name}', "
            f"owner='{self.owner.name}', state='{self.state}',deontic_type='{self.template.token_type}')"
        )
