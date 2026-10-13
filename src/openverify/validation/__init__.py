"""Schema validation followed by the prose invariants of the supported draft."""

import json
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from typing import Protocol, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError as SchemaError
from pydantic import JsonValue, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import Schema

from openverify.errors import ProtocolError
from openverify.model import (
    AdmissionPolicy,
    AnnotatedValue,
    ArtifactRef,
    Decision,
    Evidence,
    Extension,
    Graph,
    Measurement,
    Profile,
    ResourceDimension,
    Result,
    RunRecord,
    SeverityDomain,
    Value,
    VerificationDefinition,
)
from openverify.serialization import decode, to_data

TYPES: dict[str, type[Value]] = {
    "verification-definition": VerificationDefinition,
    "result": Result,
    "decision": Decision,
    "artifact-ref": ArtifactRef,
    "evidence": Evidence,
    "graph": Graph,
    "resource": Measurement,
    "severity-domain": SeverityDomain,
    "profile": Profile,
    "run-record": RunRecord,
    "extension": Extension,
    "resource-dimension": ResourceDimension,
}


def load_schema(name: str) -> dict[str, JsonValue]:
    if name not in TYPES and name not in ("extension", "resource-dimension"):
        raise ProtocolError("PROTOCOL_STRUCTURE", "Unknown schema name", details=name)
    return cast(
        dict[str, JsonValue],
        json.loads(
            files("openverify")
            .joinpath(f"data/schemas/{name}.schema.json")
            .read_text(encoding="utf-8")
        ),
    )


class ValidatorPort(Protocol):
    def validate(self, instance: JsonValue) -> None: ...


@lru_cache
def schema_validator(name: str) -> Draft202012Validator:
    resources: list[tuple[str, Resource[Schema]]] = []
    for path in files("openverify").joinpath("data/schemas").iterdir():
        schema = cast(dict[str, JsonValue], json.loads(path.read_text(encoding="utf-8")))
        resources.append((cast(str, schema["$id"]), Resource.from_contents(cast(Schema, schema))))
    registry = Registry[Schema]().with_resources(resources)
    return Draft202012Validator(
        load_schema(name), registry=registry, format_checker=FormatChecker()
    )


def validate_wire(name: str, data: JsonValue) -> None:
    decode(data)
    if isinstance(data, dict) and "protocol" in data and data["protocol"] != "draft":
        raise ProtocolError("PROTOCOL_VERSION", "Unsupported protocol marker", "/protocol")
    try:
        cast(ValidatorPort, schema_validator(name)).validate(data)
    except SchemaError as error:
        path = "/" + "/".join(
            str(p).replace("~", "~0").replace("/", "~1") for p in error.absolute_path
        )
        raise ProtocolError(
            "PROTOCOL_STRUCTURE", "Wire object violates schema", path, error.message
        ) from error


def parse_object(name: str, data: str | bytes | JsonValue) -> Value:
    if name not in TYPES:
        raise ProtocolError("PROTOCOL_STRUCTURE", "Unknown object type", details=name)
    raw = decode(data)
    validate_wire(name, raw)
    try:
        value = TYPES[name].model_validate(raw)
    except ValidationError as exc:
        raise ProtocolError("PROTOCOL_STRUCTURE", "Typed wire validation failed") from exc
    semantic(value)
    return value


def parse_definition(data: str | bytes | JsonValue) -> VerificationDefinition:
    return cast(VerificationDefinition, parse_object("verification-definition", data))


def parse_result(data: str | bytes | JsonValue) -> Result:
    return cast(Result, parse_object("result", data))


def parse_run_record(data: str | bytes | JsonValue) -> RunRecord:
    return cast(RunRecord, parse_object("run-record", data))


def validate_definition(value: VerificationDefinition) -> None:
    parse_definition(to_data(value))


def validate_result(value: Result) -> None:
    parse_result(to_data(value))


def fail(code: str, message: str) -> None:
    raise ProtocolError(code, message)


