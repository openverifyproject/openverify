"""Relay test authors use public SDK/Provider APIs, never the Reference Engine."""

import asyncio
from collections.abc import AsyncIterator

from pydantic import JsonValue

from openverify import Graph
from openverify.authoring import constant
from openverify.model import Context, Result
from openverify.provider import Invocation, Outcome, ProviderEvent, ProviderManifest
from openverify.relay import provider
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.providers import FunctionProvider
from openverify.standard.common import OBJECT, STRING, object_schema


def known(verdict: str = "PASS", **fields: JsonValue) -> Result:
    return Result.model_validate(
        {
            "disposition": "EXECUTED",
            "execution_outcome": "SUCCESS",
            "applicability": "APPLICABLE",
            "determination": "KNOWN",
            "verdict": verdict,
            **fields,
        }
    )


def echo_provider(*, provider_id: str = "com.example.echo", delay: float = 0) -> FunctionProvider:
    @provider(
        provider_id=provider_id,
        capability_id="com.example.echo",
        kind="DERIVE",
        input_schema=object_schema({"x": True}),
        output_schema=object_schema({"x": True}),
        config_schema=object_schema({}),
    )
    async def echo(inputs: Context, config: Context) -> Context:
        await asyncio.sleep(delay)
        return {"x": inputs["x"]}

    return echo


def echo_graph(id: str = "echo") -> Graph:
    graph = Graph(id)
    x = graph.input("x", True)
    graph.derive("echo", "com.example.echo", inputs={"x": x}, outputs={"x": True})
    return graph


def local_catalog(implementation: FunctionProvider | None = None) -> Catalog:
    result = Catalog()
    result.register(
        implementation if implementation is not None else echo_provider(), concurrency_safe=True
    )
    return result


class Scripted:
    def __init__(
        self, items: list[ProviderEvent | Outcome], manifest: ProviderManifest | None = None
    ) -> None:
        self.items = items
        self.specification = manifest if manifest is not None else echo_provider().manifest()

    def manifest(self) -> ProviderManifest:
        return self.specification

    async def cancel(self, invocation_id: str, reason: str | None = None) -> None:
        pass

    async def invoke(self, invocation: Invocation) -> AsyncIterator[ProviderEvent | Outcome]:
        for item in self.items:
            yield item.model_copy(update={"invocation_id": invocation.invocation_id})


def evaluator_graph(capability: str = "com.example.judge") -> Graph:
    graph = Graph("evaluation")
    graph.evaluate("check", capability, inputs={"x": constant("hello", STRING)})
    return graph


def judge_provider(result: Result | None = None) -> FunctionProvider:
    @provider(
        provider_id="com.example.judge",
        capability_id="com.example.judge",
        kind="EVALUATE",
        input_schema=object_schema({"x": STRING, "subject": OBJECT, "criterion": OBJECT}),
        output_schema=object_schema({"result": OBJECT}),
        config_schema=object_schema({}),
    )
    async def evaluate(inputs: Context, config: Context) -> Result:
        return result if result is not None else known()

    return evaluate
