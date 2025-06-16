# policy.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union


class DurationUnit(Enum):
    """
    Represents the units of time used in Duration.
    """

    MINUTE = "minute"
    MINUTES = "minutes"
    HOUR = "hour"
    HOURS = "hours"
    DAY = "day"
    DAYS = "days"
    WEEK = "week"
    WEEKS = "weeks"
    MONTH = "month"
    MONTHS = "months"
    YEAR = "year"
    YEARS = "years"

    @staticmethod
    def from_text(text: str) -> DurationUnit:
        """
        Static method to convert a string to a DurationUnit enum member.
        """
        txt = text.lower()
        for member in DurationUnit:
            if member.value == txt:
                return member
        raise ValueError(
            f"Unknown DurationUnit: {text}, must be one of {', '.join(m.value for m in DurationUnit)}"
        )


@dataclass
class Duration:
    """
    Represents a duration like '5 days' or '2 hours'.
    """

    value: float
    unit: DurationUnit  # Now this works because DurationUnit is defined above

    def __repr__(self) -> str:
        return f"Duration(value={self.value!r}, unit={self.unit!r})"


@dataclass
class NumberInterval:
    """
    Represents a numeric interval like '10..20'.
    """

    from_: float
    to_: float

    def __repr__(self) -> str:
        return f"NumberInterval(from_={self.from_!r}, to_={self.to_!r})"

    def __contains__(self, value: float) -> bool:
        return self.from_ <= value <= self.to_


PolicyValue = Union[
    Duration,
    NumberInterval,
    float,
    str,
    bool,
]


class EnvelopeRuleType(Enum):
    ONE = "one"
    SET = "set"
    LIST = "list"

    @staticmethod
    def from_text(text: str) -> EnvelopeRuleType:
        """
        Static method to convert a string to an EnvelopeRuleType enum member.
        """
        txt = text.lower()
        if txt == "one":
            return EnvelopeRuleType.ONE
        if txt == "set":
            return EnvelopeRuleType.SET
        if txt == "list":
            return EnvelopeRuleType.LIST
        raise ValueError(
            f"Unknown EnvelopeRuleType: {text}, must be one of {', '.join(m.value for m in EnvelopeRuleType)}"
        )

    def __repr__(self) -> str:
        return f"{self.name}"


@dataclass
class EnvelopeRule:
    """
    Represents a rule within a policy envelope.
    """

    type: EnvelopeRuleType
    values: List[PolicyValue] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"EnvelopeRule(Type={self.type!r}, values={self.values!r})"


@dataclass
class PolicyEnvelope:
    """
    Represents the envelope of a policy, containing rules that define the policy's scope.
    """

    envelope_rules: List[EnvelopeRule] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"PolicyEnvelope(envelope_rules={self.envelope_rules!r})"


@dataclass
class PolicySettingBehaviour:

    policy_setting_role: str

    def __repr__(self) -> str:
        return (
            f"PolicySettingBehaviour(policy_setting_role={self.policy_setting_role!r})"
        )


@dataclass
class Policy:
    """
    Represents a policy within a community.
    """

    name: str
    type: str
    setting_behaviour: PolicySettingBehaviour
    initial_value: PolicyValue
    envelope: PolicyEnvelope

    def __post_init__(self) -> None:
        # TODO: Validate the type
        pass

    def __repr__(self) -> str:
        return (
            f"Policy(name={self.name!r}, type={self.type!r}, "
            f"setting_behaviour={self.setting_behaviour!r}, "
            f"initial_value={self.initial_value!r}, "
            f"envelope={self.envelope!r})"
        )

    def __str__(self) -> str:
        return f"{self.name}"


@dataclass
class PolicyEnvelopeConfig:
    """
    Represents a configuration for a policy envelope.
    """

    policy: str
    envelope_rules: List[EnvelopeRule] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.policy:
            raise ValueError("PolicyEnvelopeConfig requires a non‐empty policy name.")
        if len(self.envelope_rules) < 1:
            raise ValueError(
                f"PolicyEnvelopeConfig for '{self.policy}' needs at least one EnvelopeRule."
            )

    def __repr__(self) -> str:
        return (
            f"PolicyEnvelopeConfig(policy={self.policy!r}, "
            f"envelope_rules={self.envelope_rules!r})"
        )


Rule = Union[Policy, PolicyEnvelope, PolicyValue]
