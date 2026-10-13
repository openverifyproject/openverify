"""Compact definition inspection and the standard partial status projection."""

from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.model import Result, VerificationDefinition
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