def semantic(value: Value) -> None:
    # Walk nested protocol values; never interpret arbitrary metadata/config/extension data.
    if isinstance(value, AnnotatedValue) and any(e.required for e in value.extensions):
        fail("EXTENSION_UNSUPPORTED", "Required extension is unsupported")
    if isinstance(value, Extension) and value.required:
        fail("EXTENSION_UNSUPPORTED", "Required extension is unsupported")
    for field in type(value).model_fields:
        item = getattr(value, field)
        if isinstance(item, Value):
            semantic(item)
        elif isinstance(item, list):
            for child in cast(list[object], item):
                if isinstance(child, Value):
                    semantic(child)
        elif isinstance(item, dict):
            for child in cast(dict[str, object], item).values():
                if isinstance(child, Value):
                    semantic(child)
    if isinstance(value, Result):
        _result(value)
    elif isinstance(value, Evidence):
        if all(
            x is None
            for x in (value.message, value.artifact_ref, value.locator, value.structured_data)
        ):
            fail("EVIDENCE_EMPTY", "Evidence needs a meaningful component")
    elif isinstance(value, Measurement):
        valid = (
            value.kind in ("EXACT", "ESTIMATED")
            and value.value is not None
            and value.minimum is None
            and value.maximum is None
            or value.kind == "RANGE"
            and value.value is None
            and value.minimum is not None
            and value.maximum is not None
            and value.minimum <= value.maximum
            or value.kind == "UNKNOWN"
            and all(x is None for x in (value.value, value.minimum, value.maximum))
        )
        if not valid:
            fail("RESOURCE_MEASUREMENT", "Invalid kind-dependent measurement fields")
    elif isinstance(value, Decision):
        if (value.kind == "ROUTE") != (value.destination is not None):
            fail("RESULT_STATE", "Only ROUTE requires a destination")
    elif isinstance(value, SeverityDomain):
        if (
            not value.levels
            or len({v.label for v in value.levels}) != len(value.levels)
            or len({v.rank for v in value.levels}) != len(value.levels)
        ):
            fail("PROFILE_DOMAIN", "Severity levels need unique labels and ranks")
    elif isinstance(value, Graph):
        _graph(value)
    elif isinstance(value, AdmissionPolicy):
        if (
            value.strategy == "PROBABILITY"
            and value.probability is None
            or value.strategy != "PROBABILITY"
            and value.probability is not None
        ):
            fail("ADMISSION_POLICY", "Probability is required only for PROBABILITY")
    elif isinstance(value, VerificationDefinition):
        try:
            Draft202012Validator.check_schema(value.judgment_schema)
        except Exception as exc:
            raise ProtocolError("PROTOCOL_STRUCTURE", "Invalid judgment schema") from exc
    elif isinstance(value, RunRecord):
        _lineage(value)
    elif isinstance(value, Profile):
        if len({d.id for d in value.resource_dimensions}) != len(value.resource_dimensions):
            fail("PROFILE_DOMAIN", "Resource dimension ids must be unique")


def _result(r: Result) -> None:
    observations = (r.judgment, r.verdict, r.score, r.severity)
    evaluation = (r.applicability, r.determination, *observations)
    if r.disposition != "EXECUTED":
        valid = r.execution_outcome is None and all(x is None for x in evaluation)
    elif r.execution_outcome == "ERROR":
        valid = all(x is None for x in evaluation)
    elif r.execution_outcome == "SUCCESS":
        if r.applicability == "NOT_APPLICABLE":
            valid = r.determination is None and all(x is None for x in observations)
        elif r.applicability == "APPLICABLE":
            valid = (
                r.determination == "KNOWN"
                or r.determination == "UNKNOWN"
                and all(x is None for x in observations)
            )
        else:
            valid = False
    else:
        valid = False
    if not valid:
        fail("RESULT_STATE", "Impossible Result axis combination")


GUARD_VALUES = {
    "disposition": {"EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED"},
    "execution_outcome": {"SUCCESS", "ERROR"},
    "applicability": {"APPLICABLE", "NOT_APPLICABLE"},
    "determination": {"KNOWN", "UNKNOWN"},
    "verdict": {"PASS", "FAIL"},
    "decision_kind": {"CONTINUE", "STOP_SUCCESS", "STOP_FAILURE", "ROUTE", "RETRY", "DEFER"},
}
HANDLING = {"UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING"}
REDUCERS = {
    "ALL",
    "ANY",
    "MAJORITY",
    "MIN_SCORE",
    "MAX_SCORE",
    "AVERAGE",
    "WEIGHTED_AVERAGE",
    "WORST_SEVERITY",
}


def aggregate_config(config: dict[str, JsonValue], count: int | None = None) -> None:
    reducer = config.get("reducer")
    handling = config.get("handling")
    allowed = {"reducer", "handling"}
    if reducer == "WEIGHTED_AVERAGE":
        allowed.add("weights")
    if reducer == "WORST_SEVERITY":
        allowed.add("severity_domain")
    if (
        not isinstance(reducer, str)
        or reducer not in REDUCERS
        or not isinstance(handling, dict)
        or set(handling) != HANDLING
        or any(v not in ("REJECT", "IGNORE") for v in handling.values())
        or set(config) != allowed
    ):
        fail("AGGREGATE_CONFIG", "Reducer needs exact explicit handling and configuration")
    if reducer == "WEIGHTED_AVERAGE":
        weights = config.get("weights")
        if (
            not isinstance(weights, list)
            or not weights
            or any(type(w) not in (int, float) or cast(float, w) < 0 for w in weights)
            or not any(w > 0 for w in cast(list[float], weights))
            or count is not None
            and len(weights) != count
        ):
            fail("AGGREGATE_CONFIG", "Weights must align with inputs and have positive total")
    if reducer == "WORST_SEVERITY":
        try:
            parse_object("severity-domain", config.get("severity_domain"))
        except ProtocolError as exc:
            raise ProtocolError("AGGREGATE_CONFIG", "Invalid severity domain") from exc


