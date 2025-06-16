# parameter.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Parameter:
    """
    Represents a single parameter.
    """

    name: str
    type_hint: str  # TODO: Should consider converting to Type

    def __repr__(self):
        type_name = getattr(self.type_hint, "name", repr(self.type_hint))
        return f"Parameter(name={self.name!r}, type_hint='{type_name}')"
