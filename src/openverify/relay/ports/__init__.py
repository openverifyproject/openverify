"""The six replaceable boundaries. No infrastructure or provider implementations."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from openverify.model import ExecutionError, OperationRequirement, ProviderBinding, RunRecord
from openverify.provider import Invocation, Outcome, ProviderEvent, ProviderManifest

type EventSink = Callable[[ProviderEvent], None]


@dataclass(frozen=True)
class InvocationRequest:
    manifest: ProviderManifest
    invocation: Invocation


class ProviderTransport(Protocol):
    async def invoke(self, request: InvocationRequest, emit: EventSink) -> Outcome: ...


@dataclass(frozen=True)
class AvailableProvider:
    manifest: ProviderManifest
    transport: ProviderTransport


@dataclass(frozen=True)
class InvocationReport:
    outcome: Outcome | None = None
    events: tuple[ProviderEvent, ...] = ()
    error: ExecutionError | None = None
    output_error: ExecutionError | None = None


@dataclass(frozen=True)
class RelayEvent:
    run_id: str
    kind: str
    node_id: str | None = None
    invocation_id: str | None = None
    event: ProviderEvent | None = None


class ProviderCatalog(Protocol):
    def providers(self) -> Sequence[AvailableProvider]: ...


class ProviderBinder(Protocol):
    def bind(
        self,
        requirement: OperationRequirement,
        providers: Sequence[AvailableProvider],
        explicit: ProviderBinding | None = None,
    ) -> AvailableProvider: ...


class ExecutionDriver(Protocol):
    async def execute(
        self,
        provider: AvailableProvider,
        request: InvocationRequest,
        timeout: float,
        emit: EventSink,
    ) -> InvocationReport: ...


class RecordStore(Protocol):
    def put(self, record: RunRecord) -> None: ...
    def get(self, run_id: str) -> RunRecord | None: ...


class EventObserver(Protocol):
    def observe(self, event: RelayEvent) -> None: ...
