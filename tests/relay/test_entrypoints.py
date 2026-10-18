"""Real CLI, official MCP client/server, HTTP, and executable custom providers."""

import asyncio
import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import cast

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openverify import parse_run_record
from openverify.model import Context
from openverify.relay.entrypoints.http import create_app

ROOT = Path(__file__).resolve().parents[2]


def cli(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "openverify.relay.entrypoints.cli", *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=20,
    )


def test_cli_json_stdin_exit_codes_validate_inspect_and_discovery(tmp_path: Path) -> None:
    for text, code in [("Migration Rollback", 0), ("Migration Rollback TODO", 1)]:
        result = cli("run", "text", "--inputs", "-", "--json", stdin=json.dumps({"text": text}))
        assert result.returncode == code, result.stderr
        assert not result.stderr
        record = parse_run_record(result.stdout)
        assert record.final_results["all"].verdict == ("PASS" if code == 0 else "FAIL")
    invalid = cli("run", "text", "--inputs", "-", "--json", stdin="{}")
    assert invalid.returncode == 2 and not invalid.stdout
    assert json.loads(invalid.stderr)["code"] == "RUN_INPUT"
    assert json.loads(cli("validate", "text").stdout) == {"valid": True}
    assert json.loads(cli("inspect", "text").stdout)["id"] == "text"
    assert "text" in json.loads(cli("examples").stdout)
    providers = json.loads(cli("providers", "list").stdout)
    assert providers and cli("providers", "inspect", providers[0]["provider_id"]).returncode == 0


def test_actual_mcp_server_discover_describe_invoke_and_inspect() -> None:
    async def scenario() -> None:
        parameters = StdioServerParameters(
            command=sys.executable, args=["-m", "openverify.relay.entrypoints.cli", "mcp"], cwd=ROOT
        )
        async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {t.name for t in tools.tools} == {
                "list_graphs",
                "describe_graph",
                "run_graph",
                "inspect_result",
            }
            listed = await session.call_tool("list_graphs", {})
            assert not listed.isError
            described = await session.call_tool("describe_graph", {"name": "text"})
            assert not described.isError
            result = await session.call_tool(
                "run_graph", {"name": "text", "inputs": {"text": "Migration Rollback"}}
            )
            assert not result.isError, result
            assert result.structuredContent is not None
            record = parse_run_record(cast(Context, result.structuredContent))
            assert record.final_results["all"].verdict == "PASS"
            retained = await session.call_tool("inspect_result", {"run_id": record.run_id})
            assert not retained.isError
            denied = await session.call_tool(
                "run_graph", {"name": "../../arbitrary.py", "inputs": {}}
            )
            assert denied.isError

    asyncio.run(scenario())


def test_optional_http_named_graphs_auth_and_bounds() -> None:
    async def scenario() -> None:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=create_app(token="local-secret", max_body_bytes=1024)
            ),
            base_url="http://testserver",
        ) as client:
            assert (await client.get("/health")).status_code == 200
            assert (await client.post("/verify", json={})).status_code == 401
            headers = {"authorization": "Bearer local-secret"}
            response = await client.post(
                "/verify",
                headers=headers,
                json={"graph": "text", "inputs": {"text": "Migration Rollback"}},
            )
            assert response.status_code == 200
            assert parse_run_record(response.content).final_results["all"].verdict == "PASS"
            assert (
                await client.post(
                    "/verify", headers=headers, json={"graph": "arbitrary", "inputs": {}}
                )
            ).status_code == 400
            assert (
                await client.post("/verify", headers=headers, content=b"a" * 1025)
            ).status_code == 413

    asyncio.run(scenario())


def test_custom_provider_example_and_real_stdio_example(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "examples/custom-provider/check.py")],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    manifest, record = result.stdout.splitlines()
    assert json.loads(manifest)["provider_id"] == "com.example.phrase_provider"
    assert parse_run_record(record).final_results["phrase"].verdict == "FAIL"
    # Independently register its manifest and external process without modifying Relay.
    from openverify import Graph, Relay
    from openverify.provider import parse_provider_manifest
    from openverify.relay.adapters.catalog import Catalog
    from openverify.relay.adapters.stdio import StdioTransport

    graph = Graph("external")
    text = graph.input("text", {"type": "string"})
    graph.evaluate(
        "phrase", "com.example.prohibited_phrase", inputs={"text": text}, config={"phrase": "TBD"}
    )
    catalog = Catalog()
    catalog.register_transport(
        parse_provider_manifest(manifest),
        StdioTransport(
            (sys.executable, str(ROOT / "examples/stdio-provider/provider.py")), str(ROOT)
        ),
    )
    run = Relay(catalog=catalog).run_sync(graph, inputs={"text": "TBD"})
    assert run.results["phrase"].verdict == "FAIL", run.to_json()
    exported = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples/stdio-provider/run.py"),
            "--export-dir",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=20,
    )
    assert exported.returncode == 0, exported.stderr
    command = cli(
        "run",
        str(tmp_path / "graph.json"),
        "--inputs",
        str(tmp_path / "inputs.json"),
        "--providers",
        str(tmp_path / "providers.json"),
        "--json",
    )
    assert command.returncode == 1, command.stderr
    assert parse_run_record(command.stdout).final_results["phrase"].verdict == "FAIL"


def test_http_over_actual_localhost_socket() -> None:
    from openverify.relay.adapters.process import spawn, terminate

    async def scenario() -> None:
        with socket.socket() as available:
            available.bind(("127.0.0.1", 0))
            port = available.getsockname()[1]
        process = await spawn(
            (sys.executable, "-m", "openverify.relay.entrypoints.cli", "http", "--port", str(port)),
            str(ROOT),
        )
        try:
            async with httpx.AsyncClient(
                base_url=f"http://127.0.0.1:{port}", trust_env=False
            ) as client:
                async with asyncio.timeout(10):
                    while True:
                        try:
                            response = await client.get("/health", timeout=0.25)
                            if response.status_code == 200:
                                break
                        except (httpx.ConnectError, httpx.ConnectTimeout):
                            pass
                        await asyncio.sleep(0.05)
                response = await client.post(
                    "/verify", json={"graph": "text", "inputs": {"text": "Migration Rollback"}}
                )
                assert response.status_code == 200
                assert parse_run_record(response.content).final_results["all"].verdict == "PASS"
        finally:
            await terminate(process)

    asyncio.run(scenario())


def test_all_advertised_python_examples(tmp_path: Path) -> None:
    import os

    for file in (
        "guardrail/run.py",
        "application-integration/run.py",
        "custom-graph/run.py",
        "multi-agent/run.py",
        "code-verification/run.py",
        "stdio-provider/run.py",
    ):
        result = subprocess.run(
            [sys.executable, str(ROOT / "examples" / file)],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=45,
            env={**os.environ, "TEMP": str(tmp_path), "TMP": str(tmp_path)},
        )
        assert result.returncode == 0, f"{file}: {result.stderr} {result.stdout[-2000:]}"
