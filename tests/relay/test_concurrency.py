"""Actual overlap, deterministic acceptance, per-run isolation and cancellation."""

import asyncio

from openverify import Graph, Relay, parse_run_record
from openverify.authoring import constant
from openverify.lifecycle import Cancellation
from openverify.model import Context
from openverify.relay import RuntimeConfig, provider
from openverify.standard.common import OBJECT
from tests.relay.helpers import echo_graph, local_catalog


def test_independent_nodes_overlap_dependencies_wait_and_snapshots_isolate() -> None:
    async def scenario() -> None:
        entered: set[str] = set()
        together = asyncio.Event()

        @provider(
            provider_id="com.example.parallel",
            capability_id="com.example.echo",
            kind="DERIVE",
            input_schema=OBJECT,
            output_schema=OBJECT,
            config_schema=OBJECT,
        )
        async def echo(inputs: Context, config: Context) -> Context:
            name = str(inputs["x"])
            entered.add(name)
            if len(entered) == 2:
                together.set()
            async with asyncio.timeout(2):
                await together.wait()
            await asyncio.sleep(0.01 if name == "first" else 0.001)
            return {"x": inputs["x"]}

        catalog = local_catalog(echo)
        graph = Graph("parallel")
        a = graph.derive(
            "a", "com.example.echo", inputs={"x": constant("first")}, outputs={"x": True}
        )
        b = graph.derive(
            "b", "com.example.echo", inputs={"x": constant("second")}, outputs={"x": True}
        )
        graph.derive(
            "join", "com.example.echo", inputs={"x": a["x"]}, outputs={"x": True}, dependencies=[b]
        )
        run = await Relay(catalog=catalog).run(graph, inputs={})
        assert all(n.state == "SUCCESS" for n in run.record.nodes)
        a_record, b_record, join = run.record.nodes
        assert (
            a_record.started_at < b_record.finished_at
            and b_record.started_at < a_record.finished_at
        )
        assert join.started_at >= max(a_record.finished_at, b_record.finished_at)
        assert [n.node_id for n in run.record.nodes] == ["a", "b", "join"]
        assert parse_run_record(run.to_json()) == run.record

    asyncio.run(scenario())


def test_concurrent_graphs_different_inputs_and_no_cancellation_leakage() -> None:
    async def scenario() -> None:
        from tests.relay.helpers import echo_provider

        relay = Relay(catalog=local_catalog(echo_provider(delay=0.02)))
        token = Cancellation()
        token.cancel("Only A")
        first, second = await asyncio.gather(
            relay.run(echo_graph("security"), inputs={"x": {"worktree": "A"}}, cancellation=token),
            relay.run(echo_graph("formatting"), inputs={"x": {"worktree": "B"}}),
        )
        assert first.results["echo"].disposition == "CANCELLED"
        assert second.record.nodes[0].information == {"x": {"worktree": "B"}}
        assert first.record.run_id != second.record.run_id
        assert (
            first.record.definition.id == "security" and second.record.definition.id == "formatting"
        )
        assert not first.record.provider_bindings
        assert second.record.provider_bindings

    asyncio.run(scenario())


def test_running_cancellation_and_timeout_are_distinct() -> None:
    async def scenario() -> None:
        entered = asyncio.Event()
        cleaned = asyncio.Event()

        @provider(
            provider_id="com.example.hang",
            capability_id="com.example.echo",
            kind="DERIVE",
            input_schema=OBJECT,
            output_schema=OBJECT,
            config_schema=OBJECT,
        )
        async def hanging(inputs: Context, config: Context) -> Context:
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaned.set()
            return {"x": 1}

        relay = Relay(catalog=local_catalog(hanging), config=RuntimeConfig(timeout=0.1))
        token = Cancellation()
        task = asyncio.create_task(relay.run(echo_graph(), inputs={"x": 1}, cancellation=token))
        await entered.wait()
        token.cancel("Interrupted by host")
        run = await task
        assert cleaned.is_set()
        assert run.record.nodes[0].state == "CANCELLED"
        assert run.record.cancellation and run.record.cancellation.phase == "RUNNING"
        assert run.record.provider_bindings
        timeout = await relay.run(echo_graph(), inputs={"x": 2})
        assert timeout.results["echo"].execution_outcome == "ERROR"
        assert timeout.results["echo"].verdict is None
        assert timeout.record.nodes[0].reason == "TIMEOUT"

    asyncio.run(scenario())


def test_cancellation_observed_before_output_acceptance_wins_completion_race() -> None:
    async def scenario() -> None:
        token = Cancellation()

        @provider(
            provider_id="com.example.race",
            capability_id="com.example.echo",
            kind="DERIVE",
            input_schema=OBJECT,
            output_schema=OBJECT,
            config_schema=OBJECT,
        )
        async def echo(inputs: Context, config: Context) -> Context:
            token.cancel("Host cancellation before acceptance")
            return {"x": inputs["x"]}

        run = await Relay(catalog=local_catalog(echo)).run(
            echo_graph(), inputs={"x": 1}, cancellation=token
        )
        assert run.record.nodes[0].state == "CANCELLED"
        assert run.record.nodes[0].information == {}
        assert run.record.cancellation is not None and run.record.cancellation.phase == "RUNNING"
        assert parse_run_record(run.to_json()) == run.record

    asyncio.run(scenario())
