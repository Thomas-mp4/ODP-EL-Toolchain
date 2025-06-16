# tracer.py
import datetime
from colorama import Fore
from dataclasses import dataclass
from typing import Dict, Any, List

from ODP.enterprise_object import Party
from ODP.behavior import SpeechAct
from runtime.instances import DeonticTokenInstance


class LogColors:
    """Color constants for logging."""

    HEADER = Fore.MAGENTA
    SUCCESS = Fore.GREEN
    ERROR = Fore.RED
    WARNING = Fore.YELLOW
    INFO = Fore.CYAN
    DEFAULT = Fore.LIGHTBLACK_EX


@dataclass
class LogEntry:
    """A structured entry for the simulation trace."""

    timestamp: datetime.datetime
    event_type: str
    details: Dict[str, Any]


class SimulationTracer:
    """Records key simulation events to build a detailed history."""

    def __init__(self):
        self.history: List[LogEntry] = []

    def _log(self, event_type: str, details: Dict[str, Any]):
        self.history.append(LogEntry(datetime.datetime.now(), event_type, details))

    def log_action(self, party: Party, action: SpeechAct, args: Dict[str, Any]):
        self._log(
            "ACTION",
            {
                "party": party,
                "action_name": action.name,
                "args": {k: repr(v) for k, v in args.items()},
            },
        )

    def log_action_prohibited(self, party: Party, action_name: str, reason: str):
        """Logs an attempted action that was prohibited."""
        self._log(
            "ACTION_PROHIBITED",
            {
                "party": party,
                "action_name": action_name,
                "reason": reason,
            },
        )

    def log_token_creation(self, token: DeonticTokenInstance):
        self._log(
            "TOKEN_CREATE",
            {
                "token_id": token.instance_id,
                "template_name": token.template.name,
                "owner": token.owner,
            },
        )

    def log_token_state_change(self, token: DeonticTokenInstance, trigger_event: str):
        self._log(
            "TOKEN_STATE_CHANGE",
            {
                "token_id": token.instance_id,
                "template_name": token.template.name,
                "owner": token.owner,
                "new_state": token.state.name,
                "trigger_event": trigger_event,
            },
        )


class MermaidGenerator:
    """Generates a Mermaid sequence diagram from a simulation trace."""

    def __init__(self, history: List[LogEntry]):
        self.history = history

    def generate(self) -> str:
        participants = sorted(
            list(
                set(
                    p.name
                    for entry in self.history
                    for p in [entry.details.get("party"), entry.details.get("owner")]
                    if p
                )
            )
        )

        lines = ["sequenceDiagram", "    participant Engine"]
        lines.extend(f"    participant {p}" for p in participants)
        lines.append("")

        for entry in self.history:
            details = entry.details
            if entry.event_type == "ACTION":
                lines.append(
                    f'    {details["party"].name}->>+Engine: {details["action_name"]}()'
                )
            elif entry.event_type == "ACTION_PROHIBITED":
                party_name = details["party"].name
                action_name = details["action_name"]
                reason = details["reason"].replace('"', "'") # Mermaid can be picky with quotes
                lines.append(f"    {party_name}->>+Engine: [Attempt] {action_name}()")
                lines.append(f"    Engine-->>-{party_name}: Prohibited")
                lines.append(f"    Note over Engine,{party_name}: {reason}")
            elif entry.event_type == "TOKEN_CREATE":
                lines.append(
                    f'    Note over {details["owner"].name}: Token \'{details["template_name"]}\' CREATED'
                )
            elif entry.event_type == "TOKEN_STATE_CHANGE":
                new_state = details["new_state"]
                lines.append(
                    f'    Engine-->>-Engine: Event: {details["trigger_event"]}'
                )
                lines.append(
                    f'    Note over {details["owner"].name}: Token \'{details["template_name"]}\' is now {new_state}'
                )

        return "\n".join(lines)