# enterprise_object.py
from dataclasses import dataclass, field
from typing import List

from .behavior import CommunityRole, DeonticToken


class EnterpriseObject:
    """
    Base class for all enterprise objects.
    """

    pass


class ActiveEO(EnterpriseObject):
    """
    Base class for all active enterprise objects.

    An enterprise object that is able to fill an action role.
    In other words, it is an enterprise object that can be involved in some behaviour. (Clause 6.3.1)
    """

    pass


@dataclass
class Party(ActiveEO):
    """
    Represents an enterprise object modelling a natural person or any other entity considered
    to have some of the rights, powers and duties of a natural person. (Clause 6.6.1)
    """

    name: str
    fulfills_roles: List[CommunityRole] = field(default_factory=list)
    active_tokens: List[DeonticToken] = field(default_factory=list)

    def get_action(self, action_name: str):
        """Finds an action by searching all fulfilled roles."""
        for role in self.fulfills_roles:
            action = role.get_action(action_name)
            if action:
                return action
        return None

    def has_role(self, role_name: str) -> bool:
        """Checks if the party fulfills a role with the given name."""
        return any(role.name == role_name for role in self.fulfills_roles)

    def __repr__(self) -> str:
        role_names = [r.name for r in self.fulfills_roles]
        return f"Party(name={self.name!r}, fulfills_roles={role_names!r}, active_tokens={len(self.active_tokens)})"


@dataclass
class Agent(ActiveEO):
    """
    An active enterprise object that has been delegated something
    (authorization, responsibility, provision of a service, etc.) by,
    and acts for, a party (in exercising the authorization, carrying out the responsibility,
    providing the service, etc.). (Clause 6.6.8)
    """

    name: str
    principal: Party

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, principal={self.principal.name!r})"
