"""Real external process sessions, failures, and cooperative cancellation."""

import asyncio
import sys
from pathlib import Path

import pytest

from openverify import Relay
from openverify.lifecycle import Cancellation
from openverify.relay import RuntimeConfig
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.adapters.logging import CallbackObserver
from openverify.relay.adapters.stdio import StdioTransport
from openverify.relay.ports import RelayEvent
from tests.relay.helpers import echo_graph, echo_provider

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "mode", ["ok", "exit", "malformed", "correlation", "duplicate", "hang", "missing"]
)
def test_external_sessions(mode: str) -> None:
    catalog = Catalog()
    argv = (
        (sys.executable, "-m", "tests.relay.stdio_peer", mode)
        if mode != "missing"
        else (str(ROOT / "nonexistent-executable"),)
    )
    catalog.register_transport(echo_provider().manifest(), StdioTransport(argv, str(ROOT)))
    run = Relay(catalog=catalog, config=RuntimeConfig(timeout=5)).run_sync(
        echo_graph(), inputs={"x": "external"}
    )
    record = run.record.nodes[0]
    if mode == "ok":
        assert record.state == "SUCCESS" and record.information == {"x": "external"}, run.to_json()
    else:
        assert record.state == "ERROR" and record.result is not None
        assert record.result.verdict is None
    assert record.provider_binding is not None


def test_external_cancel_received_and_process_cleaned(tmp_path: Path) -> None:
    async def scenario() -> None:
        marker = tmp_path / "cancel.txt"
        catalog = Catalog()
        catalog.register_transport(
            echo_provider().manifest(),
            StdioTransport(
                (sys.executable, "-m", "tests.relay.stdio_peer", "hang", str(marker)), str(ROOT)
            ),
        )
        accepted = asyncio.Event()

        def observed(event: RelayEvent) -> None:
            if event.kind == "provider_event":
                accepted.set()

        relay = Relay(
            catalog=catalog, config=RuntimeConfig(timeout=5), observer=CallbackObserver(observed)
        )
        token = Cancellation()
        task = asyncio.create_task(relay.run(echo_graph(), inputs={"x": 1}, cancellation=token))
        async with asyncio.timeout(4):
            await accepted.wait()
        token.cancel("Host ended attempt")
        result = await task
        assert result.record.nodes[0].state == "CANCELLED"
        assert marker.read_text() == "cancel received"

    asyncio.run(scenario())
