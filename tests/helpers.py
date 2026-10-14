"""Shared typed fixture helpers."""

import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import (
    Constant,
    Context,
    InputPort,
    Node,
    OutputPort,
    ValueSource,
    VerificationDefinition,
)
from openverify.serialization import to_data
from openverify.validation import parse_definition

ROOT = Path(__file__).resolve().parents[1]


def definition(example: str = "prose") -> VerificationDefinition:
    return parse_definition((ROOT / f"examples/{example}/definition.json").read_bytes())


def context(example: str = "prose") -> Context:
    return cast(
        Context, json.loads((ROOT / f"examples/{example}/context.json").read_text(encoding="utf-8"))
    )


def handling(action: str = "REJECT") -> dict[str, JsonValue]:
    return {
        name: action
        for name in [
            "UNKNOWN",
            "ERROR",
            "SKIP",
            "DEFERRED",
            "CANCELLED",
            "NOT_APPLICABLE",
            "MISSING",
        ]
    }


def node(*, id: str, kind: str, executor_ref: str, config: Context | None = None) -> Node:
    """Small explicit fixture author; production SDK has no implicit semantic binding."""
    capability = (
        "openverify.aggregate"
        if executor_ref == "standard.aggregate"
        else "com.example." + executor_ref.replace("-", "_")
    )
    inputs: list[InputPort] = []
    outputs: list[OutputPort] = []
    bindings: dict[str, ValueSource] = {}
    if kind in ("EVALUATE", "AGGREGATE"):
        d = definition("generic")
        inputs = [
            InputPort(name=n, schema={"type": "object"}, required=True, on_unavailable="BLOCK")
            for n in ("subject", "criterion")
        ]
        bindings = {
            "subject": Constant(value=to_data(d.subject)),
            "criterion": Constant(value=to_data(d.criterion)),
        }
        outputs = [OutputPort(name="result", schema={"type": "object"}, role="RESULT")]
    if kind == "AGGREGATE":
        inputs.append(
            InputPort(
                name="members",
                schema={"type": "array", "items": {"type": "string"}},
                required=True,
                on_unavailable="BLOCK",
            )
        )
        bindings["members"] = Constant(value=[])
    if kind == "CONTROL":
        outputs = [OutputPort(name="decision", schema={"type": "object"}, role="DECISION")]
    return Node.model_validate(
        {
            "id": id,
            "kind": kind,
            "operation": {"capability_id": capability, "capability_version": "1"},
            "inputs": inputs,
            "outputs": outputs,
            "bindings": bindings,
            "config": config or {},
        }
    )
