# event.py
from dataclasses import dataclass, field
from typing import List, Union, Set, Tuple

from .parameter import Parameter


@dataclass(frozen=True)
class Event:
    """
    A single event.
    """

    name: str
    artifacts: Tuple[Parameter] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"Event(name={self.name!r}, artifacts={[a.name for a in self.artifacts]!r})"
        )

    def __str__(self) -> str:
        return self.name


@dataclass
class EventExpression:
    """
    A Boolean combination of Events.
    """

    op: Union[None, str]
    operands: List[Union["EventExpression", Event]]

    def is_leaf(self) -> bool:
        return (
            self.op is None
            and len(self.operands) == 1
            and isinstance(self.operands[0], Event)
        )

    def evaluate(self, occurred: Set[Event]) -> bool:
        """
        Checks whether this expression holds given a set of occurred events.
        """
        if self.is_leaf():
            # Leaf’s sole operand is an Event
            return self.operands[0] in occurred

        if self.op == "AND":
            return all(
                (
                    operand.evaluate(occurred)
                    if isinstance(operand, EventExpression)
                    else operand in occurred
                )
                for operand in self.operands
            )

        if self.op == "OR":
            return any(
                (
                    operand.evaluate(occurred)
                    if isinstance(operand, EventExpression)
                    else operand in occurred
                )
                for operand in self.operands
            )

        # If neither leaf nor AND/OR, treat it as False by default.
        return False

    def __repr__(self) -> str:
        # If it's a leaf node, just show the event itself.
        if self.is_leaf():
            return repr(self.operands[0])

        # If it's a non-leaf node with only one child, we don't need parentheses.
        if len(self.operands) == 1:
            return repr(self.operands[0])

        # Only add parentheses when we have multiple operands that need grouping.
        op_symbol = " & " if self.op == "AND" else " | "
        return f"({op_symbol.join(map(repr, self.operands))})"
