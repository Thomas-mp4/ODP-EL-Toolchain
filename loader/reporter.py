# reporter.py

from typing import List, Any
import colorama
from ODP import model, community, policy, behavior


class ModelReporter:
    """Walks a hydrated model and prints a structured, readable report."""

    HEADER = colorama.Fore.CYAN
    DEFAULT_COLOR = colorama.Fore.RESET
    INDENT_CYCLE = [
        colorama.Fore.BLUE,
        colorama.Fore.GREEN,
        colorama.Fore.MAGENTA,
        colorama.Fore.YELLOW,
    ]

    def __init__(self, hydrated_model: model.Model):
        self.model = hydrated_model
        self.indent_level = 0

    def _log(self, message: str, color: str = None):
        """Prints a message with the current indentation level and color."""
        if color is None:
            log_color = self.INDENT_CYCLE[self.indent_level % len(self.INDENT_CYCLE)]
        else:
            log_color = color

        print(f"{'  ' * self.indent_level}{log_color}{message}{self.DEFAULT_COLOR}")

    def report(self):
        """Generates and prints the full report for the model."""
        self._log("Hydrated Model Details:", self.HEADER)
        self.indent_level += 1
        self._report_simple_types()
        self._report_communities()
        self.indent_level -= 1

    def _report_collection(
        self, title: str, collection: List[Any], item_prefix: str = ""
    ):
        """Generic helper to report a collection of items under a title."""
        if not collection:
            return
        self._log(f"{title}:")
        self.indent_level += 1
        for item in collection:
            self._log(f"{item_prefix}{item}")
        self.indent_level -= 1

    def _report_simple_types(self):
        self._report_collection(
            "Simple Types", self.model.simple_types, item_prefix="- "
        )

    def _report_communities(self):
        self._log("Communities:")
        self.indent_level += 1
        for comm in self.model.communities:
            self._log(f"{comm}")
            self.indent_level += 1
            self._log(f'Objective: "{comm.objective}"')
            self._report_artifacts(comm)
            self._report_events(comm)
            self._report_roles(comm)
            self._report_policies(comm)
            self.indent_level -= 1
        self.indent_level -= 1

    def _report_artifacts(self, comm: community.Community):
        if not comm.artifacts:
            return
        self._report_collection("Artifacts", comm.artifacts, item_prefix="- ")

    def _report_events(self, comm: community.Community):
        self._report_collection("Events", comm.events, item_prefix="- ")

    def _report_roles(self, comm: community.Community):
        if not comm.roles:
            return
        self._log("Roles:")
        self.indent_level += 1
        for role in comm.roles:
            self._log(f"- Role: {role}")

            self.indent_level += 1
            if role.actions:
                for action in role.actions:
                    self._log(f"- Action: {action}")

            self.indent_level -= 1
        self.indent_level -= 1

    def _report_policies(self, comm: community.Community):
        policies = [r for r in comm.rules if isinstance(r, policy.Policy)]
        self._report_collection("Policies", policies, item_prefix="- ")
