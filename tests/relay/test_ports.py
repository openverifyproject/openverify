"""Each actual port can be replaced independently with small host implementations."""

from collections.abc import Sequence

import pytest

from openverify import Relay
from openverify.model import OperationRequirement, ProviderBinding, RunRecord
from openverify.relay.adapters.binder import DeterministicBinder
from openverify.relay.adapters.local import LocalDriver
from openverify.relay.adapters.memory import MemoryStore
from openverify.relay.ports import (
    AvailableProvider,
    EventSink,
    InvocationReport,
    InvocationRequest,
    RelayEvent,
)
from tests.relay.helpers import echo_graph, local_catalog


class HostBinder:
    def __init__(self) -> None:
        self.calls = 0

    def bind(
        self,
        requirement: OperationRequirement,
        providers: Sequence[AvailableProvider],
        explicit: ProviderBinding | None = None,
    ) -> AvailableProvider:
        self.calls += 1
        return DeterministicBinder().bind(requirement, providers, explicit)


class HostDriver:
    def __init__(self) -> None:
        self.calls = 0

    async def execute(
        self,
        provider: AvailableProvider,
        request: InvocationRequest,
        timeout: float,
        emit: EventSink,
    ) -> InvocationReport:
        self.calls += 1
        return await LocalDriver().execute(provider, request, timeout, emit)


class HostStore:
    def __init__(self) -> None:
        self.memory = MemoryStore()
        self.calls = 0

    def put(self, record: RunRecord) -> None:
        self.calls += 1
        self.memory.put(record)

    def get(self, run_id: str) -> RunRecord | None:
        return self.memory.get(run_id)


class HostObserver:
    def __init__(self) -> None:
        self.calls = 0

    def observe(self, event: RelayEvent) -> None:
        self.calls += 1


@pytest.mark.parametrize("port", ["binder", "driver", "store", "observer"])
def test_independent_replacements(port: str) -> None:
    binder, driver, store, observer = HostBinder(), HostDriver(), HostStore(), HostObserver()
    relay = Relay(
        catalog=local_catalog(),
        binder=binder if port == "binder" else None,
        driver=driver if port == "driver" else None,
        store=store if port == "store" else None,
        observer=observer if port == "observer" else None,
    )
    result = relay.run_sync(echo_graph(), inputs={"x": "host-port"})
    assert result.record.nodes[0].information == {"x": "host-port"}
    replacement = {"binder": binder, "driver": driver, "store": store, "observer": observer}[port]
    assert replacement.calls > 0


def test_driver_cannot_bypass_correlation_validation() -> None:
    from openverify.provider import Outcome

    class IncorrectDriver:
        async def execute(
            self,
            provider: AvailableProvider,
            request: InvocationRequest,
            timeout: float,
            emit: EventSink,
        ) -> InvocationReport:
            return InvocationReport(
                outcome=Outcome(invocation_id="different-run", state="COMPLETED", output={"x": 1})
            )

    result = Relay(catalog=local_catalog(), driver=IncorrectDriver()).run_sync(
        echo_graph(), inputs={"x": 1}
    )
    assert result.results["echo"].execution_outcome == "ERROR"
