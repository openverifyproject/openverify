"""Small sequential local executor for the documented DAG subset."""

from copy import deepcopy
from datetime import UTC, datetime
from time import perf_counter
from typing import cast
from uuid import uuid4

from jsonschema import Draft202012Validator
from pydantic import JsonValue
from referencing import Registry as SchemaRegistry
from referencing.jsonschema import Schema

from openverify.adapters import Registry
from openverify.engine.admission import admit
from openverify.engine.aggregation import aggregate
from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.model import (
    Context,
    Decision,
    Edge,
    Measurement,
    NodeRecord,
    Result,
    RunRecord,
    VerificationDefinition,
)
from openverify.serialization import decode, to_data
from openverify.validation import (
    ValidatorPort,
    ordered_nodes,
    parse_object,
    parse_run_record,
    validate_definition,
    validate_result,
)


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _context(value: object) -> Context:
    decode(cast(JsonValue, value))
    if not isinstance(value, dict):
        raise ProtocolError("EXECUTOR_ERROR", "Derive output must be a Context mapping")
    return cast(Context, value)


def error_result(exc: Exception) -> Result:
    code = exc.code if isinstance(exc, ProtocolError) else "EXECUTOR_ERROR"
    return Result(
        disposition="EXECUTED",
        execution_outcome="ERROR",
        output={"code": code, "message": str(exc)},
    )


def _version(adapter: object) -> str | None:
    version = getattr(adapter, "version", None)
    return version if isinstance(version, str) and version else None


def _guard(edge: Edge, results: dict[str, Result], decisions: dict[str, Decision]) -> bool:
    guard = edge.guard
    if guard is None:
        return True
    if guard.field in ("decision_kind", "decision_destination"):
        decision = decisions.get(guard.node_id)
        value = getattr(decision, "kind" if guard.field == "decision_kind" else "destination", None)
    else:
        value = getattr(results.get(guard.node_id), guard.field, None)
    return value == guard.value


class Engine:
    def __init__(self, registry: Registry):
        self.registry = registry

    def run(
        self, definition: VerificationDefinition, context: Context, *, opportunity_id: str
    ) -> RunRecord:
        # Frozen models are shallow: snapshot caller-owned nested containers before execution.
        definition = deepcopy(definition)
        validate_definition(definition)
        decode(context)
        for capability, supported in (
            (definition.execution_policy.activation, "MANUAL"),
            (definition.execution_policy.selection, "EXPLICIT"),
        ):
            if capability.executor_ref != supported or capability.config:
                raise ProtocolError(
                    "POLICY_UNSUPPORTED", "Only MANUAL/EXPLICIT with empty config are implemented"
                )
        admission = admit(definition, opportunity_id)
        initial = deepcopy(context)
        working = deepcopy(context)
        started = now()
        results: dict[str, Result] = {}
        decisions: dict[str, Decision] = {}
        records: list[NodeRecord] = []
        inactive: set[str] = set()
        stopped = admission.outcome != "RUN"
        node_map = {n.id: n for n in definition.graph.nodes}
        for id in ordered_nodes(definition.graph):
            node = node_map[id]
            edges = [e for e in definition.graph.edges if e.to_node == id]
            upstream_ids = [e.from_node for e in edges]
            prior = {id: results[id] for id in upstream_ids if id in results}
            before = deepcopy(working)
            node_started = now()
            clock = perf_counter()
            result: Result | None = None
            decision: Decision | None = None
            derived: Context | None = None
            executor_version: str | None = None
            if stopped or any(
                e.from_node in inactive or not _guard(e, results, decisions) for e in edges
            ):
                result = Result(
                    disposition="SKIPPED",
                    output={"reason": "admission/control/guard disabled invocation"},
                )
                inactive.add(id)
            else:
                try:
                    adapter: object | None = None
                    if node.kind == "DERIVE":
                        adapter = self.registry.derivers.get(node.executor_ref)
                        if adapter is None:
                            raise ProtocolError(
                                "EXECUTOR_UNSUPPORTED", "Unregistered Derive adapter"
                            )
                        executor_version = _version(adapter)
                        update = _context(
                            self.registry.derivers[node.executor_ref].execute(
                                deepcopy(working), deepcopy(node.config)
                            )
                        )
                        derived = deepcopy(update)
                        working.update(deepcopy(update))
                    elif node.kind == "CONTROL":
                        adapter = self.registry.controllers.get(node.executor_ref)
                        if adapter is None:
                            raise ProtocolError(
                                "EXECUTOR_UNSUPPORTED", "Unregistered Control adapter"
                            )
                        executor_version = _version(adapter)
                        candidate = self.registry.controllers[node.executor_ref].execute(
                            deepcopy(working), deepcopy(prior), deepcopy(node.config)
                        )
                        validated = cast(Decision, parse_object("decision", to_data(candidate)))
                        if validated.kind == "ROUTE" and validated.destination not in node_map:
                            raise ProtocolError(
                                "GRAPH_REFERENCE", "ROUTE destination is absent from graph"
                            )
                        decision = validated
                        decisions[id] = decision
                        if decision.kind in ("STOP_SUCCESS", "STOP_FAILURE", "RETRY", "DEFER"):
                            stopped = True
                    else:
                        if node.kind == "AGGREGATE" and node.executor_ref == "standard.aggregate":
                            executor_version = "0.1.0"
                            candidate_result = aggregate(list(prior.values()), node.config)
                        else:
                            adapter = self.registry.evaluators.get(node.executor_ref)
                            if adapter is None:
                                raise ProtocolError(
                                    "EXECUTOR_UNSUPPORTED", "Unregistered Evaluate adapter"
                                )
                            executor_version = _version(adapter)
                            candidate_result = self.registry.evaluators[node.executor_ref].execute(
                                deepcopy(working), deepcopy(prior), deepcopy(node.config)
                            )
                        validate_result(candidate_result)
                        if candidate_result.judgment is not None:
                            cast(
                                ValidatorPort,
                                Draft202012Validator(
                                    definition.judgment_schema, registry=SchemaRegistry[Schema]()
                                ),
                            ).validate(candidate_result.judgment)
                        result = deepcopy(candidate_result)
                except Exception as exc:
                    result = error_result(exc)
                    decision = None
                    derived = None
            if result is not None:
                results[id] = result
            duration = max(0.0, perf_counter() - clock)
            records.append(
                NodeRecord(
                    node_id=id,
                    executor_ref=node.executor_ref,
                    executor_version=executor_version,
                    upstream_node_ids=upstream_ids,
                    upstream_results=deepcopy(prior),
                    input_context=before,
                    started_at=node_started,
                    finished_at=now(),
                    usage={"wall_time": Measurement(unit="s", kind="EXACT", value=duration)},
                    result=result,
                    decision=decision,
                    derived=derived,
                )
            )
        record = RunRecord(
            run_id=str(uuid4()),
            definition=definition,
            definition_fingerprint=fingerprint(definition),
            subject=definition.subject,
            initial_context=initial,
            opportunity_id=opportunity_id,
            admission=admission,
            started_at=started,
            finished_at=now(),
            nodes=records,
            final_results=results,
        )
        return parse_run_record(to_data(record))
