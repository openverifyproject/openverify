"""Compact definition inspection and the standard partial status projection."""

from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.model import Result, UpstreamOutput, VerificationDefinition
from openverify.serialization import to_data
from openverify.validation import ordered_nodes, validate_definition, validate_result


def inspect_definition(definition: VerificationDefinition) -> dict[str, JsonValue]:
    validate_definition(definition)
    return {
        "id": definition.id,
        "version": definition.version,
        "subject": definition.subject.id,
        "criterion": definition.criterion.description,
        "node_order": cast(list[JsonValue], ordered_nodes(definition.graph)),
        "admission": definition.execution_policy.admission.strategy,
        "execution_policy": to_data(definition.execution_policy),
        "run_inputs": [cast(JsonValue, p.model_dump(by_alias=True)) for p in definition.run_inputs],
        "nodes": {
            n.id: {
                "operation": cast(JsonValue, n.operation.model_dump()),
                "inputs": [cast(JsonValue, p.model_dump(by_alias=True)) for p in n.inputs],
                "outputs": [cast(JsonValue, p.model_dump(by_alias=True)) for p in n.outputs],
                "bindings": {k: cast(JsonValue, v.model_dump()) for k, v in n.bindings.items()},
                "consumers": {
                    p.name: [
                        consumer.id
                        for consumer in definition.graph.nodes
                        if any(
                            isinstance(s, UpstreamOutput)
                            and s.node_id == n.id
                            and s.output == p.name
                            for s in [
                                *consumer.bindings.values(),
                                *[
                                    e.guard.source
                                    for e in definition.graph.edges
                                    if e.to_node == consumer.id and e.guard is not None
                                ],
                            ]
                        )
                    ]
                    for p in n.outputs
                },
            }
            for n in definition.graph.nodes
        },
    }


def flattened_status(result: Result) -> str:
    validate_result(result)
    if result.disposition == "SKIPPED":
        return "SKIP"
    if result.disposition == "EXECUTED":
        if result.execution_outcome == "ERROR":
            return "ERROR"
        if result.applicability == "APPLICABLE":
            if result.determination == "UNKNOWN":
                return "UNKNOWN"
            if result.verdict:
                return result.verdict
    raise ProtocolError("RESULT_PROJECTION", "No specified flattened status for this state")