def _graph(graph: Graph) -> None:
    ids = [n.id for n in graph.nodes]
    if len(set(ids)) != len(ids):
        fail("GRAPH_DUPLICATE", "Duplicate graph node id")
    pairs: set[tuple[str, str]] = set()
    for e in graph.edges:
        if e.from_node not in ids or e.to_node not in ids:
            fail("GRAPH_REFERENCE", "Missing edge endpoint")
        if (e.from_node, e.to_node) in pairs:
            fail("GRAPH_DUPLICATE", "Duplicate directed edge")
        pairs.add((e.from_node, e.to_node))
        if e.guard and (
            e.guard.node_id != e.from_node
            or e.guard.field in GUARD_VALUES
            and e.guard.value not in GUARD_VALUES[e.guard.field]
        ):
            fail("GRAPH_REFERENCE", "Invalid guard reference or axis value")
    if graph.features:
        fail("GRAPH_UNSUPPORTED", "Declared graph feature is unsupported")
    ordered_nodes(graph)
    for n in graph.nodes:
        if n.kind == "AGGREGATE" and n.executor_ref == "standard.aggregate":
            aggregate_config(
                n.config,
                sum(
                    e.to_node == n.id
                    for e in graph.edges
                    if next(node for node in graph.nodes if node.id == e.from_node).kind
                    in ("EVALUATE", "AGGREGATE")
                ),
            )


def ordered_nodes(graph: Graph) -> list[str]:
    ordered: list[str] = []
    remaining = [n.id for n in graph.nodes]
    while remaining:
        ready = next(
            (
                id
                for id in remaining
                if all(e.from_node in ordered for e in graph.edges if e.to_node == id)
            ),
            None,
        )
        if ready is None:
            fail("GRAPH_UNSUPPORTED", "Cycles are not supported by the draft subset")
        ordered.append(cast(str, ready))
        remaining.remove(cast(str, ready))
    return ordered


def _lineage(run: RunRecord) -> None:
    graph = run.definition.graph
    nodes = {n.id: n for n in graph.nodes}
    seen: dict[str, Result] = {}
    seen_ids: set[str] = set()
    if run.subject != run.definition.subject or datetime.fromisoformat(
        run.finished_at
    ) < datetime.fromisoformat(run.started_at):
        fail("PROVENANCE_LINEAGE", "Definition identity or run timing mismatch")
    for record in run.nodes:
        node = nodes.get(record.node_id)
        expected = {e.from_node for e in graph.edges if e.to_node == record.node_id}
        if (
            node is None
            or record.node_id in seen_ids
            or record.executor_ref != node.executor_ref
            or set(record.upstream_node_ids) != expected
            or len(record.upstream_node_ids) != len(expected)
            or not expected <= seen_ids
            or record.upstream_results != {id: seen[id] for id in expected if id in seen}
            or datetime.fromisoformat(record.finished_at)
            < datetime.fromisoformat(record.started_at)
        ):
            fail("PROVENANCE_LINEAGE", "Node dependency lineage mismatch")
        outputs = sum(x is not None for x in (record.result, record.decision, record.derived))
        assert node is not None
        if datetime.fromisoformat(record.started_at) < datetime.fromisoformat(
            run.started_at
        ) or datetime.fromisoformat(record.finished_at) > datetime.fromisoformat(run.finished_at):
            fail("PROVENANCE_LINEAGE", "Node timing is outside run interval")
        if run.admission.outcome != "RUN" and (
            record.result is None or record.result.disposition == "EXECUTED"
        ):
            fail("PROVENANCE_LINEAGE", "Unadmitted run cannot contain executed nodes")
        if (
            outputs != 1
            or record.decision is not None
            and node.kind != "CONTROL"
            or record.derived is not None
            and node.kind != "DERIVE"
            or record.result is not None
            and node.kind in ("CONTROL", "DERIVE")
            and record.result.execution_outcome != "ERROR"
            and record.result.disposition == "EXECUTED"
        ):
            fail("PROVENANCE_LINEAGE", "Node output does not match semantic kind")
        seen_ids.add(record.node_id)
        if record.result:
            seen[record.node_id] = record.result
    if seen_ids != set(nodes) or run.final_results != seen:
        fail("PROVENANCE_LINEAGE", "Incomplete node or final-result lineage")
