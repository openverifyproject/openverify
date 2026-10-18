"""An allowlisted host boundary shared by MCP and HTTP."""

import asyncio
from collections.abc import Mapping

from openverify.authoring import Graph
from openverify.inspection import inspect_definition
from openverify.model import Context, VerificationDefinition
from openverify.relay import Relay
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
    ) -> None:
        self.relay = relay if relay is not None else Relay()
        if max_concurrent_runs < 1:
            raise ValueError("max_concurrent_runs must be positive")
        self._limit = asyncio.Semaphore(max_concurrent_runs)
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
