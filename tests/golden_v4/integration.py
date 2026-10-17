"""Actual subprocess stdio, CLI, MCP tool and ASGI HTTP host boundaries."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from openverify.provider import ProviderContractError
from openverify.provider.stdio import FrameDecoder,encode_frame

from .oracle import model as m
from .runtime import run,catalog_for
from .sut import accepted

ROOT=Path(__file__).resolve().parents[2]


def frame(message):
    body=json.dumps(message,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")+body


async def receive(stream):
    header=await asyncio.wait_for(stream.readuntil(b"\r\n\r\n"),10)
    length=int(header.decode("ascii").split(":",1)[1].strip())
    return json.loads((await asyncio.wait_for(stream.readexactly(length),10)).decode("utf-8"))


async def transport_method(method):
    proc=await asyncio.create_subprocess_exec(sys.executable,str(Path(__file__).with_name("stdio_peer.py")),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,cwd=ROOT)
    async def send(message):
        proc.stdin.write(frame(message));await proc.stdin.drain()
    try:
        await send({"jsonrpc":"2.0","id":"init-1","method":"initialize","params":{"supported_contract_versions":["0.1"],"supported_vcp_versions":["draft"]}})
        init=await receive(proc.stdout)
        assert init["id"]=="init-1" and init["result"]["contract_version"]=="0.1"
        assert init["result"]["manifest"]["provider_id"]==m.PROVIDER
        if method!="initialize":
            inv=m.invocation();inv["input"]={"authored":"雪"}
            if method=="cancel":inv["input"]["wait_for_cancel"]=True
            await send({"jsonrpc":"2.0","id":"invoke-1","method":"invoke","params":inv})
            event=await receive(proc.stdout)
            assert event=={"jsonrpc":"2.0","method":"event","params":{"invocation_id":"v4-attempt","sequence":1,"kind":"progress","payload":{"accepted":True}}}
            if method=="cancel":
                await send({"jsonrpc":"2.0","id":"cancel-1","method":"cancel","params":{"invocation_id":"v4-attempt","reason":"authored"}})
                responses=[await receive(proc.stdout),await receive(proc.stdout)]
                by_id={r["id"]:r for r in responses}
                assert by_id["cancel-1"]["result"] is None
                assert by_id["invoke-1"]["result"]=={"invocation_id":"v4-attempt","state":"CANCELLED"}
            else:
                result=await receive(proc.stdout)
                assert result["id"]=="invoke-1"
                assert result["result"]=={"invocation_id":"v4-attempt","state":"COMPLETED","output":{"echo":{"authored":"雪"}}}
        return {"accepted":True}
    finally:
        proc.stdin.close()
        try:await asyncio.wait_for(proc.wait(),10)
        except TimeoutError:
            proc.kill();await proc.wait();raise
        stderr=(await proc.stderr.read()).decode("utf-8",errors="replace")
        # The binding specifies frames and pending-request effects, not a process
        # exit status after EOF with all requests settled. Keep shutdown evidence.
        if stderr:
            from .reporters import runner
            (runner.ARTIFACTS/f"stdio-{method}-stderr.txt").write_text(stderr,encoding="utf-8")


def framing(s,node):
    name=s["scenario"];message={"jsonrpc":"2.0","id":"authored","result":{"unicode":"雪"}}
    body=frame(message)
    if name=="UNKNOWN_METHOD":
        return asyncio.run(unknown_method())
    decoder=FrameDecoder()
    def check():
        if name=="PARTIAL_READ":
            observed=[]
            for byte in body:observed+=decoder.feed(bytes([byte]))
            assert observed==[message]
        elif name=="COALESCED_READ":assert decoder.feed(body+body)==[message,message]
        elif name=="UTF8_BYTES":
            assert encode_frame(message)==frame(message) or json.loads(encode_frame(message).split(b"\r\n\r\n")[1])==message
            assert decoder.feed(body)==[message]
        elif name=="BAD_HEADER":decoder.feed(body.replace(b"Content-Length",b"Other-Length"))
        elif name=="TRUNCATED":decoder.feed(body[:-1])
        decoder.finish()
    return accepted(check,node)


async def unknown_method():
    proc=await asyncio.create_subprocess_exec(sys.executable,str(Path(__file__).with_name("stdio_peer.py")),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,cwd=ROOT)
    try:
        proc.stdin.write(frame({"jsonrpc":"2.0","id":"init-unknown","method":"initialize","params":{"supported_contract_versions":["0.1"],"supported_vcp_versions":["draft"]}}));await proc.stdin.drain()
        initialized=await receive(proc.stdout)
        assert initialized["result"]["contract_version"]=="0.1"
        proc.stdin.write(frame({"jsonrpc":"2.0","id":"unknown-1","method":"unsupported","params":{}}));await proc.stdin.drain()
        response=await receive(proc.stdout)
        assert response["error"]["code"]==-32601
        return {"accepted":True}
    finally:
        proc.stdin.close()
        try:await asyncio.wait_for(proc.wait(),10)
        except TimeoutError:proc.kill();await proc.wait();raise


async def host(surface,node):
    from openverify import Relay
    from openverify.relay.entrypoints.service import GraphService
    from openverify.relay.templates import text_graph
    if surface=="PYTHON":
        relay=Relay(catalog=catalog_for({"n":{}}));record=(await run(relay,m.definition([m.node()]),node)).record
        assert relay.store.get(record.run_id)==record
        return {"accepted":True}
    service=GraphService(graphs={"text":text_graph()})
    original_run=service.relay.run
    async def measured_run(*args,**kw):
        node.v4_relay_calls=getattr(node,"v4_relay_calls",0)+1;start=time.monotonic()
        try:return await original_run(*args,**kw)
        finally:node.v4_relay_seconds=getattr(node,"v4_relay_seconds",0)+time.monotonic()-start
    service.relay.run=measured_run
    if surface.startswith("MCP"):
        from openverify.relay.entrypoints.mcp import create_server
        server=create_server(service)
        tools=await server.list_tools()
        assert {t.name for t in tools}=={"list_graphs","describe_graph","run_graph","inspect_result"}
        if surface=="MCP_LIST":
            result=await server.call_tool("list_graphs",{})
            assert "text" in str(result)
        else:
            result=await server.call_tool("run_graph",{"name":"text","inputs":{"text":"Migration Rollback"}})
            assert "run_id" in str(result) and "PASS" in str(result)
        return {"accepted":True}
    import httpx
    from openverify.relay.entrypoints.http import create_app
    token="v4-secret" if surface=="HTTP_AUTH" else None
    app=create_app(service,token=token,max_body_bytes=16 if surface=="HTTP_BODY_LIMIT" else 1024*1024)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://v4.local") as client:
        if surface=="HTTP_HEALTH":
            r=await client.get("/health");assert r.status_code==200 and r.json()=={"status":"ok","protocol":"draft","runtime":"relay-0.1"}
        else:
            payload={"graph":"text","inputs":{"text":"Migration Rollback" if surface!="HTTP_FAIL" else "TBD"}}
            if surface=="HTTP_BAD_GRAPH":payload["graph"]="not-authorized"
            r=await client.post("/verify",json=payload)
            if surface=="HTTP_AUTH":assert r.status_code==401
            elif surface=="HTTP_BODY_LIMIT":assert r.status_code==413
            elif surface=="HTTP_BAD_GRAPH":assert r.status_code==400
            else:
                assert r.status_code==200
                record=r.json();assert record["run_inputs"]==payload["inputs"]
                assert record["final_results"]["all"]["verdict"]==("FAIL" if surface=="HTTP_FAIL" else "PASS")
    return {"accepted":True}


def cli(surface,node):
    import tempfile
    from .reporters import runner
    folder=runner.ARTIFACTS/"cli"/surface;folder.mkdir(parents=True,exist_ok=True)
    values={"text":"Migration Rollback" if surface=="CLI_PASS" else "TBD"}
    file=folder/"inputs.json";file.write_text(json.dumps(values),encoding="utf-8")
    env={**os.environ,"PYTHONPATH":str(ROOT/"src")}
    p=subprocess.run([sys.executable,"-m","openverify.relay.entrypoints.cli","run","text","--inputs",str(file),"--json"],cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert p.returncode==(0 if surface=="CLI_PASS" else 1),(p.returncode,p.stdout,p.stderr)
    record=json.loads(p.stdout);assert record["run_inputs"]==values
    node.v4_relay_calls=getattr(node,"v4_relay_calls",0)+1
    assert record["final_results"]["all"]["verdict"]==("PASS" if surface=="CLI_PASS" else "FAIL")
    return {"accepted":True}


def execute_integration(case,node):
    action=case["action"];s=case["stimulus"]
    if action=="framing":return framing(s,node)
    if action=="transport_method":return asyncio.run(transport_method(s["method"]))
    if s["surface"].startswith("CLI"):return cli(s["surface"],node)
    return asyncio.run(host(s["surface"],node))
