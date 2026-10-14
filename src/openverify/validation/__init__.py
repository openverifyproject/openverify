"""Schema validation followed by the prose invariants of the supported draft."""

import json
import re
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
    Constant,
    Decision,
    Evidence,
    ExecutionObservation,
    Extension,
    ExternalReference,
    Graph,
    InputPort,
    InputResolution,
    Measurement,
    NodeRecord,
    OperationRequirement,
    OutputPort,
    Profile,
    ResourceDimension,
    Result,
    RunInput,
    RunRecord,
    SeverityDomain,
    UpstreamOutput,
    Value,
    VerificationDefinition,
)
from openverify.serialization import decode, json_equal, to_data

TYPES: dict[str, type[Value]] = {
    "input-port": InputPort,
    "output-port": OutputPort,
    "operation-requirement": OperationRequirement,
    "execution-observation": ExecutionObservation,
    "input-resolution": InputResolution,
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
    if name not in TYPES and name != "value-source":
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


def _rfc3339_datetime(value: object) -> bool:
    # jsonschema's date-time checker otherwise depends on an optional package.
    if not isinstance(value, str):
        return True
    if (
        re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(?:\.[0-9]+)?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})",
            value,
        )
        is None
    ):
        return False
    datetime.fromisoformat(value[:-1] + "Z" if value.endswith("z") else value)
    return True


@lru_cache
def schema_validator(name: str) -> Draft202012Validator:
    resources: list[tuple[str, Resource[Schema]]] = []
    for path in files("openverify").joinpath("data/schemas").iterdir():
        schema = cast(dict[str, JsonValue], json.loads(path.read_text(encoding="utf-8")))
        resources.append((cast(str, schema["$id"]), Resource.from_contents(cast(Schema, schema))))
    registry = Registry[Schema]().with_resources(resources)
    checker = FormatChecker()
    checker.checks("date-time", raises=ValueError)(_rfc3339_datetime)
    return Draft202012Validator(load_schema(name), registry=registry, format_checker=checker)


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
    if name == "value-source":
        raw = decode(data)
        validate_wire(name, raw)
        assert isinstance(raw, dict)
        cls = {
            "CONSTANT": Constant,
            "RUN_INPUT": RunInput,
            "EXTERNAL_REFERENCE": ExternalReference,
            "UPSTREAM_OUTPUT": UpstreamOutput,
        }[cast(str, raw["kind"])]
        value = cls.model_validate(raw)
        semantic(value)
        return value
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
        if isinstance(value, ExecutionObservation) and field == "evidence":
            # Observations retain structurally valid but semantically rejected
            # evidence. Acceptance validates it without discarding incurred usage.
            continue
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
        from openverify.dataflow import validate_executable

        validate_executable(value)
    elif isinstance(value, InputPort):
        from openverify.dataflow import validate_port

        validate_port(value)
    elif isinstance(value, OutputPort):
        from openverify.json_schema import check_schema

        check_schema(value.value_schema)
    elif isinstance(value, InputResolution):
        usable = value.status == "AVAILABLE" or value.used_default
        if (
            usable != ("value" in value.model_fields_set)
            or value.status == "AVAILABLE"
            and (value.source is None or value.used_default)
            or value.source is None
            and value.status != "ABSENT"
        ):
            fail("DATAFLOW_BINDING", "Resolution status/source/value contradict")
    elif isinstance(value, OperationRequirement):
        if (
            re.fullmatch(
                r"(?:openverify\.[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*|[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*){2,})",
                value.capability_id,
            )
            is None
            or not value.capability_version
        ):
            fail("DATAFLOW_BINDING", "Malformed capability requirement")
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
    if "judgment" in r.model_fields_set and not (
        r.disposition == "EXECUTED"
        and r.execution_outcome == "SUCCESS"
        and r.applicability == "APPLICABLE"
        and r.determination == "KNOWN"
    ):
        fail("RESULT_STATE", "Only KNOWN applicable Results can emit a judgment, including null")


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
    if graph.features:
        fail("GRAPH_UNSUPPORTED", "Declared graph feature is unsupported")
    ordered_nodes(graph)
    from openverify.dataflow import validate_graph

    validate_graph(graph)


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


def _timestamp(value: str) -> datetime:
    # RFC3339 allows lowercase z; datetime accepts uppercase Z. Preserve wire text.
    try:
        return datetime.fromisoformat(value[:-1] + "Z" if value.endswith("z") else value)
    except ValueError as exc:
        raise ProtocolError("PROTOCOL_STRUCTURE", "Invalid RFC3339 timestamp") from exc


def validate_executable_definition(value: VerificationDefinition) -> None:
    """The one definition validator; alias names its executable guarantee."""
    validate_definition(value)


