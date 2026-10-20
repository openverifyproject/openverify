"""An allowlisted host boundary shared by MCP and HTTP."""
# pyright: basic

import asyncio
from collections.abc import Mapping
from typing import cast

from openverify.authoring import Graph
from openverify.inspection import inspect_definition
from openverify.lifecycle import Cancellation
from openverify.model import Context, VerificationDefinition
from openverify.relay import Relay
from openverify.relay.adapters.sqlite import SQLiteStore
from openverify.relay.errors import RelayError
from openverify.relay.templates import guardrail_graph, text_graph
from openverify.serialization import serialize, to_data
from openverify.validation import parse_definition


class GraphService:
    def __init__(
        self,
        relay: Relay | None = None,
        graphs: Mapping[str, Graph | VerificationDefinition] | None = None,
        max_concurrent_runs: int = 8,
        registry: SQLiteStore | None = None,
    ) -> None:
        self.relay = relay if relay is not None else Relay()
        if max_concurrent_runs < 1:
            raise ValueError("max_concurrent_runs must be positive")
        self._limit = asyncio.Semaphore(max_concurrent_runs)
        self.registry = registry
        self._active: dict[str, Cancellation] = {}
        supplied = (
            graphs if graphs is not None else {"text": text_graph(), "guardrail": guardrail_graph()}
        )
        self._graphs = {
            name: serialize(g.build() if isinstance(g, Graph) else g)
            for name, g in supplied.items()
        }

    def definition(self, name: str) -> VerificationDefinition:
        if name not in self._graphs:
            raise RelayError("GRAPH_UNAVAILABLE", "Graph is not authorized by this host")
        return parse_definition(self._graphs[name])

    def list_graphs(self) -> list[str]:
        return sorted(self._graphs)

    def describe_graph(self, name: str) -> Context:
        return inspect_definition(self.definition(name))

    async def run_graph(self, name: str, inputs: Context) -> Context:
        async with self._limit:
            result = await self.relay.run(self.definition(name), inputs=inputs)
        data = to_data(result.record)
        assert isinstance(data, dict)
        return data

    def inspect_result(self, run_id: str) -> Context:
        record = self.relay.store.get(run_id)
        if record is None:
            raise RelayError("RUN_UNAVAILABLE", "Run is not retained by this service")
        data = to_data(record)
        assert isinstance(data, dict)
        return data

    def register(self, definition: Context) -> Context:
        if self.registry is None:
            raise RelayError("REGISTRY_UNAVAILABLE", "Persistent graph registry is not configured")
        return cast(Context, self.registry.register(definition))

    def replace(self, graph_id: str, definition: Context) -> Context:
        if self.registry is None:
            raise RelayError("REGISTRY_UNAVAILABLE", "Persistent graph registry is not configured")
        return cast(Context, self.registry.replace(graph_id, definition))

    def retrieve(self, graph_id: str, revision: int | None = None) -> Context:
        if self.registry is None:
            raise RelayError("REGISTRY_UNAVAILABLE", "Persistent graph registry is not configured")
        return cast(Context, self.registry.definition(graph_id, revision))

    async def execute(
        self,
        graph_id: str,
        inputs: Context,
        revision: int | None = None,
        request_id: str | None = None,
    ) -> Context:
        from uuid import uuid4

        if self.registry is None:
            raise RelayError("REGISTRY_UNAVAILABLE", "Persistent graph registry is not configured")
        selected = self.retrieve(graph_id, revision)
        request_id = request_id or str(uuid4())
        token = Cancellation()
        self.registry.begin(request_id, graph_id, cast(int, selected["revision"]))
        self._active[request_id] = token
        try:
            async with self._limit:
                run = await self.relay.run(
                    parse_definition(selected["definition"]), inputs=inputs, cancellation=token
                )
            record = serialize(run.record)
            self.registry.finish(request_id, "COMPLETED", record=record)
            return {
                "request_id": request_id,
                "graph_id": graph_id,
                "revision": selected["revision"],
                "state": "COMPLETED",
                "record": to_data(run.record),
            }
        except BaseException as exc:
            state = "INTERRUPTED" if isinstance(exc, asyncio.CancelledError) else "ERROR"
            self.registry.finish(request_id, state, reason=str(exc))
            raise
        finally:
            self._active.pop(request_id, None)

    def lookup(self, request_id: str) -> Context:
        if self.registry is None:
            raise RelayError("REGISTRY_UNAVAILABLE", "Persistent graph registry is not configured")
        row = self.registry.run(request_id)
        if row["record"] is not None:
            import json

            row["record"] = json.loads(row["record"])
        return row

    def cancel(self, request_id: str) -> Context:
        token = self._active.get(request_id)
        if token is None:
            return self.lookup(request_id)
        token.cancel("Relay Client cancellation")
        return {"request_id": request_id, "state": "CANCELLING"}
