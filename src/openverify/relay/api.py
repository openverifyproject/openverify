"""Small public facade and default composition root."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar
from uuid import uuid4

from openverify.authoring import Graph
from openverify.errors import ProtocolError
from openverify.lifecycle import Cancellation
from openverify.model import (
    Context,
    Decision,
    Evidence,
    ResourceVector,
    Result,
    RunRecord,
    VerificationDefinition,
)
from openverify.provider import ProviderContractError
from openverify.relay.adapters.binder import DeterministicBinder
from openverify.relay.adapters.local import LocalDriver
from openverify.relay.adapters.logging import LoggingObserver
from openverify.relay.adapters.memory import MemoryStore
from openverify.relay.application.run import coordinate
from openverify.relay.config import RuntimeConfig
from openverify.relay.errors import RelayError
from openverify.relay.ports import (
    EventObserver,
    ExecutionDriver,
    ProviderBinder,
    ProviderCatalog,
    RecordStore,
)
from openverify.serialization import serialize
from openverify.validation import parse_definition


@dataclass(frozen=True)
class Run:
    record: RunRecord

    @property
    def results(self) -> dict[str, Result]:
        return dict(self.record.final_results)

    @property
    def decisions(self) -> dict[str, Decision]:
        return {n.node_id: n.decision for n in self.record.nodes if n.decision is not None}

    @property
    def evidence(self) -> dict[str, list[Evidence]]:
        return {
            n.node_id: [
                *(n.observation.evidence if n.observation else []),
                *(n.result.evidence if n.result else []),
            ]
            for n in self.record.nodes
        }

    @property
    def usage(self) -> dict[str, ResourceVector]:
        return {n.node_id: dict(n.usage) for n in self.record.nodes}

    def to_json(self) -> str:
        return serialize(self.record)


def passing_gate(run: Run) -> bool:
    """Fail closed unless all recorded judgments executed successfully and passed."""
    return bool(run.results) and all(
        r.disposition == "EXECUTED"
        and r.execution_outcome == "SUCCESS"
        and r.applicability == "APPLICABLE"
        and r.determination == "KNOWN"
        and r.verdict == "PASS"
        for r in run.results.values()
    )


T = TypeVar("T")


class Relay:
    def __init__(
        self,
        *,
        catalog: ProviderCatalog | None = None,
        binder: ProviderBinder | None = None,
        driver: ExecutionDriver | None = None,
        store: RecordStore | None = None,
        observer: EventObserver | None = None,
        config: RuntimeConfig | None = None,
    ) -> None:
        if catalog is None:
            from openverify.standard import standard_catalog

            try:
                catalog = standard_catalog()
            except (ProtocolError, ProviderContractError):
                raise
            except Exception as exc:
                raise RelayError(
                    "CATALOG_FAILURE",
                    "Default provider catalog initialization failed",
                    details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
                ) from exc
        self.catalog = catalog
        self.binder = binder if binder is not None else DeterministicBinder()
        self.driver = driver if driver is not None else LocalDriver()
        self.store = store if store is not None else MemoryStore()
        self.observer = observer if observer is not None else LoggingObserver()
        self.config = config if config is not None else RuntimeConfig()

    async def run(
        self,
        graph: Graph | VerificationDefinition | str | bytes,
        *,
        inputs: Context,
        opportunity_id: str | None = None,
        cancellation: Cancellation | None = None,
    ) -> Run:
        definition = (
            graph.build()
            if isinstance(graph, Graph)
            else (parse_definition(graph) if isinstance(graph, (str, bytes)) else graph)
        )
        record = await coordinate(
            definition,
            inputs,
            self.config,
            self.catalog,
            self.binder,
            self.driver,
            self.store,
            self.observer,
            str(uuid4()) if opportunity_id is None else opportunity_id,
            cancellation,
        )
        return Run(record)

    def run_sync(
        self,
        graph: Graph | VerificationDefinition | str | bytes,
        *,
        inputs: Context,
        opportunity_id: str | None = None,
    ) -> Run:
        return asyncio.run(self.run(graph, inputs=inputs, opportunity_id=opportunity_id))

    async def verify_before(
        self,
        action: Callable[[], Awaitable[T]],
        graph: Graph | VerificationDefinition,
        *,
        inputs: Context,
        gate_policy: Callable[[Run], bool] = passing_gate,
    ) -> T:
        run = await self.run(graph, inputs=inputs)
        if not gate_policy(run):
            raise RelayError(
                "GATE_REJECTED", f"Verification rejected action; run={run.record.run_id}"
            )
        return await action()
