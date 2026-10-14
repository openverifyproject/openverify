"""Pure dataflow validation/resolution shared by execution and provenance checking."""

from copy import deepcopy
from typing import Never, cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.json_schema import check_schema, obvious_incompatible, validate_value
from openverify.model import (
    Constant,
    Context,
    Decision,
    ExecutionObservation,
    ExternalReference,
    Graph,
    InputPort,
    InputResolution,
    JsonSchema,
    Node,
    NodeRecord,
    Result,
    RunInput,
    UpstreamOutput,
    ValueSource,
    VerificationDefinition,
)
from openverify.serialization import json_equal, to_data


def fail(message: str, code: str = "DATAFLOW_BINDING") -> Never:
    raise ProtocolError(code, message)


def validate_port(port: InputPort) -> None:
    check_schema(port.value_schema)
    if (
        (port.required and port.on_unavailable != "BLOCK")
        or (not port.required and port.on_unavailable == "BLOCK")
        or (port.on_unavailable == "DEFAULT") != (port.default is not None)
    ):
        fail("Required ports BLOCK; optional ports explicitly OMIT or DEFAULT")
    if port.default is not None:
        validate_value(port.value_schema, port.default.value)


def unique_ports(ports: list[InputPort]) -> None:
    if len({p.name for p in ports}) != len(ports):
        fail("Duplicate input port name")
    for port in ports:
        validate_port(port)


def ancestors(graph: Graph, target: str) -> set[str]:
    found: set[str] = set()
    while True:
        expanded = found | {e.from_node for e in graph.edges if e.to_node in found | {target}}
        if expanded == found:
            return found
        found = expanded


def pointer(value: JsonValue, path: str) -> JsonValue:
    import re

    if path == "":
        return value
    if not path.startswith("/") or re.search(r"~(?:[^01]|$)", path):
        fail("Invalid JSON Pointer", "GRAPH_REFERENCE")
    for part in path[1:].split("/"):
        token = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and token in value:
            value = value[token]
        elif (
            isinstance(value, list)
            and re.fullmatch(r"0|[1-9][0-9]*", token)
            and int(token) < len(value)
        ):
            value = value[int(token)]
        else:
            raise KeyError(path)
    return value


def source_schema(
    source: ValueSource, graph: Graph, consumer: str, run_ports: list[InputPort] | None
) -> JsonSchema:
    if isinstance(source, Constant):
        return {"const": source.value}
    if isinstance(source, ExternalReference):
        return {"const": to_data(source.reference)}
    if isinstance(source, RunInput):
        if run_ports is None:
            return True  # Standalone Graph has no enclosing run declarations.
        port = next((p for p in run_ports if p.name == source.name), None)
        if port is None:
            fail("Binding references unknown run input")
        return port.value_schema
    producer = next((n for n in graph.nodes if n.id == source.node_id), None)
    if producer is None:
        fail("Binding references unknown producer")
    assert producer is not None
    output = next((p for p in producer.outputs if p.name == source.output), None)
    if output is None:
        fail("Binding references unknown output")
    if source.node_id not in ancestors(graph, consumer):
        fail("Upstream output needs a strict execution ancestor")
    assert output is not None
    return output.value_schema


def validate_bindings(
    ports: list[InputPort],
    bindings: dict[str, ValueSource],
    graph: Graph,
    consumer: str,
    run_ports: list[InputPort] | None,
) -> None:
    unique_ports(ports)
    names = {p.name for p in ports}
    if not set(bindings) <= names or any(p.required and p.name not in bindings for p in ports):
        fail("Unknown target or unbound required input")
    for port in ports:
        source = bindings.get(port.name)
        if source is None:
            continue
        schema = source_schema(source, graph, consumer, run_ports)
        if isinstance(source, (Constant, ExternalReference)):
            value = source.value if isinstance(source, Constant) else to_data(source.reference)
            validate_value(port.value_schema, value, "DATAFLOW_SCHEMA")
        elif obvious_incompatible(schema, port.value_schema):
            fail("Obviously incompatible source/target schemas", "DATAFLOW_SCHEMA")


