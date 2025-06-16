# model.py
from dataclasses import dataclass, field
from typing import List

from .community import Community
from .type import SimpleType


@dataclass
class Model:
    """
    Top-level container.
    """

    simple_types: List[SimpleType] = field(default_factory=list)
    communities: List[Community] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Model(simple_types={self.simple_types!r}, "
            f"communities={self.communities!r})"
        )
