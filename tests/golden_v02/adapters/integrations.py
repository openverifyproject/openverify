"""Real public entrypoint clients; returned records use the same VCP assertions."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import shutil
import sysconfig
import tempfile
from pathlib import Path

from tools.golden_v02.build_baseline import node, definition, result, scenario, behavior
from tools.golden_v02.compare import equal
from tools.golden_v02.execution import AdapterGap, EnvironmentUnavailable
from tests.golden_v02.adapters.public import prepare
from tools.golden_v02.verify_manifest import ROOT


def console():
    path = shutil.which(
        "openverify", path=sysconfig.get_path("scripts") + os.pathsep + os.environ.get("PATH", "")
    )
    if path is None:
        raise EnvironmentUnavailable("installed openverify console script absent")
    return path


def environment():
    return {**os.environ, "PYTHONPATH": str(ROOT / "src") + os.pathsep + str(ROOT)}


def terminal(record, expected):
    judgments = [
        r
        for r in record["final_results"].values()
        if r.get("execution_outcome") == "SUCCESS" and r.get("verdict")
    ]
    assert judgments, "no terminal binary Results"
    equal(expected, record["final_results"]["all"]["verdict"])
    assert record["provider_bindings"]
    for n in record["nodes"]:
        for value in n["input_values"].values():
            # Preserve arbitrary JSON as provided; no JSON type coercion.
            json.dumps(value, allow_nan=False)


async def python_entry(variant):
    from openverify import Relay
    from openverify.relay.templates import text_graph

    graph = text_graph()
    if variant == "json":
        graph = graph.to_json()
    elif variant == "model":
        graph = graph.build()
    if variant == "sync":
        run = await asyncio.to_thread(
            Relay().run_sync, graph, inputs={"text": "Migration Rollback"}
        )
    else:
        run = await Relay().run(graph, inputs={"text": "Migration Rollback"})
    record = json.loads(run.to_json())
    terminal(record, "PASS")
    return {"verified": True, "record": record}


async def cli(variant):
    command = [console(), "run", "text", "--inputs", "-", "--json"]
    supplied = {"text": "Migration TODO" if variant == "fail_stdin" else "Migration Rollback"}
    expected_exit = 1 if variant == "fail_stdin" else 0
    if variant == "invalid_input":
        supplied = {"undeclared": True}
        expected_exit = 2
    if variant == "both_stdin_reject":
        command[2] = "-"
        expected_exit = 2
    with tempfile.TemporaryDirectory(prefix="golden-cli-") as folder:
        root = Path(folder)
        if variant == "graph_stdin":
            from openverify.relay.templates import text_graph

            input_file = root / "inputs.json"
            input_file.write_text(json.dumps(supplied), encoding="utf-8")
            command = [
                console(),
                "run",
                "-",
                "--inputs",
                str(input_file),
                "--json",
            ]
            raw = text_graph().to_json()
        elif variant == "error_exit":
            command = [
                console(),
                "run",
                "document",
                "--inputs",
                "-",
                "--json",
                "--root",
                folder,
            ]
            supplied = {"file": str(root / "missing.txt")}
            expected_exit = 2
            raw = json.dumps(supplied)
        elif variant == "unknown_exit":
            from openverify.provider import wire_data
            from tests.golden_v02.adapters.public import manifest_for

            n = node("unknown", "EVALUATE")
            requirement = n["operation"]
            manifest = wire_data(manifest_for("unknown", requirement))
            peer = root / "peer.json"
            peer.write_text(
                json.dumps(
                    {
                        "manifest": manifest,
                        "behaviors": {
                            requirement["capability_id"]: {"outputs": {"result": result("UNKNOWN")}}
                        },
                    }
                ),
                encoding="utf-8",
            )
            config = root / "providers.json"
            config.write_text(
                json.dumps(
                    {
                        "stdio": [
                            {
                                "manifest": manifest,
                                "argv": [
                                    sys.executable,
                                    str(ROOT / "tools/golden_v02/stdio_provider.py"),
                                    "--spec",
                                    str(peer),
                                ],
                                "cwd": str(ROOT),
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            graph = root / "graph.json"
            graph.write_text(json.dumps(definition([n])), encoding="utf-8")
            command = [
                console(),
                "run",
                str(graph),
                "--inputs",
                "-",
                "--providers",
                str(config),
                "--json",
            ]
            supplied = {}
            raw = "{}"
            expected_exit = 3
        else:
            raw = json.dumps(supplied)
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=ROOT,
            env=environment(),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(raw.encode("utf-8")), 20)
        finally:
            if process.returncode is None:
                process.kill()
                await process.wait()
        equal(expected_exit, process.returncode, "/exit_code")
        if variant in ("pass_stdin", "fail_stdin", "graph_stdin"):
            record = json.loads(stdout)
            terminal(record, "FAIL" if variant == "fail_stdin" else "PASS")
        elif variant in ("error_exit", "unknown_exit"):
            record = json.loads(stdout)
            assert record["protocol"] == "draft"
        else:
            assert stderr, "invalid CLI request has no diagnostic"
        return {
            "verified": True,
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
        }


async def http(variant):
    try:
        import httpx
        from openverify.relay.entrypoints.http import create_app
    except ImportError as exc:
        raise EnvironmentUnavailable("optional HTTP dependencies absent: " + str(exc)) from exc
    app = create_app(token="golden-token")
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://golden.invalid"
    ) as client:
        if variant == "health":
            response = await client.get("/health")
            equal(200, response.status_code)
            equal("draft", response.json()["protocol"])
        else:
            headers = {
                "Authorization": "Bearer " + ("bad" if variant == "bad_token" else "golden-token")
            }
            if variant == "oversized":
                response = await client.post(
                    "/verify", content=b"x" * (1024 * 1024 + 1), headers=headers
                )
                equal(413, response.status_code)
            else:
                response = await client.post(
                    "/verify",
                    json={
                        "graph": "untrusted" if variant == "unknown_graph" else "text",
                        "inputs": {
                            "text": "Migration TODO" if variant == "fail" else "Migration Rollback"
                        },
                    },
                    headers=headers,
                )
                equal(
                    401 if variant == "bad_token" else 400 if variant == "unknown_graph" else 200,
                    response.status_code,
                )
                if variant in ("pass", "fail"):
                    terminal(response.json(), "FAIL" if variant == "fail" else "PASS")
        return {"verified": True, "http_status": response.status_code, "body": response.json()}


async def mcp(variant):
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError as exc:
        raise EnvironmentUnavailable("optional official MCP SDK absent: " + str(exc)) from exc
    params = StdioServerParameters(
        command=console(), args=["mcp"], env=environment(), cwd=str(ROOT)
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            if variant == "tools":
                names = sorted(t.name for t in (await session.list_tools()).tools)
                equal(["describe_graph", "inspect_result", "list_graphs", "run_graph"], names)
                return {"verified": True, "tools": names}
            if variant == "list":
                response = await session.call_tool("list_graphs", {})
            elif variant == "describe":
                response = await session.call_tool("describe_graph", {"name": "text"})
            elif variant == "unauthorized":
                response = await session.call_tool(
                    "run_graph", {"name": "not-allowlisted", "inputs": {}}
                )
                assert response.isError
                return {"verified": True, "unauthorized_rejected": True}
            else:
                response = await session.call_tool(
                    "run_graph",
                    {
                        "name": "text",
                        "inputs": {
                            "text": "Migration TODO"
                            if variant == "run_fail"
                            else "Migration Rollback"
                        },
                    },
                )
            assert not response.isError
            # Official SDK structuredContent can wrap non-object return values;
            # RunRecord object results are required to remain full structures.
            body = response.structuredContent
            if body is None:
                body = json.loads(next(c.text for c in response.content if c.type == "text"))
            if variant in ("run_pass", "run_fail", "inspect"):
                terminal(body, "FAIL" if variant == "run_fail" else "PASS")
                if variant == "inspect":
                    inspected = await session.call_tool(
                        "inspect_result", {"run_id": body["run_id"]}
                    )
                    stored = inspected.structuredContent or json.loads(
                        next(c.text for c in inspected.content if c.type == "text")
                    )
                    equal(body, stored)
            elif variant == "list":
                assert "text" in str(body) and "guardrail" in str(body)
            else:
                assert "text" in str(body)
            return {"verified": True, "body": body}


async def guardrail(variant):
    from openverify import parse_definition, parse_run_record
    from openverify.relay import Run, passing_gate

    n = node("gate", "EVALUATE")
    sc = scenario([n], [], {"gate": behavior({"result": result(variant)})}, {})
    # Nonexecution is a runner lifecycle fact, never valid evaluator output.
    if variant in ("SKIP", "DEFERRED"):
        sc["definition"]["execution_policy"]["admission"] = (
            {"strategy": "PROBABILITY", "probability": 0}
            if variant == "SKIP"
            else {
                "operation": {
                    "capability_id": "com.example.golden.policy_admission",
                    "capability_version": "1",
                },
                "inputs": [],
                "bindings": {},
                "config": {},
            }
        )
        if variant == "DEFERRED":
            sc["policies"] = {"ADMISSION": {"outcome": "DEFER", "reason": "golden.defer"}}
    bound = prepare(sc)
    calls = []

    async def action():
        calls.append("authorized")
        return "performed"

    if variant == "CANCELLED":
        from openverify.lifecycle import Cancellation

        token = Cancellation()
        token.cancel("golden.gate.cancel")
        record = await bound.invoke(cancellation=token)
        equal("CANCELLED", record["nodes"][0]["result"]["disposition"])
        assert not passing_gate(Run(parse_run_record(record)))
        equal([], calls)
        return {"verified": True, "action_calls": calls, "gate": False}
    try:
        returned = await bound.relay.verify_before(
            action, parse_definition(bound.definition), inputs={}
        )
    except Exception as exc:
        assert variant != "PASS", exc
        from openverify.relay.errors import RelayError

        assert isinstance(exc, RelayError), "unstructured guardrail rejection"
        assert not calls, "rejected action executed"
        return {
            "verified": True,
            "action_calls": calls,
            "rejection": getattr(exc, "code", type(exc).__name__),
        }
    equal("PASS", variant)
    equal(["authorized"], calls)
    equal("performed", returned)
    return {"verified": True, "action_calls": calls}


async def experiment(payload):
    entry, variant = payload["entrypoint"], payload["variant"]
    if entry == "python":
        return await python_entry(variant)
    if entry == "cli":
        return await cli(variant)
    if entry == "mcp":
        return await mcp(variant)
    if entry == "http":
        return await http(variant)
    if entry == "guardrail":
        return await guardrail(variant)
    if entry == "multi_agent":
        from tests.golden_v02.adapters.runtime import isolation

        return await isolation(
            "separate_worktrees" if variant == "worktrees" else "distinct_inputs"
        )
    raise AdapterGap("entrypoint " + entry)
