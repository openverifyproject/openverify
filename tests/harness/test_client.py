# pyright: basic
import asyncio
import json
import os
from typing import cast

import pytest

from openverify.relay import Relay
from openverify.relay.adapters.sqlite import SQLiteStore
from openverify.relay.entrypoints.client import validate_request
from openverify.relay.entrypoints.service import GraphService
from openverify.relay.errors import RelayError
from openverify.relay.templates import text_graph
from openverify.serialization import to_data


def test_revisions_runs_and_restart(tmp_path):
    path = tmp_path / "relay.db"
    store = SQLiteStore(path)
    service = GraphService(Relay(store=store), registry=store)
    definition = cast(dict, to_data(text_graph().build()))
    registered = service.register(definition)
    graph_id = cast(str, registered["graph_id"])
    assert registered["revision"] == 1
    assert service.replace(graph_id, definition)["revision"] == 2
    assert service.retrieve(graph_id, 1)["definition"] == definition
    first = asyncio.run(service.execute(graph_id, {"text": "Migration Rollback"}, 1))
    second = asyncio.run(service.execute(graph_id, {"text": "TODO"}, 2))
    assert first["request_id"] != second["request_id"]
    assert first["revision"] == 1 and second["revision"] == 2
    assert service.lookup(cast(str, first["request_id"]))["state"] == "COMPLETED"
    store.connection.close()
    reopened = SQLiteStore(path)
    assert reopened.run(cast(str, second["request_id"]))["revision"] == 2
    reopened.begin("in-flight", graph_id, 1)
    reopened.connection.close()
    assert SQLiteStore(path).run("in-flight")["state"] == "INTERRUPTED"


def test_binding_failure_is_a_persisted_error(tmp_path):
    from openverify.authoring import Graph

    store = SQLiteStore(tmp_path / "failures.db")
    service = GraphService(Relay(store=store), registry=store)
    graph = Graph("missing-provider")
    graph.evaluate("check", "example.provider.unavailable")
    graph_id = cast(str, service.register(cast(dict, to_data(graph.build())))["graph_id"])
    with pytest.raises(RelayError):
        asyncio.run(service.execute(graph_id, {}, request_id="failed-binding"))
    assert service.lookup("failed-binding")["state"] == "ERROR"
    assert service.lookup("failed-binding")["record"] is None


def test_client_json_stdin(tmp_path):
    import subprocess
    import sys

    definition = to_data(text_graph().build())
    command = [
        sys.executable,
        "-m",
        "openverify.relay.entrypoints.client",
        "--database",
        str(tmp_path / "client.db"),
    ]
    requests = [
        {"client_version": "1", "id": "one", "op": "register", "definition": definition},
        {"client_version": "1", "id": "bad", "op": "missing"},
    ]
    process = subprocess.run(
        command,
        input="".join(json.dumps(r) + "\n" for r in requests),
        text=True,
        capture_output=True,
        check=True,
    )
    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert {r["id"] for r in responses} == {"one", "bad"}
    assert next(r for r in responses if r["id"] == "one")["ok"]
    assert not next(r for r in responses if r["id"] == "bad")["ok"]


def test_portable_client_request_fixtures():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "conformance/relay-client-v1"
    for path in (root / "valid").glob("*.json"):
        assert validate_request(json.loads(path.read_text()))
    for path in (root / "invalid").glob("*.json"):
        with pytest.raises(ValueError):
            validate_request(json.loads(path.read_text()))


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Release TBD", "FAIL"), ("ERROR", "ERROR"), ("WAIT", "CANCELLED")],
)
def test_node_client_python_relay_node_provider(tmp_path, text, expected):
    import runpy
    import shutil
    import subprocess
    import sys
    from pathlib import Path

    from openverify.provider import wire_data

    if os.environ.get("OPENVERIFY_TEST_NODE") != "1":
        pytest.skip("Node interoperability runs in the dedicated Node job")

    node = shutil.which("node")
    if not node:
        pytest.skip("Node is unavailable")
    repository = Path(__file__).resolve().parents[2]
    namespace = runpy.run_path(str(repository / "examples/custom-provider/check.py"))
    manifest = tmp_path / "manifest.json"
    graph = tmp_path / "graph.json"
    fixture = repository / "tests/harness/node_contract_fixture.cjs"
    manifest.write_text(json.dumps(wire_data(namespace["prohibited_phrase"].manifest())))
    graph.write_text(namespace["graph"]().to_json())
    (tmp_path / "openverify.toml").write_text(
        "[[providers.stdio]]\n"
        f"argv = {json.dumps([node, str(fixture), 'provider', str(manifest)])}\n"
        "manifest_file = 'manifest.json'\n"
        "cwd = '.'\n",
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            node,
            str(fixture),
            "client",
            sys.executable,
            "-",
            str(graph),
            str(tmp_path / "runs.db"),
            text,
        ],
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                str(repository / part)
                for part in ("src", "packages/code/src", "packages/english/src")
            ),
        },
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    record = json.loads(completed.stdout)
    assert record["state"] == "COMPLETED"
    result = record["record"]["final_results"]["phrase"]
    observed = result.get("verdict") or result.get("execution_outcome") or result["disposition"]
    assert observed == expected
