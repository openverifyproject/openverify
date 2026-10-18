"""Independent Provider Contract 0.1 simulator; Python standard library only.

Usage: python stdio_provider.py --spec /absolute/provider.json
The host file supplies a manifest and deterministic behaviors keyed by capability.
This is a disposable conformance peer, never a general executable launcher.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from pathlib import Path

LOCK = threading.Lock()


def read_frame():
    header = sys.stdin.buffer.readline()
    if not header:
        return None
    if not header.lower().startswith(b"content-length: ") or not header.endswith(b"\r\n"):
        raise ValueError("bad Content-Length header")
    length = int(header[16:-2])
    if length <= 0 or length > 16 * 1024 * 1024 or sys.stdin.buffer.read(2) != b"\r\n":
        raise ValueError("bad frame")
    raw = sys.stdin.buffer.read(length)
    if len(raw) != length:
        raise EOFError("truncated frame")
    return json.loads(raw)


def send(message):
    raw = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    with LOCK:
        sys.stdout.buffer.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("ascii") + raw)
        sys.stdout.buffer.flush()


def rpc_error(identity, code, message="deliberate conformance rejection", number=-32000):
    send({"jsonrpc":"2.0","id":identity,"error":{"code":number,"message":message,"data":{"code":code,"message":message}}})


def serve(spec):
    manifest, behaviors = spec["manifest"], spec.get("behaviors", {})
    initialized = False
    attempts = {}
    rpc_ids = set()
    def execute(rpc_id, invocation, behavior, cancelled):
        identity = invocation["invocation_id"]
        mode = behavior.get("mode", "valid")
        if mode == "crash":
            os._exit(17)
        if mode == "malformed":
            with LOCK:
                sys.stdout.buffer.write(b"Content-Length: 4\r\n\r\nnope")
                sys.stdout.buffer.flush()
            return
        if mode == "missing_terminal":
            return
        if mode == "stderr":
            sys.stderr.write("conformance diagnostic\n"); sys.stderr.flush()
        sequence = 0
        for event in behavior.get("events", []):
            sequence += 1
            send({"jsonrpc":"2.0","method":"event","params":{"invocation_id":identity,"sequence":sequence,**event}})
        if behavior.get("entered_path"):
            Path(behavior["entered_path"]).write_text(identity, encoding="utf-8")
        if mode in ("delayed", "cancelling", "ignores_cancel"):
            if mode == "ignores_cancel":
                threading.Event().wait()
            else:
                cancelled.wait(behavior.get("delay_seconds", 30))
        if cancelled.is_set() and mode != "ignores_cancel":
            outcome = {"invocation_id":identity,"state":"CANCELLED"}
        elif mode == "failing":
            outcome = {"invocation_id":identity,"state":"ERROR","error":{"code":"com.example.golden.failed","message":"specified failure"}}
        else:
            outcome = {"invocation_id":identity,"state":"COMPLETED","output":behavior.get("outputs", invocation["input"])}
        if "usage" in behavior:
            outcome["resource_usage"] = behavior["usage"]
        if mode == "wrong_correlation":
            outcome["invocation_id"] = "other-attempt"
        send({"jsonrpc":"2.0","id":rpc_id,"result":outcome})
        attempts[identity]["terminal"] = True
        if mode == "duplicate":
            send({"jsonrpc":"2.0","id":rpc_id,"result":outcome})
        if mode == "event_after_terminal":
            send({"jsonrpc":"2.0","method":"event","params":{"invocation_id":identity,"sequence":sequence+1,"kind":"progress","payload":None}})
    while True:
        message = read_frame()
        if message is None:
            return
        identity = message.get("id")
        if not isinstance(identity,str) or not identity or identity in rpc_ids:
            rpc_error(identity,"PROTOCOL_VIOLATION"); continue
        rpc_ids.add(identity)
        method, params = message.get("method"), message.get("params", {})
        if method == "initialize":
            if initialized:
                rpc_error(identity,"PROTOCOL_VIOLATION"); continue
            if "0.1" not in params.get("supported_contract_versions",[]):
                rpc_error(identity,"CONTRACT_VERSION_UNSUPPORTED"); return
            initialized = True
            send({"jsonrpc":"2.0","id":identity,"result":{"contract_version":"0.1","manifest":manifest}})
        elif not initialized:
            rpc_error(identity,"PROTOCOL_VIOLATION")
        elif method == "cancel":
            aid=params.get("invocation_id")
            if aid not in attempts:
                rpc_error(identity,"PROTOCOL_VIOLATION"); continue
            attempt=attempts[aid]
            if not attempt["terminal"] and not attempt["cancellation"]:
                rpc_error(identity,"PROTOCOL_VIOLATION"); continue
            attempt["cancel"].set()
            send({"jsonrpc":"2.0","id":identity,"result":None})
        elif method == "invoke":
            aid=params.get("invocation_id")
            if not isinstance(aid,str) or not aid or aid in attempts:
                rpc_error(identity,"PROTOCOL_VIOLATION"); continue
            if params.get("contract_version") != "0.1":
                rpc_error(identity,"CONTRACT_VERSION_UNSUPPORTED"); continue
            matches=[c for c in manifest["capabilities"] if c["capability_id"] == params.get("capability_id")]
            if not matches:
                rpc_error(identity,"CAPABILITY_UNAVAILABLE"); continue
            matches=[c for c in matches if c["capability_version"] == params.get("capability_version")]
            if not matches:
                rpc_error(identity,"CAPABILITY_VERSION_UNSUPPORTED"); continue
            cap=matches[0]
            # This simulator's advertised schemas are deliberately unrestricted.
            # Schema-invalid response behaviors are peer faults, not an oracle.
            if "deadline" in params or "resource_budget" in params:
                rpc_error(identity,"INVALID_INVOCATION"); continue
            cancel=threading.Event()
            attempts[aid]={"cancel":cancel,"terminal":False,"cancellation":cap["lifecycle_features"]["cancellation"]}
            b=behaviors.get(params["capability_id"],{})
            threading.Thread(target=execute,args=(identity,params,b,cancel),daemon=True).start()
        else:
            rpc_error(identity,"PROTOCOL_VIOLATION",number=-32601)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--spec",required=True)
    options=parser.parse_args()
    serve(json.loads(Path(options.spec).read_text(encoding="utf-8")))
