"""Run-local state machine with deterministic parallel waves and explicit barriers."""

import asyncio
from collections.abc import Sequence
from copy import deepcopy
from typing import cast
from uuid import uuid4

from openverify.dataflow import resolve_inputs
from openverify.fingerprint import fingerprint
from openverify.lifecycle import Cancellation, Cause, Lifecycle, nonexecution
from openverify.model import (
    Admission,
    CancellationEvent,
    Context,
    Extension,
    InputResolution,
    Node,
    NodeRecord,
    RunRecord,
    VerificationDefinition,
)
from openverify.policy import ROLES, policies
from openverify.provider import ProviderEvent, ProviderManifest, parse_provider_manifest, wire_data
from openverify.relay.application.binding import bind
from openverify.relay.application.execution import execute_node, now
from openverify.relay.application.policies import evaluate_policies
from openverify.relay.application.preparation import prepare
from openverify.relay.config import RuntimeConfig
from openverify.relay.core.readiness import ready_wave
from openverify.relay.core.state import RunState
from openverify.relay.errors import RelayError
from openverify.relay.ports import (
    AvailableProvider,
    EventObserver,
    ExecutionDriver,
    InvocationReport,
    InvocationRequest,
    ProviderBinder,
    ProviderCatalog,
    RecordStore,
    RelayEvent,
)
from openverify.serialization import serialize, to_data
from openverify.validation import parse_run_record


def validate_catalog(values: object) -> Sequence[AvailableProvider]:
    """An injected port's runtime value must satisfy its declared public type."""
    from openverify.relay.error_codes import RelayErrorCode

    if not isinstance(values, Sequence):
        raise RelayError(RelayErrorCode.CATALOG_INVALID, "Catalog must return a provider sequence")
    snapshot: list[AvailableProvider] = []
    identities: set[tuple[str, str]] = set()
    for value in cast(Sequence[object], values):
        if (
            not isinstance(value, AvailableProvider)
            or not isinstance(cast(object, value.manifest), ProviderManifest)
            or not callable(getattr(value.transport, "invoke", None))
        ):
            raise RelayError(
                RelayErrorCode.CATALOG_INVALID, "Catalog returned an invalid provider value"
            )
        manifest = parse_provider_manifest(wire_data(value.manifest))
        key = (manifest.provider_id, manifest.provider_version)
        if key in identities:
            raise RelayError("PROVIDER_CONFLICT", f"Provider already registered: {key}")
        identities.add(key)
        snapshot.append(AvailableProvider(manifest, value.transport))
    return tuple(snapshot)


