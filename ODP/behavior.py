# behavior.py

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, TYPE_CHECKING, Dict, Any

from .event import Event, EventExpression
from .guard import Guard
from .parameter import Parameter

if TYPE_CHECKING:
    from .enterprise_object import ActiveEO


class DeonticType(Enum):
    BURDEN = auto()
    PERMIT = auto()
    EMBARGO = auto()


@dataclass
class DeonticToken:
    """
    An enterprise object which expresses a constraint on the ability of an active enterprise object
    holding it to perform certain actions. An active enterprise object carries a set of deontic tokens,
    which control the occurrence of conditional actions within its behaviour.
    These tokens are either permits, burdens or embargos.
    A deontic token is not itself an active enterprise object;
    it is held by exactly one active enterprise object. (Clause 6.4.1)
    """

    token_type: DeonticType
    name: str
    parameters: List[str] = field(default_factory=list)
    affected_role: Optional["CommunityRole"] = None
    pre_activation_guard: Optional["Guard"] = None
    activation_trigger: Optional["Event"] = None
    finish_expression: Optional["EventExpression"] = None
    post_event_guard: Optional["Guard"] = None

    def is_permit(self) -> bool:
        return self.token_type is DeonticType.PERMIT

    def is_burden(self) -> bool:
        return self.token_type is DeonticType.BURDEN

    def is_embargo(self) -> bool:
        return self.token_type is DeonticType.EMBARGO

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, token_type={self.token_type.name}, "

    def __str__(self):
        return f"{self.name} ({self.token_type.name})"


class Burden(DeonticToken):
    def __init__(self, **kw):
        super().__init__(token_type=DeonticType.BURDEN, **kw)


class Permit(DeonticToken):
    def __init__(self, **kw):
        super().__init__(token_type=DeonticType.PERMIT, **kw)


class Embargo(DeonticToken):
    def __init__(self, **kw):
        super().__init__(token_type=DeonticType.EMBARGO, **kw)


@dataclass
class CommunityRole:
    """
    Represents a role within a community.
    """

    name: str
    description: Optional[str] = None
    actions: List["Action"] = field(default_factory=list)
    tokens: List[DeonticToken] = field(default_factory=list)

    def __repr__(self):
        return f"CommunityRole(name={self.name!r})"

    def __str__(self):
        return self.name

    def get_token_by_name(self, token_name: str) -> Optional[DeonticToken]:
        for t in self.tokens:
            if t.name == token_name:
                return t
        return None

    def get_tokens(self) -> List[DeonticToken]:
        return self.tokens

    def get_obligations(self) -> List[Burden]:
        return [t for t in self.tokens if isinstance(t, Burden)]

    def get_permissions(self) -> List[Permit]:
        return [t for t in self.tokens if isinstance(t, Permit)]

    def get_embargoes(self) -> List[Embargo]:
        return [t for t in self.tokens if isinstance(t, Embargo)]

    def get_action(self, action_name: str) -> Optional["Action"]:
        for action in self.actions:
            if action.name == action_name:
                return action
        return None


@dataclass
class DelegatedToken(Enum):
    PERMIT = auto()
    BURDEN = auto()


@dataclass
class Action:
    """
    Parent class for all actions (SpeechAct, BasicAction, Authorization, Delegation, Declaration).
    """

    name: str
    parameters: List["Parameter"] = field(default_factory=list)
    guard: Optional["Guard"] = None
    trigger_event: Optional["Event"] = None

    def __repr__(self):
        params = [p.name for p in self.parameters]
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"parameters={params!r}, guard={self.guard!r}, trigger_event={self.trigger_event!r})"
        )

    def __str__(self):
        return self.name


@dataclass
class ActionCall:
    """
    Represents a call to an action within another action.
    """

    role: CommunityRole
    action: str
    arguments: List[str] = field(default_factory=list)

    def __repr__(self):
        return f"ActionCall(role={self.role!r}, action={self.action!r}, args={self.arguments!r})"

    def __str__(self):
        return f"Call {self.action} on {self.role.name} with args {', '.join(self.arguments)}"


@dataclass
class BasicAction(Action):
    """
    Represents one of the actions that can be performed.
    """

    # TODO: Return type should refer to Type
    return_type: Optional[str] = None
    calls: List["ActionCall"] = field(default_factory=list)


@dataclass
class SpeechAct(Action):
    """
    An action whose performance results in a change to the sets of deontic tokens (permits, embargoes and burdens)
    carried by the active enterprise objects filling its various action roles. (Clause 6.4.7)
    """

    tokens: List["DeonticToken"] = field(default_factory=list)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(name={self.name!r}, "
            f"parameters={[p.name for p in self.parameters]!r}, "
            f"guard={self.guard!r}, tokens={[t.name for t in self.tokens]!r}, "
            f"trigger_event={self.trigger_event!r})"
        )

    def __str__(self):
        return f"{self.name}"


@dataclass
class Authorization(SpeechAct):
    """
    An action indicating that a particular behaviour shall not be prevented.
    Unlike a permission, an authorization is an empowerment. (Clause 6.6.4)
    """

    pass


@dataclass(kw_only=True)
class Delegation(SpeechAct):
    """
    The action that assigns something, such as authorization, responsibility or provision of
    a service to another object. A delegation, once made, may later be withdrawn. (Clause 6.6.6)
    """

    # NOTE: agent is CommunityRole, in the standard it is a concept inherited from ActiveEO.
    # NOTE: There is a link communityRolefiller from CommunityRole to ActiveEO (See DSL).

    token_type: DelegatedToken
    token_name: str
    agent: CommunityRole | None

    def __repr__(self):
        return (
            f"Delegation(name={self.name!r}, token_type={self.token_type.name}, "
            f"token_name={self.token_name!r}, agent={self.agent!r}, "
            f"guard={self.guard!r})"
        )


@dataclass
class Declaration(SpeechAct):
    # NOTE: Declaration is a type of SpeechAct, so it inherits from it, it does not have any unique attributes.
    pass
