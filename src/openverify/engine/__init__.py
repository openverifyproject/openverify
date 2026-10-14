"""Small sequential reference implementation of typed DAG execution."""

from copy import deepcopy
from datetime import UTC, datetime
from time import perf_counter
from typing import cast
from uuid import uuid4

from openverify.adapters import Registry
from openverify.dataflow import (
    accept_outputs,
    error_result,
    guards_enabled,
    resolve_inputs,
    validate_run_inputs,
)
from openverify.engine.admission import admit
from openverify.engine.aggregation import aggregate
from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.model import (
    Context,
    Decision,
    ExecutionObservation,
    Measurement,
    NodeRecord,
    Result,
    RunRecord,
    VerificationDefinition,
)
from openverify.serialization import decode, to_data
from openverify.validation import ordered_nodes, parse_object, parse_run_record, validate_definition


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def observation(value: ExecutionObservation | Context | Result | Decision) -> ExecutionObservation:
    # SDK conveniences all normalize into the same portable observation channel.
    if isinstance(value, Result):
        return ExecutionObservation(outputs={"result": to_data(value)}, usage=deepcopy(value.usage))
    if isinstance(value, Decision):
        return ExecutionObservation(outputs={"decision": to_data(value)})
    if isinstance(value, ExecutionObservation):
        return deepcopy(value)
    return ExecutionObservation(outputs=deepcopy(value))


class Engine:
    def __init__(self, registry: Registry):
        self.registry = registry

    def run(
        self,
        definition: VerificationDefinition,
        run_inputs: Context,
        *,
        opportunity_id: str,
        context: Context | None = None,
    ) -> RunRecord:
        definition = deepcopy(definition)
        validate_definition(definition)
        decode(run_inputs)
        supplied = deepcopy(run_inputs)
        values = validate_run_inputs(definition, supplied)
        ambient = deepcopy(context) if context is not None else {}
        decode(ambient)
        for capability, supported in (
            (definition.execution_policy.activation, "MANUAL"),
            (definition.execution_policy.selection, "EXPLICIT"),
        ):
            if (
                capability.executor_ref != supported
                or capability.config
                or capability.inputs
                or capability.bindings
            ):
                raise ProtocolError(
                    "POLICY_UNSUPPORTED", "Only empty-input MANUAL/EXPLICIT are implemented"
                )
        if (
            definition.execution_policy.admission.inputs
            or definition.execution_policy.admission.bindings
        ):
            raise ProtocolError("POLICY_UNSUPPORTED", "Custom admission inputs are unsupported")
        admission = admit(definition, opportunity_id)
        started = now()
        results: dict[str, Result] = {}
        records: dict[str, NodeRecord] = {}
        stopped = admission.outcome != "RUN"
        node_map = {n.id: n for n in definition.graph.nodes}
        for node_id in ordered_nodes(definition.graph):
            node = node_map[node_id]
            upstream_ids = [e.from_node for e in definition.graph.edges if e.to_node == node_id]
            prior = {key: results[key] for key in upstream_ids if key in results}
            inputs, resolutions, blocked = resolve_inputs(node, values, records, definition.graph)
            node_started = now()
            clock = perf_counter()
            result: Result | None = None
            decision: Decision | None = None
            information: Context = {}
            observed: ExecutionObservation | None = None
            executor_version: str | None = None
            executor_ref: str | None = None
            state = "SUCCESS"
            reason: str | None = None
            disabled = stopped or not guards_enabled(node_id, definition.graph, values, records)
            if disabled or blocked:
                reason = "DISABLED" if disabled else "INPUT_UNAVAILABLE"
                state = "NONEXECUTED"
                result = Result(disposition="SKIPPED", output={"reason": reason})
            else:
                try:
                    if (
                        node.kind == "AGGREGATE"
                        and node.operation.capability_id == "openverify.aggregate"
                    ):
                        executor_ref, executor_version = "openverify.reference.aggregate", "1"
                        members = [
                            cast(Result, parse_object("result", inputs[name]))
                            for name in node.aggregate_inputs
                        ]
                        config = deepcopy(node.config)
                        if config["reducer"] == "WEIGHTED_AVERAGE":
                            weights = cast(Context, config["weights"])
                            config["weights"] = [weights[name] for name in node.aggregate_inputs]
                        observed = observation(aggregate(members, config))
                    else:
                        requirement = node.operation
                        adapter = self.registry.operations.get(
                            (requirement.capability_id, requirement.capability_version)
                        )
                        if adapter is None:
                            raise ProtocolError(
                                "EXECUTOR_UNSUPPORTED", "Unregistered exact operation requirement"
                            )
                        executor_ref = f"{type(adapter).__module__}.{type(adapter).__qualname__}"
                        version = getattr(adapter, "version", None)
                        executor_version = version if isinstance(version, str) and version else None
                        observed = observation(
                            adapter.execute(deepcopy(inputs), deepcopy(node.config))
                        )
                    # Validate observation envelope independently of semantic output acceptance.
                    observed = cast(
                        ExecutionObservation,
                        parse_object("execution-observation", to_data(observed)),
                    )
                    information, result, decision = accept_outputs(node, observed, definition)
                    if result is not None and result.execution_outcome == "ERROR":
                        state = "ERROR"
                    if decision is not None and decision.kind in (
                        "STOP_SUCCESS",
                        "STOP_FAILURE",
                        "RETRY",
                        "DEFER",
                    ):
                        stopped = True
                except Exception as exc:
                    result = error_result(exc)
                    state = "ERROR"
                    reason = exc.code if isinstance(exc, ProtocolError) else "EXECUTOR_ERROR"
                    information, decision = {}, None
            if result is not None:
                results[node_id] = result
            duration = max(0.0, perf_counter() - clock)
            records[node_id] = NodeRecord.model_validate(
                {
                    "node_id": node_id,
                    "kind": node.kind,
                    "operation": to_data(node.operation),
                    "executor_ref": executor_ref,
                    "executor_version": executor_version,
                    "upstream_node_ids": upstream_ids,
                    "upstream_results": {k: to_data(v) for k, v in prior.items()},
                    "input_values": inputs,
                    "input_resolutions": {k: to_data(v) for k, v in resolutions.items()},
                    "started_at": node_started,
                    "finished_at": now(),
                    "usage": {
                        "wall_time": to_data(Measurement(unit="s", kind="EXACT", value=duration))
                    },
                    "state": state,
                    "reason": reason,
                    "observation": to_data(observed) if observed is not None else None,
                    "information": information,
                    "result": to_data(result) if result is not None else None,
                    "decision": to_data(decision) if decision is not None else None,
                }
            )
        record = RunRecord(
            run_id=str(uuid4()),
            definition=definition,
            definition_fingerprint=fingerprint(definition),
            subject=definition.subject,
            initial_context=ambient,
            run_inputs=supplied,
            opportunity_id=opportunity_id,
            admission=admission,
            started_at=started,
            finished_at=now(),
            nodes=list(records.values()),
            final_results=results,
        )
        return parse_run_record(to_data(record))