async def coordinate(
    definition: VerificationDefinition,
    inputs: Context,
    config: RuntimeConfig,
    catalog: ProviderCatalog,
    binder: ProviderBinder,
    driver: ExecutionDriver,
    store: RecordStore,
    observer: EventObserver,
    opportunity_id: str,
    cancellation: Cancellation | None,
) -> RunRecord:
    prepared = prepare(definition, inputs)
    definition, values = prepared.definition, prepared.values
    if not opportunity_id:
        raise RelayError("OPPORTUNITY_ID", "Opportunity identity must be nonempty")
    run_id = str(uuid4())
    started = now()
    diagnostics: list[str] = []
    traces: Context = {}

    def notify(kind: str, node_id: str | None = None, event: ProviderEvent | None = None) -> None:
        try:
            observer.observe(
                RelayEvent(
                    run_id, kind, node_id, event.invocation_id if event else None, deepcopy(event)
                )
            )
        except Exception as exc:
            diagnostics.append(f"Observer failure: {type(exc).__name__}")

    def audit_trace(key: str, request: InvocationRequest, report: InvocationReport | None) -> None:
        previous = traces.get(key)
        trace: Context = previous if isinstance(previous, dict) else {}
        trace.update(
            invocation=wire_data(request.invocation),
            provider_id=request.manifest.provider_id,
            provider_version=request.manifest.provider_version,
        )
        if report is not None:
            trace["events"] = [wire_data(e) for e in report.events]
            trace["outcome"] = wire_data(report.outcome) if report.outcome else None
            trace["transport_error"] = to_data(report.error) if report.error else None
        traces[key] = trace

    from openverify.errors import ProtocolError
    from openverify.provider import ProviderContractError
    from openverify.relay.error_codes import RelayErrorCode

    try:
        available = validate_catalog(catalog.providers())
    except (ProtocolError, ProviderContractError):
        raise
    except Exception as exc:
        raise RelayError(
            RelayErrorCode.CATALOG_FAILURE,
            "Provider catalog failed",
            details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
        ) from exc
    # Bind all requirements before admission, so selection is not affected by scheduler timing.
    bound = {
        n.id: bind(n.operation, available, binder, config.bindings.get(n.id))
        for n in definition.graph.nodes
    }
    policy_providers: dict[str, AvailableProvider] = {}
    for role, policy in zip(ROLES, policies(definition), strict=True):
        if policy.operation is not None:
            policy_providers[role] = bind(
                policy.operation, available, binder, config.bindings.get(f"policy:{role}")
            )
    unknown = set(config.bindings) - set(bound) - {f"policy:{r}" for r in policy_providers}
    if unknown:
        raise RelayError("PROVIDER_BINDING_MISMATCH", f"Unknown binding targets: {sorted(unknown)}")
    evaluations = await evaluate_policies(
        definition, values, opportunity_id, policy_providers, driver, config.timeout, audit_trace
    )
    if evaluations is None:
        raise RelayError("NO_OCCURRENCE", "Opportunity was inactive or unselected")
    admission = cast(Admission, evaluations[-1].outcome)
    lifecycle = Lifecycle(admission)
    state = RunState({n.id: "PENDING" for n in definition.graph.nodes})
    event: CancellationEvent | None = None
    notify("run_started")

    def nonexecuted(
        node: Node, cause: Cause, resolved: tuple[Context, dict[str, InputResolution], bool]
    ) -> NodeRecord:
        inputs_, resolutions_, _ = resolved
        upstream = [e.from_node for e in definition.graph.edges if e.to_node == node.id]
        timestamp = now()
        return NodeRecord(
            node_id=node.id,
            kind=node.kind,
            operation=node.operation,
            upstream_node_ids=upstream,
            input_values=inputs_,
            input_resolutions=resolutions_,
            upstream_results={
                k: r.result for k in upstream if (r := state.records[k]).result is not None
            },
            started_at=timestamp,
            finished_at=timestamp,
            usage={},
            state="NONEXECUTED",
            reason=cause[1],
            result=nonexecution(cause),
        )

    while len(state.records) < len(definition.graph.nodes):
        wave = ready_wave(
            definition.graph,
            set(state.records),
            1 if cancellation is not None else config.max_concurrency,
        )
        if not wave:
            raise RelayError("GRAPH_UNSUPPORTED", "Graph cannot make progress")
        tasks: list[tuple[Node, asyncio.Task[NodeRecord]]] = []
        wave_records: dict[str, NodeRecord] = {}
        for node in wave:
            resolved = resolve_inputs(node, values, state.records, definition.graph)
            if (
                cancellation is not None
                and cancellation.reason is not None
                and admission.outcome == "RUN"
            ):
                if event is None:
                    event = CancellationEvent(
                        node_id=node.id, phase="BEFORE_START", reason=cancellation.reason
                    )
                lifecycle.cancelled = True
            cause = lifecycle.cause(node.id, definition.graph, values, state.records, resolved[2])
            if cause is not None:
                wave_records[node.id] = nonexecuted(node, cause, resolved)
                state.transition(node.id, "TERMINAL")
                continue
            state.transition(node.id, "READY")
            state.transition(node.id, "RUNNING")
            notify("node_started", node.id)

            def emit(item: ProviderEvent, node_id: str = node.id) -> None:
                notify("provider_event", node_id, item)
                trace = traces.get(node_id)
                if isinstance(trace, dict):
                    events = trace.setdefault("events", [])
                    if isinstance(events, list):
                        events.append(wire_data(item))

            def audit(
                request: InvocationRequest, report: InvocationReport | None, node_id: str = node.id
            ) -> None:
                audit_trace(node_id, request, report)

            task = asyncio.create_task(
                execute_node(
                    node,
                    definition,
                    bound[node.id],
                    driver,
                    resolved[0],
                    resolved[1],
                    state.records,
                    config.timeout,
                    emit,
                    audit,
                    cancellation,
                )
            )
            tasks.append((node, task))
        try:
            if cancellation is not None and tasks:
                node, task = tasks[0]
                while not task.done():
                    if cancellation.reason is not None:
                        event = CancellationEvent(
                            node_id=node.id, phase="RUNNING", reason=cancellation.reason
                        )
                        task.cancel()
                        break
                    await asyncio.wait([task], timeout=0.01)
            if tasks:
                await asyncio.gather(*(task for _, task in tasks))
        except BaseException:
            for _, task in tasks:
                task.cancel()
            await asyncio.gather(*(task for _, task in tasks), return_exceptions=True)
            raise
        for node, task in tasks:
            record = task.result()
            wave_records[node.id] = record
            state.transition(node.id, "TERMINAL")
        for node in wave:
            record = wave_records[node.id]
            state.records[node.id] = record
            if record.state == "CANCELLED":
                if event is None and cancellation is not None:
                    event = CancellationEvent(
                        node_id=node.id,
                        phase="RUNNING",
                        reason=cancellation.reason or "Host cancellation",
                    )
                lifecycle.cancelled = True
            if record.decision is not None:
                lifecycle.control(node.id, record.decision, definition.graph)
            notify("node_terminal", node.id)
    # Dict insertion order is dependency order. Nodes within a wave have no mutual dependencies.
    records = list(state.records.values())
    notify("run_completed")
    record = RunRecord(
        run_id=run_id,
        definition=definition,
        definition_fingerprint=fingerprint(definition),
        subject=definition.subject,
        initial_context={},
        run_inputs=prepared.supplied,
        opportunity_id=opportunity_id,
        admission=admission,
        policy_evaluations=evaluations,
        cancellation=event,
        started_at=started,
        finished_at=now(),
        nodes=records,
        provider_bindings={
            r.node_id: r.provider_binding for r in records if r.provider_binding is not None
        },
        final_results={r.node_id: r.result for r in records if r.result is not None},
        extensions=[
            Extension(
                namespace="urn:openverify:relay",
                version="0.1",
                required=False,
                data={"observer_errors": [str(d) for d in diagnostics], "invocations": traces},
            )
        ],
    )
    validated = parse_run_record(serialize(record))
    store.put(validated)
    return validated
