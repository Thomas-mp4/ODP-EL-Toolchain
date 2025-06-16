# engine.py
import uuid
from typing import Dict, Any, List

from ODP import policy, behavior
from ODP.behavior import SpeechAct, Embargo, Event
from ODP.enterprise_object import Party
from ODP.model import Model
from .instances import ArtifactInstance, DeonticTokenInstance, DeonticTokenState
from .tracer import SimulationTracer, LogColors


class Engine:
    def __init__(self, model: Model):
        self.model = model
        self.parties: Dict[str, Party] = {}
        self.artifacts: Dict[str, ArtifactInstance] = {}
        self.tokens: List[DeonticTokenInstance] = []
        self.tracer = SimulationTracer()

        # Policy values are cached for performance
        self.policy_values: Dict[str, Any] = {
            rule.name: rule.initial_value
            for comm in model.communities
            for rule in comm.rules
            if isinstance(rule, policy.Policy)
        }

    def _log(self, message: str, color: str = None):
        prefix = "(Engine) "
        if color:
            print(f"{color}{prefix}{message}")
        else:
            print(f"{prefix}{message}")

    def create_party(self, name: str, role_names: List[str]):
        if name in self.parties:
            self._log(f"Party '{name}' already exists.", LogColors.ERROR)
            return

        roles = [self.model.communities[0].get_role(r) for r in role_names]
        if not all(roles):
            self._log(
                f"One or more roles for '{name}' not found: {role_names}",
                LogColors.ERROR,
            )
            return

        self.parties[name] = Party(name=name, fulfills_roles=roles)
        self._log(f"Created party: {self.parties[name]}", LogColors.SUCCESS)

    def create_artifact_instance(
        self, artifact_type: str, instance_id: str, **properties
    ):
        if instance_id in self.artifacts:
            self._log(f"Artifact '{instance_id}' already exists.", LogColors.ERROR)
            return

        template = self.model.communities[0].get_artifact(artifact_type)
        if not template:
            self._log(f"Artifact type '{artifact_type}' not found.", LogColors.ERROR)
            return

        instance = ArtifactInstance(instance_id, template, properties)
        self.artifacts[instance_id] = instance
        self._log(f"Created artifact: {instance}", LogColors.SUCCESS)

    def _get_domain_functions(self) -> Dict[str, callable]:
        """Returns a dictionary of domain-specific functions for use in guards."""

        def loan_count(p: Party) -> int:
            count = sum(
                1
                for art in self.artifacts.values()
                if art.template.name == "Loan" and getattr(art, "borrower", None) == p
            )
            self._log(
                f"  (Guard) loanCount for '{p.name}' is {count}", LogColors.DEFAULT
            )
            return count

        def has_unpaid_fines(p: Party) -> bool:
            found = any(
                art.template.name == "Fine"
                and getattr(art, "borrower", None) == p
                and not getattr(art, "isPaid", True)
                for art in self.artifacts.values()
            )
            self._log(
                f"  (Guard) hasUnpaidFines for '{p.name}' is {found}", LogColors.DEFAULT
            )
            return found

        return {"loanCount": loan_count, "hasUnpaidFines": has_unpaid_fines}

    def _resolve_token_owner(self, token_template, performer, action_args) -> Party:
        """Determines the owner of a new token based on the action's context."""
        if not token_template.affected_role:
            return performer

        role_name = token_template.affected_role.name
        for arg in action_args.values():
            if isinstance(arg, Party) and arg.has_role(role_name):
                return arg
            if isinstance(arg, ArtifactInstance):
                for prop in arg.properties.values():
                    if isinstance(prop, Party) and prop.has_role(role_name):
                        return prop
        return performer

    def perform_action(self, party_name: str, action_name: str, **kwargs):
        self._log(
            f"'{party_name}' attempts '{action_name}' with {kwargs}", LogColors.WARNING
        )

        party = self.parties.get(party_name)
        if not party:
            self._log(f"Party '{party_name}' not found.", LogColors.ERROR)
            return

        action = party.get_action(action_name)
        if not action:
            self._log(
                f"Action '{action_name}' not found for party '{party_name}'.",
                LogColors.ERROR,
            )
            return

        for token in self.tokens:
            if (
                token.owner == party
                and token.state == DeonticTokenState.ACTIVE
                and isinstance(token.template, Embargo)
            ):
                # TODO: Actively check whether this specific embargo applies to this action. (Evaluate its guard)
                reason = f"Active embargo '{token.template.name}'"
                self._log(f"Action prohibited by {reason}.", LogColors.ERROR)
                self.tracer.log_action_prohibited(party, action_name, reason)
                return

        if action.guard:
            self._log(f"Evaluating guard: [{action.guard.raw}]", LogColors.DEFAULT)
            context = {
                **self.policy_values,
                **self._get_domain_functions(),
                "self": party,
                **kwargs,
            }
            if not action.guard.evaluate(context):
                reason = f"Guard failed: {action.guard.raw}"
                self._log(f"Action '{action.name}' prohibited. {reason}", LogColors.ERROR)
                self.tracer.log_action_prohibited(party, action.name, reason)
                return

        self._log(f"Action '{action.name}' permitted.", LogColors.SUCCESS)
        self.tracer.log_action(party, action, kwargs)

        # TODO: This domain logic is assumed for now, normally this would come from an invariant domain library.
        if action.name == "borrowItem":
            loan_id = f"loan-{uuid.uuid4().hex[:6]}"
            props = {"item": kwargs.get("item"), "borrower": party, "isOverdue": False}
            self.create_artifact_instance("Loan", loan_id, **props)
            kwargs["loan"] = self.artifacts[loan_id]
        elif action.name == "returnItem":
            loan = kwargs.get("loan")
            if loan and loan.instance_id in self.artifacts:
                del self.artifacts[loan.instance_id]
        elif action.name == "fineBorrower":
            loan = kwargs.get("loan")
            fine_id = f"fine-{uuid.uuid4().hex[:6]}"
            props = {
                "borrower": loan.borrower,
                "loan": loan,
                "amount": 500,
                "isPaid": False,
            }
            self.create_artifact_instance("Fine", fine_id, **props)
            kwargs["fine"] = self.artifacts[fine_id]


        if isinstance(action, behavior.Delegation):
            token_to_delegate_name = action.token_name
            new_owner = kwargs.get("agent")
            loan_context = kwargs.get("loan")

            if not new_owner or not new_owner.has_role(
                    action.agent.name):  # action.agent is the CommunityRole from the DSL
                self._log(
                    f"Delegation failed: recipient '{new_owner.name}' does not fulfill required role '{action.agent.name}'",
                    LogColors.ERROR)
                return

            token_found = None
            for token in self.tokens:
                # Find the active token owned by the delegator that matches the name and context (the specific loan)
                if (
                    token.owner == party and
                    token.template.name == token_to_delegate_name and
                    token.state == DeonticTokenState.ACTIVE and
                    token.context.get("loan") == loan_context
                ):
                    token_found = token
                    break

            if token_found and new_owner:
                self._log(f"  - Delegating token '{token_found.template.name}' from '{party.name}' to '{new_owner.name}'", LogColors.DEFAULT)
                token_found.owner = new_owner
                # The token remains active, just the owner changes.
                self.tracer.log_token_state_change(token_found, f"delegated via {action.name}")
            else:
                self._log(f"  - Could not find active token '{token_to_delegate_name}' for this context to delegate.", LogColors.ERROR)

        if isinstance(action, SpeechAct):
            for token_template in action.tokens:
                owner = self._resolve_token_owner(token_template, party, kwargs)
                token = DeonticTokenInstance(
                    template=token_template, owner=owner, context=kwargs
                )
                self.tokens.append(token)
                self._log(f"Created token: {token}", LogColors.DEFAULT)
                self.tracer.log_token_creation(token)

        if action.trigger_event:
            self._fire_event(action.trigger_event, **kwargs)

    def _fire_event(self, event: Event, **kwargs):
        """Fires an event and processes its consequences, like token activation or discharge."""
        self._log(f"Event fired: {event.name}", LogColors.HEADER)
        occurred_events = {event}

        for token in self.tokens:
            # Check for activation
            if (
                token.state == DeonticTokenState.INACTIVE
                and token.template.activation_trigger == event
            ):
                token.state = DeonticTokenState.ACTIVE
                self._log(f"  - Activated token: {token}", LogColors.SUCCESS)
                self.tracer.log_token_state_change(token, event.name)

            # Check for discharge
            elif (
                token.state == DeonticTokenState.ACTIVE
                and token.template.finish_expression
            ):
                if token.template.finish_expression.evaluate(occurred_events):
                    token.state = DeonticTokenState.DISCHARGED
                    self._log(f"  - Discharged token: {token}", LogColors.SUCCESS)
                    self.tracer.log_token_state_change(token, event.name)