def _lineage(run: RunRecord) -> None:
    from openverify.dataflow import (
        accept_outputs,
        error_result,
        guards_enabled,
        resolve_inputs,
        validate_run_inputs,
    )

    graph = run.definition.graph
    nodes = {n.id: n for n in graph.nodes}
    records: dict[str, NodeRecord] = {}
    seen: dict[str, Result] = {}
    if not json_equal(to_data(run.subject), to_data(run.definition.subject)) or _timestamp(
        run.finished_at
    ) < _timestamp(run.started_at):
        fail("PROVENANCE_LINEAGE", "Definition identity or run timing mismatch")
    try:
        run_values = validate_run_inputs(run.definition, run.run_inputs)
    except ProtocolError as exc:
        raise ProtocolError("PROVENANCE_LINEAGE", "Invalid occurrence run inputs") from exc
    stopped = run.admission.outcome != "RUN"
    for record in run.nodes:
        node = nodes.get(record.node_id)
        expected = {e.from_node for e in graph.edges if e.to_node == record.node_id}
        if (
            node is None
            or record.node_id in records
            or not expected <= records.keys()
            or set(record.upstream_node_ids) != expected
            or len(record.upstream_node_ids) != len(expected)
        ):
            fail("PROVENANCE_LINEAGE", "Node dependency lineage mismatch")
        assert node is not None
        if (
            record.kind != node.kind
            or record.operation != node.operation
            or not json_equal(
                {k: to_data(v) for k, v in record.upstream_results.items()},
                {k: to_data(seen[k]) for k in expected if k in seen},
            )
        ):
            fail("PROVENANCE_LINEAGE", "Node dependency lineage mismatch")
        if (
            _timestamp(record.finished_at) < _timestamp(record.started_at)
            or _timestamp(record.started_at) < _timestamp(run.started_at)
            or _timestamp(record.finished_at) > _timestamp(run.finished_at)
            or any(
                _timestamp(records[k].finished_at) > _timestamp(record.started_at) for k in expected
            )
        ):
            fail("PROVENANCE_LINEAGE", "Node timing is outside dependency/run interval")
        values, resolutions, blocked = resolve_inputs(node, run_values, records, graph)
        if not json_equal(values, record.input_values) or not json_equal(
            {k: to_data(v) for k, v in resolutions.items()},
            {k: to_data(v) for k, v in record.input_resolutions.items()},
        ):
            fail("PROVENANCE_LINEAGE", "Input snapshots contradict declared bindings")
        if run.admission.outcome == "SKIP" and (
            record.result is None or record.result.disposition != "SKIPPED"
        ):
            fail("PROVENANCE_LINEAGE", "Admission SKIP requires every node to be SKIPPED")
        disabled = stopped or not guards_enabled(node.id, graph, run_values, records)
        if disabled or blocked:
            reason = "DISABLED" if disabled else "INPUT_UNAVAILABLE"
            expected_result = Result(disposition="SKIPPED", output={"reason": reason})
            if (
                record.state != "NONEXECUTED"
                or record.reason != reason
                or record.observation is not None
                or record.information
                or record.decision is not None
                or not json_equal(
                    to_data(record.result) if record.result is not None else None,
                    to_data(expected_result),
                )
            ):
                fail("PROVENANCE_LINEAGE", "Nonexecuted node has contradictory observations")
        else:
            if record.state == "NONEXECUTED":
                fail("PROVENANCE_LINEAGE", "Ready node cannot silently omit execution")
            if record.observation is None:
                # Local exceptions have no fabricated provider observation.
                if (
                    record.state != "ERROR"
                    or record.information
                    or record.decision is not None
                    or record.result is None
                    or record.result.execution_outcome != "ERROR"
                ):
                    fail("PROVENANCE_LINEAGE", "Invalid executor failure record")
            else:
                try:
                    information, result, decision = accept_outputs(
                        node, record.observation, run.definition
                    )
                    state = (
                        "ERROR"
                        if result is not None and result.execution_outcome == "ERROR"
                        else "SUCCESS"
                    )
                    reason = None
                except ProtocolError as exc:
                    information, result, decision = {}, error_result(exc), None
                    state, reason = "ERROR", exc.code
                if (
                    record.state != state
                    or record.reason != reason
                    or not json_equal(information, record.information)
                    or not json_equal(
                        to_data(result) if result is not None else None,
                        to_data(record.result) if record.result is not None else None,
                    )
                    or not json_equal(
                        to_data(decision) if decision is not None else None,
                        to_data(record.decision) if record.decision is not None else None,
                    )
                ):
                    fail("PROVENANCE_LINEAGE", "Observed and accepted outputs contradict")
        if record.decision is not None and record.decision.kind in (
            "STOP_SUCCESS",
            "STOP_FAILURE",
            "RETRY",
            "DEFER",
        ):
            stopped = True
        records[record.node_id] = record
        if record.result is not None:
            seen[record.node_id] = record.result
    if records.keys() != nodes.keys() or not json_equal(
        {k: to_data(v) for k, v in run.final_results.items()},
        {k: to_data(v) for k, v in seen.items()},
    ):
        fail("PROVENANCE_LINEAGE", "Incomplete node or final-result lineage")
