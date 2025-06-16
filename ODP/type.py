# type.py
from dataclasses import dataclass


class BaseType:
    """
    Base class for all types in the ODP-EL DSL.
    """

    pass


@dataclass(frozen=True)
class SimpleType(BaseType):
    """
    Mirrors the SimpleType from the ODP-EL DSL.
    """

    name: str

    def __repr__(self) -> str:
        return f"SimpleType(name={self.name!r})"

    def __str__(self) -> str:
        return self.name