def validate_graph(graph: Graph, run_ports: list[InputPort] | None = None) -> None:
    from openverify.validation import aggregate_config

    by_id = {n.id: n for n in graph.nodes}
    for node in graph.nodes:
        validate_bindings(node.inputs, node.bindings, graph, node.id, run_ports)
        if len({p.name for p in node.outputs}) != len(node.outputs):
            fail("Duplicate output identity")
        semantic_role = {
            "DERIVE": None,
            "EVALUATE": "RESULT",
            "AGGREGATE": "RESULT",
            "CONTROL": "DECISION",
        }[node.kind]
        semantic_ports = [p for p in node.outputs if p.role != "INFORMATION"]
        if (semantic_role is None and semantic_ports) or (
            semantic_role is not None
            and (
                len(semantic_ports) != 1
                or semantic_ports[0].role != semantic_role
                or semantic_ports[0].name != semantic_role.lower()
            )
        ):
            fail("Output roles do not match computation kind")
        for output in node.outputs:
            check_schema(output.value_schema)
            if output.role != "INFORMATION" and obvious_incompatible(
                output.value_schema, {"type": "object"}
            ):
                fail("Semantic outputs require object-compatible schemas", "DATAFLOW_SCHEMA")
        if node.config_schema is not None:
            check_schema(node.config_schema)
            validate_value(node.config_schema, node.config, "DATAFLOW_CONFIG")
        members = node.aggregate_inputs
        if node.kind != "AGGREGATE" and members:
            fail("Only Aggregate declares membership")
        if node.kind == "AGGREGATE":
            membership = node.bindings.get("members")
            member_port = next((p for p in node.inputs if p.name == "members"), None)
            if (
                member_port is None
                or not member_port.required
                or not isinstance(membership, Constant)
                or not json_equal(membership.value, cast(JsonValue, members))
            ):
                fail(
                    "Aggregate must bind its ordered members as an explicit input",
                    "AGGREGATE_CONFIG",
                )
            result_bindings: set[str] = set()
            for name, source in node.bindings.items():
                if isinstance(source, UpstreamOutput):
                    output = next(
                        p for p in by_id[source.node_id].outputs if p.name == source.output
                    )
                    if output.role == "RESULT":
                        result_bindings.add(name)
            if not members or len(set(members)) != len(members) or set(members) != result_bindings:
                fail("Aggregate membership must exactly name RESULT bindings", "AGGREGATE_CONFIG")
            if any(
                not p.required or p.on_unavailable != "BLOCK"
                for p in node.inputs
                if p.name in members
            ):
                fail("Aggregate members must be required BLOCK ports", "AGGREGATE_CONFIG")
            if node.operation.capability_id == "openverify.aggregate":
                if node.operation.capability_version != "1":
                    fail("Unsupported standard reducer version", "GRAPH_UNSUPPORTED")
                config = dict(node.config)
                if config.get("reducer") == "WEIGHTED_AVERAGE":
                    weights = config.get("weights")
                    if not isinstance(weights, dict) or set(weights) != set(members):
                        fail("Weights must match stable member identities", "AGGREGATE_CONFIG")
                    config["weights"] = [weights[name] for name in members]
                aggregate_config(config, len(members))
        elif node.operation.capability_id == "openverify.aggregate":
            fail("Standard reducer requires Aggregate kind")
    for edge in graph.edges:
        guard = edge.guard
        if guard is None:
            continue
        schema = source_schema(guard.source, graph, edge.to_node, run_ports)
        if isinstance(guard.source, UpstreamOutput):
            producer = by_id[guard.source.node_id]
            output = next(p for p in producer.outputs if p.name == guard.source.output)
            if output.role in ("RESULT", "DECISION") and guard.pointer:
                from openverify.validation import GUARD_VALUES

                field = guard.pointer.removeprefix("/")
                axis = "decision_kind" if output.role == "DECISION" and field == "kind" else field
                if axis in GUARD_VALUES and (
                    not isinstance(guard.value, str) or guard.value not in GUARD_VALUES[axis]
                ):
                    fail("Invalid guard axis operand", "GRAPH_REFERENCE")
                if output.role == "RESULT":
                    allowed = set(Result.model_fields)
                else:
                    allowed = set(Decision.model_fields)
                if field.split("/")[0] not in allowed:
                    fail("Unknown semantic guard field", "GRAPH_REFERENCE")
        # Validate pointer syntax independently of source availability.
        try:
            pointer({}, guard.pointer)
        except KeyError:
            pass
        if isinstance(schema, dict) and "const" in schema:
            try:
                known = pointer(schema["const"], guard.pointer)
            except KeyError:
                fail("Guard pointer absent from constant source", "GRAPH_REFERENCE")
            if not json_equal(known, guard.value):
                # Unequal values are legal; unequal JSON types are not.
                if obvious_incompatible({"const": guard.value}, {"type": json_type(known)}):
                    fail("Guard operand type mismatch", "GRAPH_REFERENCE")
        else:
            current = schema
            for token in guard.pointer[1:].split("/") if guard.pointer else []:
                token = token.replace("~1", "/").replace("~0", "~")
                if isinstance(current, dict) and isinstance(current.get("properties"), dict):
                    properties = cast(dict[str, JsonValue], current["properties"])
                    if token not in properties:
                        if current.get("additionalProperties") is False and not current.get(
                            "patternProperties"
                        ):
                            fail("Unknown guard field", "GRAPH_REFERENCE")
                        current = True  # Open object field: defer operand typing.
                    else:
                        current = cast(JsonSchema, properties[token])
                else:
                    current = True
            if isinstance(current, dict) and "$ref" in current:
                current = True  # A subtree cannot rebase a root-local reference.
            validate_value(current, guard.value, "GRAPH_REFERENCE")


