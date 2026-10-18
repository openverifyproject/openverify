"""Pre-graph policies reuse ports and exact local operation binding."""

from copy import deepcopy
from typing import cast

from openverify.adapters import Registry
from openverify.dataflow import resolve_inputs
from openverify.engine.admission import admit
from openverify.errors import ProtocolError
from openverify.model import (
    Activation,
    Admission,
    Context,
    PolicyEvaluation,
    PolicyOperation,
    Selection,
    VerificationDefinition,
)
from openverify.policy import check_outcome
from openverify.serialization import to_data
from openverify.validation import parse_object


def builtin(
    role: str, definition: VerificationDefinition, opportunity_id: str
) -> Activation | Selection | Admission:
    p = definition.execution_policy
    if role == "ACTIVATION" and p.activation.executor_ref == "MANUAL":
        return Activation(outcome="ACTIVATE", reason="MANUAL")
    if role == "SELECTION" and p.selection.executor_ref == "EXPLICIT":
        return Selection(subjects=[definition.subject], reason="EXPLICIT")
    if role == "ADMISSION":
        return admit(definition, opportunity_id)
    raise ProtocolError("POLICY_UNSUPPORTED", "Unsupported built-in policy")


def evaluate(
    role: str,
    policy: PolicyOperation,
    definition: VerificationDefinition,
    values: Context,
    opportunity_id: str,
    registry: Registry,
) -> PolicyEvaluation:
    inputs, resolutions, blocked = resolve_inputs(policy, values, {}, definition.graph)
    if blocked:
        raise ProtocolError("POLICY_INPUT", "Required policy input unavailable or invalid")
    executor_ref = executor_version = None
    if policy.operation is None:
        outcome = builtin(role, definition, opportunity_id)
    else:
        req = policy.operation
        implementation = registry.operations.get((req.capability_id, req.capability_version))
        if implementation is None:
            raise ProtocolError("POLICY_UNSUPPORTED", "Unregistered exact policy operation")
        executor_ref = f"{type(implementation).__module__}.{type(implementation).__qualname__}"
        version = getattr(implementation, "version", None)
        executor_version = version if isinstance(version, str) and version else None
        try:
            raw = implementation.execute(deepcopy(inputs), deepcopy(policy.config))
        except Exception as exc:
            raise ProtocolError("POLICY_ERROR", "Policy implementation failed") from exc
        try:
            # Policy adapters return the constrained outcome JSON object directly.
            outcome = cast(
                Activation | Selection | Admission, parse_object(role.lower(), cast(Context, raw))
            )
        except Exception as exc:
            raise ProtocolError("POLICY_OUTPUT", "Invalid policy outcome") from exc
    check_outcome(role, outcome, definition)
    return PolicyEvaluation.model_validate(
        {
            "role": role,
            "input_values": inputs,
            "input_resolutions": {k: to_data(v) for k, v in resolutions.items()},
            "outcome": to_data(outcome),
            "executor_ref": executor_ref,
            "executor_version": executor_version,
        }
    )
