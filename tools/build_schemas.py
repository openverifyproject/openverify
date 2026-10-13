"""Maintain the normative wire schemas explicitly, independently of SDK models."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "urn:verification:draft:"
STR = {"type": "string", "minLength": 1}
NUM = {"type": "number", "minimum": 0}
JSON = {}


def ref(name):
    return {"$ref": BASE + name}


def array(item):
    return {"type": "array", "items": item}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def nullable(value):
    return {"anyOf": [value, {"type": "null"}]}


def obj(properties, required=(), common=True):
    properties = dict(properties)
    if common:
        properties.update(metadata={"type": "object"}, extensions=array(ref("extension")))
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


def marked(properties, required=()):
    return obj({"protocol": {"const": "draft"}, **properties}, ("protocol", *required))


schemas = {}
schemas["extension"] = obj(
    {
        "namespace": {**STR, "pattern": ":"},
        "version": STR,
        "required": {"type": "boolean"},
        "data": JSON,
    },
    ("namespace", "version", "required", "data"),
    False,
)
schemas["artifact-ref"] = obj(
    {"id": STR, "type": STR, "locator": JSON, "schema_id": nullable(STR)},
    ("id", "type", "locator"),
)
schemas["evidence"] = obj(
    {
        "id": nullable(STR),
        "message": nullable(STR),
        "artifact_ref": nullable(ref("artifact-ref")),
        "locator": JSON,
        "structured_data": JSON,
    },
)
schemas["resource"] = obj(
    {
        "unit": STR,
        "kind": enum("EXACT", "ESTIMATED", "RANGE", "UNKNOWN"),
        "value": nullable(NUM),
        "minimum": nullable(NUM),
        "maximum": nullable(NUM),
    },
    ("unit", "kind"),
    False,
)
vector = {"type": "object", "propertyNames": STR, "additionalProperties": ref("resource")}
schemas["resource-dimension"] = obj(
    {"id": STR, "unit": STR, "description": STR},
    ("id", "unit", "description"),
)
schemas["severity-domain"] = obj(
    {
        "id": STR,
        "levels": array(obj({"label": STR, "rank": {"type": "integer"}}, ("label", "rank"), False)),
    },
    ("id", "levels"),
    False,
)
schemas["result"] = marked(
    {
        "disposition": enum("EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED"),
        "execution_outcome": nullable(enum("SUCCESS", "ERROR")),
        "applicability": nullable(enum("APPLICABLE", "NOT_APPLICABLE")),
        "determination": nullable(enum("KNOWN", "UNKNOWN")),
        "judgment": JSON,
        "verdict": nullable(enum("PASS", "FAIL")),
        "score": nullable({**NUM, "maximum": 1}),
        "severity": nullable(obj({"domain": STR, "label": STR}, ("domain", "label"), False)),
        "evidence": array(ref("evidence")),
        "output": JSON,
        "usage": vector,
    },
    ("disposition",),
)
schemas["decision"] = marked(
    {
        "kind": enum("CONTINUE", "STOP_SUCCESS", "STOP_FAILURE", "ROUTE", "RETRY", "DEFER"),
        "destination": nullable(STR),
        "reason": nullable(STR),
    },
    ("kind",),
)
schemas["graph"] = obj(
    {
        "nodes": array(
            obj(
                {
                    "id": STR,
                    "kind": enum("DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"),
                    "executor_ref": STR,
                    "config": {"type": "object"},
                    "resource_estimate": vector,
                },
                ("id", "kind", "executor_ref"),
            )
        ),
        "edges": array(
            obj(
                {
                    "from_node": STR,
                    "to_node": STR,
                    "guard": nullable(
                        obj(
                            {
                                "node_id": STR,
                                "field": enum(
                                    "disposition",
                                    "execution_outcome",
                                    "applicability",
                                    "determination",
                                    "verdict",
                                    "decision_kind",
                                    "decision_destination",
                                ),
                                "value": STR,
                            },
                            ("node_id", "field", "value"),
                            False,
                        )
                    ),
                },
                ("from_node", "to_node"),
                False,
            )
        ),
        "features": array(enum("CYCLES", "DYNAMIC_EXPANSION")),
    },
    ("nodes",),
    False,
)
schemas["verification-definition"] = marked(
    {
        "id": STR,
        "version": STR,
        "subject": ref("artifact-ref"),
        "criterion": obj({"id": STR, "description": STR}, ("id", "description")),
        "judgment_schema": {"type": "object"},
        "satisfaction_mapping": nullable({"type": "object"}),
        "graph": ref("graph"),
        "execution_policy": obj(
            {
                "activation": obj(
                    {"executor_ref": STR, "config": {"type": "object"}}, ("executor_ref",), False
                ),
                "selection": obj(
                    {"executor_ref": STR, "config": {"type": "object"}}, ("executor_ref",), False
                ),
                "admission": obj(
                    {"strategy": STR, "probability": nullable({**NUM, "maximum": 1})},
                    ("strategy",),
                    False,
                ),
            },
            ("activation", "selection", "admission"),
            False,
        ),
    },
    ("id", "version", "subject", "criterion", "judgment_schema", "graph", "execution_policy"),
)
timestamp = {"type": "string", "format": "date-time", "pattern": r"(?:[Zz]|\+00:00)$"}
results = {"type": "object", "additionalProperties": ref("result")}
schemas["run-record"] = marked(
    {
        "run_id": STR,
        "definition": ref("verification-definition"),
        "definition_fingerprint": {**STR, "pattern": "^local-sha256:[0-9a-f]{64}$"},
        "subject": ref("artifact-ref"),
        "initial_context": {"type": "object"},
        "opportunity_id": STR,
        "admission": obj(
            {"outcome": enum("RUN", "SKIP", "DEFER"), "reason": STR}, ("outcome", "reason"), False
        ),
        "started_at": timestamp,
        "finished_at": timestamp,
        "nodes": array(
            obj(
                {
                    "node_id": STR,
                    "executor_ref": STR,
                    "executor_version": nullable(STR),
                    "upstream_node_ids": array(STR),
                    "input_context": {"type": "object"},
                    "upstream_results": results,
                    "started_at": timestamp,
                    "finished_at": timestamp,
                    "usage": vector,
                    "result": nullable(ref("result")),
                    "decision": nullable(ref("decision")),
                    "derived": nullable({"type": "object"}),
                },
                (
                    "node_id",
                    "executor_ref",
                    "upstream_node_ids",
                    "input_context",
                    "upstream_results",
                    "started_at",
                    "finished_at",
                    "usage",
                ),
                False,
            )
        ),
        "final_results": results,
    },
    (
        "run_id",
        "definition",
        "definition_fingerprint",
        "subject",
        "initial_context",
        "opportunity_id",
        "admission",
        "started_at",
        "finished_at",
        "nodes",
        "final_results",
    ),
)
schemas["profile"] = marked(
    {
        "id": STR,
        "version": STR,
        "flattened_statuses": array(STR),
        "severity_domain": ref("severity-domain"),
        "aggregators": array(STR),
        "admission_policies": array(STR),
        "decisions": array(STR),
        "resource_dimensions": array(ref("resource-dimension")),
    },
    (
        "id",
        "version",
        "flattened_statuses",
        "severity_domain",
        "aggregators",
        "admission_policies",
        "decisions",
        "resource_dimensions",
    ),
)
descriptions = {
    "artifact-ref": "External artifact identity; opaque locator does not authorize fetching.",
    "evidence": "Supporting observations; prose requires at least one meaningful component.",
    "result": "Independent result axes and observations; prose restricts state combinations.",
    "resource": "Unit-bearing measurement with kind-dependent value or range fields.",
    "decision": "Verification control decision, distinct from judgment; ROUTE needs destination.",
    "graph": (
        "Directed graph subset with source equality guards; semantic validation rejects "
        "unsupported standard weighted graph aggregation."
    ),
    "verification-definition": "Versioned subject/criterion, judgment schema, graph and policy.",
    "run-record": (
        "Snapshots retaining identity, admission, lineage, outputs, usage and UTC timing."
    ),
    "extension": "Namespaced data; preserve optional, reject unsupported required meaning.",
    "resource-dimension": "Open resource dimension with explicit unit and semantic description.",
    "severity-domain": "Ordered severity labels; prose requires unique labels and distinct ranks.",
    "profile": "Named common choices organized by concept; this is not the core ontology.",
}
for name, schema in schemas.items():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": BASE + name,
        "description": descriptions[name],
        **schema,
    }
    for folder in (ROOT / "schemas/draft", ROOT / "src/openverify/data/schemas"):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{name}.schema.json").write_text(
            json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