def json_type(value: JsonValue) -> str:
    if value is None:
        return "null"
    return {
        bool: "boolean",
        str: "string",
        int: "number",
        float: "number",
        list: "array",
        dict: "object",
    }[type(value)]


def validate_executable(definition: VerificationDefinition) -> None:
    unique_ports(definition.run_inputs)
    check_schema(definition.judgment_schema)
    validate_graph(definition.graph, definition.run_inputs)
    for node in definition.graph.nodes:
        if node.kind not in ("EVALUATE", "AGGREGATE"):
            continue
        for name, expected in (
            ("subject", definition.subject),
            ("criterion", definition.criterion),
        ):
            port = next((p for p in node.inputs if p.name == name), None)
            source = node.bindings.get(name)
            if (
                port is None
                or not port.required
                or not isinstance(source, Constant)
                or not json_equal(source.value, to_data(expected))
            ):
                fail(
                    "Evaluate semantic inputs must bind the definition subject/criterion",
                    "SEMANTIC_BINDING",
                )
    for policy in (
        definition.execution_policy.activation,
        definition.execution_policy.selection,
        definition.execution_policy.admission,
    ):
        if any(isinstance(s, UpstreamOutput) for s in policy.bindings.values()):
            fail("Pre-execution policies cannot consume graph outputs")
        validate_bindings(
            policy.inputs, policy.bindings, definition.graph, "", definition.run_inputs
        )


def validate_run_inputs(definition: VerificationDefinition, supplied: Context) -> Context:
    if not set(supplied) <= {p.name for p in definition.run_inputs}:
        fail("Undeclared supplied run input", "RUN_INPUT")
    values = deepcopy(supplied)
    for port in definition.run_inputs:
        if port.name not in values:
            if port.required:
                fail("Missing required run input", "RUN_INPUT")
            if port.default is not None:
                values[port.name] = deepcopy(port.default.value)
        if port.name in values:
            validate_value(port.value_schema, values[port.name], "RUN_INPUT")
    return values


def resolve_source(
    source: ValueSource, run_values: Context, records: dict[str, NodeRecord], graph: Graph
) -> InputResolution:
    if isinstance(source, Constant):
        return InputResolution(source=source, status="AVAILABLE", value=deepcopy(source.value))
    if isinstance(source, ExternalReference):
        return InputResolution(source=source, status="AVAILABLE", value=to_data(source.reference))
    if isinstance(source, RunInput):
        if source.name in run_values:
            return InputResolution(
                source=source, status="AVAILABLE", value=deepcopy(run_values[source.name])
            )
        return InputResolution(source=source, status="ABSENT")
    record = records[source.node_id]
    # Only declared semantic ports use bookkeeping Result values.
    if (
        source.output == "result"
        and record.kind in ("EVALUATE", "AGGREGATE")
        and record.result is not None
    ):
        value = to_data(record.result)
        producer = next(n for n in graph.nodes if n.id == source.node_id)
        output = next(p for p in producer.outputs if p.name == source.output)
        try:
            validate_value(output.value_schema, value)
        except ProtocolError:
            return InputResolution(source=source, status="INVALID")
        return InputResolution(source=source, status="AVAILABLE", value=value)
    if source.output == "decision" and record.kind == "CONTROL" and record.decision is not None:
        return InputResolution(source=source, status="AVAILABLE", value=to_data(record.decision))
    if source.output in record.information:
        return InputResolution(
            source=source, status="AVAILABLE", value=deepcopy(record.information[source.output])
        )
    status = "OUTPUT_MISSING"
    if record.state == "NONEXECUTED":
        status = "PRODUCER_NOT_EXECUTED"
    elif record.state == "ERROR":
        if record.reason is None:
            status = "PRODUCER_ERROR"
        elif record.observation is not None and source.output in record.observation.outputs:
            status = "INVALID" if record.observation.error is None else "PRODUCER_ERROR"
        elif record.reason == "OUTPUT_MISSING":
            status = "OUTPUT_MISSING"
        else:
            status = "PRODUCER_ERROR"
    return InputResolution.model_validate({"source": to_data(source), "status": status})


