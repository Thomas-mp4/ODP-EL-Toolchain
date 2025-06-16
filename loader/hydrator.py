# hydrator.py
from ODP import model, type, community, artifact, event, behavior, policy
from textx import textx_isinstance


def get_fqn(obj, parent_fqn=""):
    prefix = f"{parent_fqn}." if parent_fqn else ""
    return f"{prefix}{getattr(obj, 'name', 'unnamed')}"


class Hydrator:

    def __init__(self, textx_model, metamodel):
        self.textx_model = textx_model
        self.metamodel = metamodel
        self.object_registry = {}
        self.warnings = []

    def hydrate(self) -> model.Model:
        self._instantiation_pass()
        self._linkage_pass()

        for comm in self.object_registry["model"].communities:
            comm.build_indexes()

        return self.object_registry["model"]

    def _instantiation_pass(self) -> None:
        """Instantiates all objects from the textX model."""
        # Prepare the root model object.
        hydrated_model = model.Model()
        self.object_registry["model"] = hydrated_model

        # Instantiate all simple types in the model.
        for tx_simple_type in getattr(self.textx_model, "simpleTypes", []):
            self._instantiate_simple_type(
                tx_simple_type=tx_simple_type, hydrated_model=hydrated_model
            )

        # Instantiate all communities and their components
        for tx_community in getattr(self.textx_model, "communities", []):
            self._instantiate_community(
                tx_community=tx_community, hydrated_model=hydrated_model
            )

    def _linkage_pass(self) -> None:
        """Links the instantiated objects together by resolving references."""
        for tx_community in self.textx_model.communities:
            comm_fqn = get_fqn(tx_community)
            for tx_artifact in tx_community.artifacts:
                self._link_artifact(tx_artifact, comm_fqn)
            for tx_event in getattr(tx_community, "events", []):
                self._link_event(tx_event, comm_fqn)
            for tx_role in tx_community.roles:
                self._link_actions(tx_role, comm_fqn)

    # Instantiation Helper Methods
    def _instantiate_simple_type(self, tx_simple_type, hydrated_model) -> None:
        """Instantiates a SimpleType object and adds it to the model."""
        fqn = get_fqn(tx_simple_type)
        hydrated_type = type.SimpleType(name=tx_simple_type.name)
        self.object_registry[fqn] = hydrated_type
        hydrated_model.simple_types.append(hydrated_type)

    def _instantiate_community(self, tx_community, hydrated_model) -> None:
        """Instantiates a Community object and its components."""
        comm_fqn = get_fqn(tx_community)
        hydrated_community = community.Community(
            name=tx_community.name,
            objective=tx_community.objective,
            artifacts=[],
            events=[],
            roles=[],
            rules=[],
        )
        self.object_registry[comm_fqn] = hydrated_community
        hydrated_model.communities.append(hydrated_community)

        # Instantiate all components of the community.
        for tx_artifact in getattr(tx_community, "artifacts", []):
            self._instantiate_placeholder(tx_artifact, comm_fqn)
        for tx_event in getattr(tx_community, "events", []):
            self._instantiate_placeholder(tx_event, comm_fqn)
        for tx_role in getattr(tx_community, "roles", []):
            self._instantiate_role(tx_role, comm_fqn, hydrated_community)

        PolicyRule = self.metamodel["Policy"]
        for tx_rule in tx_community.rules:
            if textx_isinstance(tx_rule, PolicyRule):
                self._instantiate_policy(tx_rule, comm_fqn, hydrated_community)

    def _instantiate_placeholder(self, tx_obj, parent_fqn):
        """Creates a placeholder for an object that will be fully created in the linkage pass."""
        fqn = get_fqn(tx_obj, parent_fqn=parent_fqn)
        self.object_registry[fqn] = {"name": tx_obj.name, "is_placeholder": True}

    def _instantiate_role(self, tx_role, parent_fqn, hydrated_community):
        role_fqn = get_fqn(tx_role, parent_fqn)
        hydrated_role = behavior.CommunityRole(
            name=tx_role.name, description=getattr(tx_role, "description", None)
        )
        self.object_registry[role_fqn] = hydrated_role
        hydrated_community.roles.append(hydrated_role)
        for tx_action in tx_role.actions:
            self._instantiate_action(tx_action, role_fqn, hydrated_role)

    def _instantiate_action(self, tx_action, parent_fqn, hydrated_role):
        action_fqn = get_fqn(tx_action, parent_fqn)
        tx_class_name = tx_action.__class__.__name__

        if tx_class_name == "SpeechAct":
            hydrated_action = behavior.SpeechAct(
                name=tx_action.name,
                parameters=[],
                guard=None,
                trigger_event=None,
                tokens=[],
            )
        elif tx_class_name == "BasicAction":
            hydrated_action = behavior.BasicAction(name=tx_action.name)
        elif tx_class_name == "Authorization":
            hydrated_action = behavior.Authorization(
                name=tx_action.name,
            )
        elif tx_class_name == "Declaration":
            hydrated_action = behavior.Declaration(
                name=tx_action.name,
            )
        elif tx_class_name == "Delegation":
            if tx_action.token_type == "permit":
                token_type = behavior.DelegatedToken.PERMIT
            elif tx_action.token_type == "burden":
                token_type = behavior.DelegatedToken.BURDEN
            else:
                self.warnings.append(
                    f"Unknown delegation token type '{tx_action.token_type}' for action '{action_fqn}'."
                )
                return
            hydrated_action = behavior.Delegation(
                name=tx_action.name,
                token_type=token_type,
                token_name=tx_action.token_name,
                agent=tx_action.agent,
                tokens=[],
            )

        else:
            self.warnings.append(
                f"Unknown action type '{tx_class_name}' for '{action_fqn}'. Skipping."
            )
            return

        self.object_registry[action_fqn] = hydrated_action
        hydrated_role.actions.append(hydrated_action)

    def _instantiate_policy(self, tx_policy, parent_fqn, hydrated_community):
        pol_fqn = get_fqn(tx_policy, parent_fqn)
        hydrated_policy = policy.Policy(
            name=tx_policy.name,
            type=tx_policy.type,
            setting_behaviour=policy.PolicySettingBehaviour(
                policy_setting_role=tx_policy.setting_behaviour.policy_setting_role
            ),
            initial_value=self._hydrate_policy_value(tx_policy.initial_value),
            envelope=self._hydrate_policy_envelope(tx_policy.envelope),
        )
        self.object_registry[pol_fqn] = hydrated_policy
        hydrated_community.rules.append(hydrated_policy)

    # Linking Helper Methods
    def _resolve_type(self, type_name: str, context_fqn: str):
        """Resolves a type name to a hydrated object from the registry."""
        local_fqn = f"{context_fqn}.{type_name}"
        if local_fqn in self.object_registry:
            return self.object_registry[local_fqn]
        if type_name in self.object_registry:
            return self.object_registry[type_name]
        return None

    def _resolve_type_hint(self, tx_type_ref, context_fqn: str) -> str:

        if isinstance(tx_type_ref, str):
            type_name_str = tx_type_ref
        elif hasattr(tx_type_ref, "type") and hasattr(tx_type_ref.type, "name"):
            type_name_str = tx_type_ref.type.name
        elif hasattr(tx_type_ref, "name"):
            type_name_str = tx_type_ref.name
        else:
            # Fallback
            type_name_str = str(tx_type_ref)
        resolved_type = self._resolve_type(type_name_str, context_fqn)
        if not resolved_type:
            self.warnings.append(
                f"Could not resolve type '{type_name_str}' in context '{context_fqn}'."
            )
        return type_name_str

    def _link_artifact(self, tx_artifact, parent_fqn):
        """Creates the final Artifact object and links its properties."""
        art_fqn = get_fqn(tx_artifact, parent_fqn)
        hydrated_properties = []
        for tx_property in tx_artifact.properties:
            type_hint = self._resolve_type_hint(tx_property.type, parent_fqn)
            hydrated_prop = artifact.Property(
                name=tx_property.name, type_hint=type_hint
            )
            hydrated_properties.append(hydrated_prop)

        final_artifact = artifact.Artifact(
            name=tx_artifact.name, properties=tuple(hydrated_properties), parties=()
        )
        hydrated_community = self.object_registry[parent_fqn]
        hydrated_community.artifacts.append(final_artifact)
        self.object_registry[art_fqn] = final_artifact

    def _link_event(self, tx_event, parent_fqn):
        """Creates the final Event object and links its parameters."""
        evt_fqn = get_fqn(tx_event, parent_fqn)
        hydrated_params = []
        for tx_param in getattr(tx_event, "artifacts", []):
            type_hint = self._resolve_type_hint(tx_param.type, parent_fqn)
            hydrated_param = event.Parameter(name=tx_param.name, type_hint=type_hint)
            hydrated_params.append(hydrated_param)

        final_event = event.Event(name=tx_event.name, artifacts=tuple(hydrated_params))
        hydrated_community = self.object_registry[parent_fqn]
        hydrated_community.events.append(final_event)
        self.object_registry[evt_fqn] = final_event

    def _link_actions(self, tx_role, comm_fqn):
        role_fqn = get_fqn(tx_role, comm_fqn)
        for tx_action in getattr(tx_role, "actions", []):
            action_fqn = get_fqn(tx_action, role_fqn)
            hydrated_action = self.object_registry.get(action_fqn)
            if not hydrated_action:
                continue

            # Link Parameters
            for tx_param in getattr(tx_action, "parameters", []):
                type_hint = self._resolve_type_hint(tx_param.type, comm_fqn)
                hydrated_param = event.Parameter(
                    name=tx_param.name, type_hint=type_hint
                )
                hydrated_action.parameters.append(hydrated_param)

            # Link Guard
            if guard := getattr(tx_action, "guard", None):
                hydrated_action.guard = behavior.Guard(raw=guard.condition)

            # Link Emitted Event
            if trigger_event := getattr(tx_action, "trigger_event", None):
                event_fqn = f"{comm_fqn}.{trigger_event.name}"
                if resolved_event := self.object_registry.get(event_fqn):
                    hydrated_action.trigger_event = resolved_event
                else:
                    self.warnings.append(
                        f"Could not resolve emitted event '{trigger_event.name}' for action '{action_fqn}'."
                    )

            # Link Deontic Tokens
            if isinstance(hydrated_action, behavior.SpeechAct):
                self._link_deontic_tokens(tx_action, hydrated_action, comm_fqn)

    def _link_deontic_tokens(self, tx_action, hydrated_action, comm_fqn):
        """Creates and links DeonticToken objects for a given SpeechAct."""
        # Check if the hydrated_action is of class Delegation
        if isinstance(hydrated_action, behavior.Delegation):
            return

        if not tx_action.tokens:
            return

        BurdenRule = self.metamodel["Burden"]
        PermitRule = self.metamodel["Permit"]
        EmbargoRule = self.metamodel["Embargo"]

        for tx_token in tx_action.tokens:
            if textx_isinstance(tx_token, BurdenRule):
                TokenClass = behavior.Burden
            elif textx_isinstance(tx_token, PermitRule):
                TokenClass = behavior.Permit
            elif textx_isinstance(tx_token, EmbargoRule):
                TokenClass = behavior.Embargo
            else:
                self.warnings.append(
                    f"Unknown token type '{tx_token.__class__.__name__}' in action '{tx_action.name}'. Skipping."
                )
                continue

            hydrated_token = TokenClass(name=tx_token.name)
            if tx_role_ref := getattr(tx_token, "role", None):
                role_fqn = f"{comm_fqn}.{tx_role_ref.name}"
                hydrated_token.affected_role = self.object_registry.get(role_fqn)
            if tx_trigger := getattr(tx_token, "activation_trigger", None):
                event_fqn = f"{comm_fqn}.{tx_trigger.name}"
                hydrated_token.activation_trigger = self.object_registry.get(event_fqn)
            if tx_finish_expr := getattr(tx_token, "finish_event", None):
                hydrated_token.finish_expression = self._hydrate_event_expression(
                    tx_finish_expr, comm_fqn
                )

            hydrated_action.tokens.append(hydrated_token)

    def _hydrate_event_expression(self, tx_expr, comm_fqn):
        tx_class_name = tx_expr.__class__.__name__
        if tx_class_name in ["EventExpression", "AndExpression"]:
            op_map = {"EventExpression": "AND", "AndExpression": "OR"}
            operands = [
                self._hydrate_event_expression(op, comm_fqn) for op in tx_expr.op
            ]
            return event.EventExpression(op=op_map[tx_class_name], operands=operands)
        elif tx_class_name == "PrimaryExpression":
            if sub_expr := getattr(tx_expr, "op", None):
                return self._hydrate_event_expression(sub_expr, comm_fqn)
            elif tx_event_ref := getattr(tx_expr, "event", None):
                resolved_event = self.object_registry.get(
                    f"{comm_fqn}.{tx_event_ref.name}"
                )
                return event.EventExpression(op=None, operands=[resolved_event])
        return None

    def _hydrate_policy_value(self, tx_value):
        DurationRule, NumberIntervalRule = (
            self.metamodel["Duration"],
            self.metamodel["NumberInterval"],
        )
        if textx_isinstance(tx_value, DurationRule):
            return policy.Duration(
                value=tx_value.value, unit=policy.DurationUnit.from_text(tx_value.unit)
            )
        elif textx_isinstance(tx_value, NumberIntervalRule):
            return policy.NumberInterval(
                from_=getattr(tx_value, "from"), to_=tx_value.to
            )
        return tx_value

    def _hydrate_policy_envelope(self, tx_envelope):
        hydrated_rules = [
            policy.EnvelopeRule(
                type=policy.EnvelopeRuleType.from_text(tx_rule.type),
                values=[self._hydrate_policy_value(v) for v in tx_rule.values],
            )
            for tx_rule in tx_envelope.envelope_rules
        ]
        return policy.PolicyEnvelope(envelope_rules=hydrated_rules)
