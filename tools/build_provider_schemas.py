"""Maintain Provider Contract schemas from explicit wire rules, not Python models."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "urn:openverify:provider:0.1:"
STR = {"type": "string", "minLength": 1}
IDENTIFIER = {
    **STR,
    "pattern": r"^(?:openverify\.[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*|"
    r"(?!openverify\.)[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*"
    r"(?:\.[a-z][a-z0-9_]*)*)$",
}
EXTENSIONS = {
    "type": "object",
    "propertyNames": IDENTIFIER,
    "additionalProperties": {},
}
VERSIONS = {"type": "array", "items": STR, "uniqueItems": True}
SCHEMA = {"type": ["object", "boolean"]}
UTC = {
    **STR,
    "format": "date-time",
    "pattern": r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|\+00:00)$",
}
VECTOR = {"type": "object", "additionalProperties": {"$ref": "urn:verification:draft:resource"}}


def ref(name):
    return {"$ref": BASE + name}


def obj(properties, required, extensions=True):
    return {
        "type": "object",
        "properties": {**properties, **({"extensions": EXTENSIONS} if extensions else {})},
        "required": list(required),
        "additionalProperties": False,
    }


FEATURES = obj(
    {
        name: {"type": "boolean"}
        for name in ("streaming", "cancellation", "deadlines", "resource_reporting")
    },
    ("streaming", "cancellation", "deadlines", "resource_reporting"),
    False,
)
schemas = {}
schemas["capability"] = obj(
    {
        "capability_id": IDENTIFIER,
        "capability_version": STR,
        "input_schema": SCHEMA,
        "output_schema": SCHEMA,
        "config_schema": SCHEMA,
        "lifecycle_features": FEATURES,
        "vcp_version": STR,
    },
    (
        "capability_id",
        "capability_version",
        "input_schema",
        "output_schema",
        "config_schema",
        "lifecycle_features",
    ),
)
schemas["provider-manifest"] = obj(
    {
        "provider_id": IDENTIFIER,
        "provider_version": STR,
        "supported_contract_versions": {**VERSIONS, "minItems": 1},
        "supported_vcp_versions": VERSIONS,
        "capabilities": {"type": "array", "items": ref("capability")},
    },
    (
        "provider_id",
        "provider_version",
        "supported_contract_versions",
        "supported_vcp_versions",
        "capabilities",
    ),
)
schemas["invocation"] = obj(
    {
        "invocation_id": STR,
        "contract_version": {"const": "0.1"},
        "capability_id": IDENTIFIER,
        "capability_version": STR,
        "input": {},
        "config": {},
        "context": {},
        "vcp_version": STR,
        "deadline": UTC,
        "resource_budget": VECTOR,
    },
    ("invocation_id", "contract_version", "capability_id", "capability_version", "input", "config"),
)
schemas["provider-event"] = obj(
    {
        "invocation_id": STR,
        "sequence": {"type": "integer", "minimum": 1, "maximum": 9007199254740991},
        "kind": {
            "enum": [
                "progress",
                "evidence",
                "artifact",
                "resource_usage",
                "diagnostic",
                "extension",
            ]
        },
        "payload": {},
        "timestamp": UTC,
    },
    ("invocation_id", "sequence", "kind", "payload"),
)
schemas["provider-event"]["allOf"] = [
    {"if": {"properties": {"kind": {"const": kind}}}, "then": {"properties": {"payload": schema}}}
    for kind, schema in (
        ("evidence", {"$ref": "urn:verification:draft:evidence"}),
        ("artifact", {"$ref": "urn:verification:draft:artifact-ref"}),
        ("resource_usage", VECTOR),
        ("extension", obj({"namespace": IDENTIFIER, "data": {}}, ("namespace", "data"), False)),
    )
]
schemas["cancel-request"] = obj({"invocation_id": STR, "reason": STR}, ("invocation_id",))
schemas["provider-error"] = obj(
    {
        "code": {
            "anyOf": [
                {
                    "enum": [
                        "CONTRACT_VERSION_UNSUPPORTED",
                        "CAPABILITY_UNAVAILABLE",
                        "CAPABILITY_VERSION_UNSUPPORTED",
                        "INVALID_INVOCATION",
                        "INVALID_CONFIG",
                        "INVALID_INPUT",
                        "INVALID_PROVIDER_OUTPUT",
                        "PROTOCOL_VIOLATION",
                    ]
                },
                IDENTIFIER,
            ]
        },
        "message": STR,
        "details": {},
    },
    ("code", "message"),
    False,
)
schemas["outcome"] = obj(
    {
        "invocation_id": STR,
        "state": {"enum": ["COMPLETED", "ERROR", "CANCELLED", "DEADLINE_EXCEEDED"]},
        "output": {},
        "error": ref("provider-error"),
        "resource_usage": VECTOR,
    },
    ("invocation_id", "state"),
)
schemas["outcome"]["allOf"] = [
    {
        "if": {"properties": {"state": {"const": "COMPLETED"}}},
        "then": {"required": ["output"], "not": {"required": ["error"]}},
        "else": {"not": {"required": ["output"]}},
    },
    {
        "if": {"properties": {"state": {"const": "ERROR"}}},
        "then": {"required": ["error"]},
        "else": {"not": {"required": ["error"]}},
    },
]
schemas["initialize-request"] = obj(
    {
        "supported_contract_versions": {**VERSIONS, "minItems": 1},
        "supported_vcp_versions": VERSIONS,
    },
    ("supported_contract_versions", "supported_vcp_versions"),
)
schemas["initialize-result"] = obj(
    {"contract_version": {"const": "0.1"}, "manifest": ref("provider-manifest")},
    ("contract_version", "manifest"),
)

for name, body in schemas.items():
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE + name, **body}
    for directory in (
        ROOT / "provider-contract/schemas/draft",
        ROOT / "src/openverify/provider/data/schemas",
    ):
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8"
        )
