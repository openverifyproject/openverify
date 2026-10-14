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
    resolve_inputs,
    validate_run_inputs,
)
from openverify.engine.aggregation import aggregate
from openverify.engine.policy import evaluate
from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.lifecycle import Cancellation, Lifecycle, nonexecution
from openverify.model import (
    Activation,
    Admission,
    CancellationEvent,
    Context,
    Decision,
    ExecutionObservation,
    Measurement,
    NodeRecord,
    PolicyEvaluation,
    Result,
    RunRecord,
    Selection,
    VerificationDefinition,
)
from openverify.policy import ROLES, policies
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
        cancellation: Cancellation | None = None,
    ) -> RunRecord:
        record = self.attempt(
            definition,
            run_inputs,
            opportunity_id=opportunity_id,
            context=context,
            cancellation=cancellation,
        )
        if record is None:
            raise ProtocolError("NO_OCCURRENCE", "Opportunity was not activated or selected")
        return record

    def attempt(
        self,
        definition: VerificationDefinition,
        run_inputs: Context,
        *,
        opportunity_id: str,
        context: Context | None = None,
        cancellation: Cancellation | None = None,
    ) -> RunRecord | None:
        definition = deepcopy(definition)
        validate_definition(definition)
        decode(run_inputs)
        supplied = deepcopy(run_inputs)
        values = validate_run_inputs(definition, supplied)
        ambient = deepcopy(context) if context is not None else {}
        decode(ambient)
        if type(opportunity_id) is not str or not opportunity_id:
            raise ProtocolError("ADMISSION_POLICY", "A nonempty opportunity identity is required")
        evaluations: list[PolicyEvaluation] = []
        for role, policy in zip(ROLES, policies(definition), strict=True):
            evaluation = evaluate(role, policy, definition, values, opportunity_id, self.registry)
            evaluations.append(evaluation)
            if isinstance(evaluation.outcome, Activation):
                if evaluation.outcome.outcome == "DO_NOT_ACTIVATE":
                    return None
            elif isinstance(evaluation.outcome, Selection) and not evaluation.outcome.subjects:
                return None
        admission = evaluations[-1].outcome
        assert isinstance(admission, Admission)
        started = now()
        results: dict[str, Result] = {}
        records: dict[str, NodeRecord] = {}
        lifecycle = Lifecycle(admission)
        cancellation_event: CancellationEvent | None = None
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
            if (
                admission.outcome == "RUN"
                and cancellation is not None
                and cancellation.reason is not None
                and cancellation_event is None
            ):
                cancellation_event = CancellationEvent(
                    node_id=node_id, phase="BEFORE_START", reason=cancellation.reason
                )
                lifecycle.cancelled = True
            cause = lifecycle.cause(node_id, definition.graph, values, records, blocked)
            if cause is not None:
                reason = cause[1]
                state = "NONEXECUTED"
                result = nonexecution(cause)
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
                    if cancellation is None or cancellation.reason is None:
                        information, result, decision = accept_outputs(node, observed, definition)
                        if result is not None and result.execution_outcome == "ERROR":
                            state = "ERROR"
                except Exception as exc:
                    result = error_result(exc)
                    state = "ERROR"
                    reason = exc.code if isinstance(exc, ProtocolError) else "EXECUTOR_ERROR"
                    information, decision = {}, None
                if cancellation is not None and cancellation.reason is not None:
                    cancellation_event = CancellationEvent(
                        node_id=node_id, phase="RUNNING", reason=cancellation.reason
                    )
                    lifecycle.cancelled = True
                    result = nonexecution(("CANCELLED", "CANCELLATION"))
                    information, decision = {}, None
                    state, reason = "CANCELLED", "CANCELLATION"
                if decision is not None:
                    lifecycle.control(node_id, decision, definition.graph)
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
            policy_evaluations=evaluations,
            cancellation=cancellation_event,
            started_at=started,
            finished_at=now(),
            nodes=list(records.values()),
            final_results=results,
        )
        return parse_run_record(to_data(record))
