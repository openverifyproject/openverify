"""Bounded asyncio execution and the common Provider Contract validation boundary."""

import asyncio
from copy import deepcopy

from openverify.model import ExecutionError
from openverify.provider import (
    LifecycleValidator,
    Outcome,
    ProviderContractError,
    ProviderEvent,
    parse_outcome,
    parse_provider_event,
    serialize,
    wire_data,
)
from openverify.relay.ports import (
    AvailableProvider,
    EventSink,
    InvocationReport,
    InvocationRequest,
)


class InvalidProviderOutput(ProviderContractError):
    def __init__(self, outcome: Outcome, message: str) -> None:
        super().__init__("INVALID_PROVIDER_OUTPUT", message)
        self.outcome = outcome


class ObservedTransportFailure(ProviderContractError):
    """Actual terminal data observed before a subsequent stream/session failure."""

    def __init__(self, outcome: Outcome, code: str, message: str) -> None:
        super().__init__(code, message)
        self.outcome = outcome


class LocalDriver:
    def __init__(self, *, max_events: int = 10000, max_event_bytes: int = 16 * 1024 * 1024) -> None:
        if max_events < 1 or max_event_bytes < 1:
            raise ValueError("Event limits must be positive")
        self.max_events = max_events
        self.max_event_bytes = max_event_bytes

    async def execute(
        self,
        provider: AvailableProvider,
        request: InvocationRequest,
        timeout: float,
        emit: EventSink,
    ) -> InvocationReport:
        validator = LifecycleValidator(request.manifest)
        validator.initialize(
            {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]}
        )
        validator.accept(wire_data(request.invocation))
        events: list[ProviderEvent] = []
        event_bytes = 0

        def observe(event: ProviderEvent) -> None:
            nonlocal event_bytes
            event = parse_provider_event(wire_data(event))
            validator.event(wire_data(event))
            event_bytes += len(serialize(event).encode("utf-8"))
            if len(events) >= self.max_events or event_bytes > self.max_event_bytes:
                raise ProviderContractError(
                    "PROTOCOL_VIOLATION", "Provider event stream exceeded host limits"
                )
            events.append(deepcopy(event))
            emit(deepcopy(event))

        outcome: Outcome | None = None
        try:
            async with asyncio.timeout(timeout):
                outcome = await provider.transport.invoke(deepcopy(request), observe)
            outcome = parse_outcome(wire_data(outcome))
            try:
                validator.outcome(wire_data(outcome))
            except ProviderContractError as exc:
                if exc.code == "INVALID_PROVIDER_OUTPUT" and outcome.state == "COMPLETED":
                    return InvocationReport(
                        outcome,
                        tuple(events),
                        output_error=ExecutionError(code=exc.code, message=exc.message),
                    )
                raise
            validator.finish()
            return InvocationReport(outcome, tuple(events))
        except InvalidProviderOutput as exc:
            return InvocationReport(
                exc.outcome,
                tuple(events),
                output_error=ExecutionError(code=exc.code, message=exc.message),
            )
        except ObservedTransportFailure as exc:
            return InvocationReport(
                parse_outcome(wire_data(exc.outcome)),
                tuple(events),
                error=ExecutionError(code=exc.code, message=exc.message),
            )
        except Exception as exc:
            code = (
                exc.code
                if isinstance(exc, ProviderContractError)
                else ("TIMEOUT" if isinstance(exc, TimeoutError) else "TRANSPORT_ERROR")
            )
            return InvocationReport(
                events=tuple(events), error=ExecutionError(code=code, message=str(exc) or code)
            )