def resolve_inputs(
    node: Node, run_values: Context, records: dict[str, NodeRecord], graph: Graph
) -> tuple[Context, dict[str, InputResolution], bool]:
    values: Context = {}
    resolutions: dict[str, InputResolution] = {}
    blocked = False
    for port in node.inputs:
        source = node.bindings.get(port.name)
        resolution = (
            resolve_source(source, run_values, records, graph)
            if source is not None
            else InputResolution(status="ABSENT")
        )
        if resolution.status == "AVAILABLE":
            try:
                validate_value(port.value_schema, resolution.value)
            except ProtocolError:
                resolution = InputResolution(source=source, status="INVALID")
        if resolution.status == "AVAILABLE":
            values[port.name] = deepcopy(resolution.value)
        elif port.on_unavailable == "DEFAULT":
            assert port.default is not None
            resolution = resolution.model_copy(
                update={"used_default": True, "value": deepcopy(port.default.value)}
            )
            values[port.name] = deepcopy(port.default.value)
        elif port.on_unavailable == "BLOCK":
            blocked = True
        resolutions[port.name] = resolution
    return values, resolutions, blocked


def guards_enabled(
    node_id: str, graph: Graph, run_values: Context, records: dict[str, NodeRecord]
) -> bool:
    for edge in graph.edges:
        if edge.to_node != node_id:
            continue
        if edge.guard is not None:
            resolution = resolve_source(edge.guard.source, run_values, records, graph)
            if resolution.status != "AVAILABLE":
                return False
            try:
                value = pointer(resolution.value, edge.guard.pointer)
            except KeyError:
                return False
            if not json_equal(value, edge.guard.value):
                return False
    return True


def accept_outputs(
    node: Node, observation: ExecutionObservation, definition: VerificationDefinition
) -> tuple[Context, Result | None, Decision | None]:
    from openverify.validation import parse_object, parse_result

    if observation.error is not None:
        raise ProtocolError(observation.error.code, observation.error.message)
    for evidence in observation.evidence:
        parse_object("evidence", to_data(evidence))
    if set(observation.outputs) != {p.name for p in node.outputs}:
        fail("Produced outputs must exactly match declarations", "OUTPUT_MISSING")
    information: Context = {}
    result: Result | None = None
    decision: Decision | None = None
    for port in node.outputs:
        value = observation.outputs[port.name]
        validate_value(port.value_schema, value, "OUTPUT_INVALID")
        if port.role == "RESULT":
            result = parse_result(value)
            if any(
                name not in observation.usage
                or not json_equal(to_data(measurement), to_data(observation.usage[name]))
                for name, measurement in result.usage.items()
            ):
                fail("Result usage contradicts execution observation", "OUTPUT_INVALID")
            if result.disposition != "EXECUTED":
                fail("Invoked evaluator must emit an executed Result", "OUTPUT_INVALID")
            if "judgment" in result.model_fields_set:
                validate_value(definition.judgment_schema, result.judgment, "JUDGMENT_INVALID")
        elif port.role == "DECISION":
            decision = cast(Decision, parse_object("decision", value))
            if decision.kind == "ROUTE" and decision.destination not in {
                n.id for n in definition.graph.nodes
            }:
                fail("ROUTE destination is absent from graph", "GRAPH_REFERENCE")
        else:
            information[port.name] = deepcopy(value)
    if result is not None and result.execution_outcome == "ERROR":
        information = {}
    return information, result, decision


def error_result(exc: Exception) -> Result:
    code = exc.code if isinstance(exc, ProtocolError) else "EXECUTOR_ERROR"
    return Result(
        disposition="EXECUTED",
        execution_outcome="ERROR",
        output={"code": code, "message": str(exc)},
    )
