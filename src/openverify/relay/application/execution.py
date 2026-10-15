"""Physical invocation, Provider/VCP acceptance, and exact node observations."""

import asyncio
import time
from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from openverify.dataflow import accept_outputs, error_result
from openverify.errors import ProtocolError
from openverify.lifecycle import Cancellation, nonexecution
from openverify.model import (
    Context,
    Evidence,
    ExecutionError,
    ExecutionObservation,
    InputResolution,
    Measurement,
    Node,
    NodeRecord,
    ResourceVector,
    VerificationDefinition,
)
from openverify.provider import Invocation, ProviderEvent
from openverify.provider.validation import validate_payload
from openverify.relay.application.contract import validate_report
from openverify.relay.ports import (
    AvailableProvider,
    EventSink,
    ExecutionDriver,
    InvocationReport,
    InvocationRequest,
)
from openverify.relay.ports.binding import identity
from openverify.validation import parse_object


def now() -> str:
    return datetime.now(UTC).isoformat()


def invocation(
    provider: AvailableProvider, capability_id: str, version: str, values: Context, config: Context
) -> InvocationRequest:
    capability = next(
        c
        for c in provider.manifest.capabilities
        if c.capability_id == capability_id and c.capability_version == version
    )
    validate_payload(capability.input_schema, values, "INVALID_INPUT")
    validate_payload(capability.config_schema, config, "INVALID_CONFIG")
    return InvocationRequest(
        deepcopy(provider.manifest),
        Invocation(
            invocation_id=str(uuid4()),
            contract_version="0.1",
            capability_id=capability_id,
            capability_version=version,
            input=deepcopy(values),
            config=deepcopy(config),
            vcp_version="draft",
        ),
    )


def observation(report: InvocationReport) -> ExecutionObservation:
    usage: ResourceVector = {}
    evidence: list[Evidence] = []
    for event in report.events:
        if event.kind == "resource_usage":
            usage = {
                k: Measurement.model_validate(v) for k, v in cast(Context, event.payload).items()
            }
        elif event.kind == "evidence":
            evidence.append(cast(Evidence, parse_object("evidence", event.payload)))
    outcome = report.outcome
    if outcome is not None and outcome.resource_usage is not None:
        usage = {k: Measurement.model_validate(v) for k, v in outcome.resource_usage.items()}
    error = report.error
    outputs: Context = {}
    if outcome is not None:
        if outcome.state == "COMPLETED":
            if isinstance(outcome.output, dict):
                outputs = deepcopy(outcome.output)
            else:
                # VCP providers return a port-name object, never primitive auto-wrapping.
                error = ExecutionError(
                    code="INVALID_PROVIDER_OUTPUT", message="VCP output must be an object"
                )
        elif outcome.state == "ERROR" and outcome.error is not None:
            error = ExecutionError(code=outcome.error.code, message=outcome.error.message)
        else:
            error = ExecutionError(
                code=outcome.state, message="Provider ended without successful output"
            )
    return ExecutionObservation(outputs=outputs, usage=usage, evidence=evidence, error=error)


async def execute_node(
    node: Node,
    definition: VerificationDefinition,
    provider: AvailableProvider,
    driver: ExecutionDriver,
    values: Context,
    resolutions: dict[str, InputResolution],
    records: dict[str, NodeRecord],
    timeout: float,
    emit: EventSink,
    audit: Callable[[InvocationRequest, InvocationReport | None], None],
    cancellation: Cancellation | None,
) -> NodeRecord:
    started = now()
    clock = time.monotonic()
    upstream = [e.from_node for e in definition.graph.edges if e.to_node == node.id]
    base = dict(
        node_id=node.id,
        kind=node.kind,
        operation=node.operation,
        upstream_node_ids=upstream,
        input_values=deepcopy(values),
        input_resolutions=deepcopy(resolutions),
        upstream_results={k: records[k].result for k in upstream if records[k].result is not None},
        started_at=started,
    )
    bound = None
    observed = None
    rejected = None
    information: Context = {}
    result = None
    decision = None
    state = "ERROR"
    reason = None
    received: list[ProviderEvent] = []

    def capture(event: ProviderEvent) -> None:
        received.append(deepcopy(event))
        emit(event)

    try:
        request = invocation(
            provider,
            node.operation.capability_id,
            node.operation.capability_version,
            values,
            node.config,
        )
        bound = identity(provider, node.operation)
        audit(request, None)
        report = await driver.execute(provider, request, timeout, capture)
        report = validate_report(request, report)
        audit(request, report)
        observed = observation(report)
        rejected = report.output_error if observed.error is None else None
        if cancellation is not None and cancellation.reason is not None:
            raise asyncio.CancelledError()
        if rejected is not None:
            raise ProtocolError(rejected.code, rejected.message)
        information, result, decision = accept_outputs(node, observed, definition)
        state = "ERROR" if result is not None and result.execution_outcome == "ERROR" else "SUCCESS"
    except asyncio.CancelledError:
        # The coordinator only interrupts one invocation when a recorded token is used.
        if observed is None:
            observed = observation(InvocationReport(events=tuple(received)))
        result = nonexecution(("CANCELLED", "CANCELLATION"))
        state, reason = "CANCELLED", "CANCELLATION"
    except Exception as exc:
        if not isinstance(exc, ProtocolError):
            exc = ProtocolError(
                getattr(exc, "code", "EXECUTOR_ERROR"), str(exc) or type(exc).__name__
            )
        result = error_result(exc)
        reason = exc.code
    usage = dict(observed.usage) if observed is not None else {}
    timing_key = "relay_wall_time" if "wall_time" in usage else "wall_time"
    usage[timing_key] = Measurement(unit="s", kind="EXACT", value=time.monotonic() - clock)
    return NodeRecord.model_validate(
        {
            **base,
            "finished_at": now(),
            "state": state,
            "reason": reason,
            "usage": usage,
            "executor_ref": bound.provider_id if bound else None,
            "executor_version": bound.provider_version if bound else None,
            "provider_binding": bound,
            "provider_output_error": rejected,
            "observation": observed,
            "information": information,
            "result": result,
            "decision": decision,
        }
    )
