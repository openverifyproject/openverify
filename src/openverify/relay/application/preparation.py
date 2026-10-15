"""Snapshot and validate all host-supplied semantic values before side effects."""

from copy import deepcopy
from dataclasses import dataclass

from openverify.dataflow import validate_run_inputs
from openverify.model import Context, VerificationDefinition
from openverify.policy import policies
from openverify.relay.errors import RelayError
from openverify.serialization import decode, serialize
from openverify.validation import parse_definition, validate_executable_definition


@dataclass(frozen=True)
class PreparedRun:
    definition: VerificationDefinition
    supplied: Context
    values: Context


def prepare(definition: VerificationDefinition, inputs: Context) -> PreparedRun:
    snapshot = parse_definition(serialize(definition))
    validate_executable_definition(snapshot)
    execution = snapshot.execution_policy
    builtins = (
        execution.activation.executor_ref,
        execution.selection.executor_ref,
        execution.admission.strategy,
    )
    allowed = ({"MANUAL"}, {"EXPLICIT"}, {"ALWAYS", "PROBABILITY"})
    for policy, discriminator, supported in zip(policies(snapshot), builtins, allowed, strict=True):
        if policy.operation is None and discriminator not in supported:
            raise RelayError("POLICY_UNSUPPORTED", f"Unsupported built-in policy: {discriminator}")
    raw = decode(deepcopy(inputs))
    if not isinstance(raw, dict):
        raise TypeError("Run inputs must be a JSON object")
    supplied = deepcopy(raw)
    values = validate_run_inputs(snapshot, supplied)
    return PreparedRun(snapshot, supplied, values)
