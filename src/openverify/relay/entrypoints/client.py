"""Relay Client v1 newline-delimited JSON stdio host."""
# pyright: basic

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import uuid4

from openverify.relay import Relay
from openverify.relay.adapters.sqlite import SQLiteStore
from openverify.relay.entrypoints.service import GraphService

MAX_LINE = 1024 * 1024
FIELDS = dict(
    {
        "register": ({"definition"}, set()),
        "replace": ({"graph_id", "definition"}, set()),
        "get": ({"graph_id"}, {"revision"}),
        "run": ({"graph_id", "inputs"}, {"revision", "request_id"}),
        "lookup": ({"request_id"}, set()),
        "cancel": ({"request_id"}, set()),
    }
)


def validate_request(request: object) -> dict:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    if request.get("client_version") != "1":
        raise ValueError("client_version 1 is required")
    if not isinstance(request.get("id"), str) or not request["id"]:
        raise ValueError("id must be a nonempty string")
    operation = request.get("op")
    if not isinstance(operation, str) or operation not in FIELDS:
        raise ValueError("unsupported operation")
    required, optional = FIELDS[operation]
    keys = set(request)
    if not required <= keys or keys - required - optional - {"client_version", "id", "op"}:
        raise ValueError("incorrect request fields")
    for name in ("graph_id", "request_id"):
        if name in request and (not isinstance(request[name], str) or not request[name]):
            raise ValueError(f"{name} must be a nonempty string")
    if "revision" in request and (type(request["revision"]) is not int or request["revision"] < 1):
        raise ValueError("revision must be a positive integer")
    if "definition" in request and not isinstance(request["definition"], dict):
        raise ValueError("definition must be an object")
    if "inputs" in request and not isinstance(request["inputs"], dict):
        raise ValueError("inputs must be an object")
    return request


async def serve(service: GraphService) -> None:
    output = asyncio.Lock()
    pending: set[asyncio.Task] = set()

    async def send(payload: dict) -> None:
        async with output:
            sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    async def dispatch(request: dict) -> None:
        correlation = request.get("id")
        try:
            if not isinstance(correlation, str) or not correlation:
                raise ValueError("id must be a nonempty string")
            operation = request.get("op")
            if operation == "register":
                result = service.register(request["definition"])
            elif operation == "replace":
                result = service.replace(request["graph_id"], request["definition"])
            elif operation == "get":
                result = service.retrieve(request["graph_id"], request.get("revision"))
            elif operation == "run":
                result = await service.execute(
                    request["graph_id"],
                    request["inputs"],
                    request.get("revision"),
                    request.get("request_id") or str(uuid4()),
                )
            elif operation == "lookup":
                result = service.lookup(request["request_id"])
            elif operation == "cancel":
                result = service.cancel(request["request_id"])
            else:
                raise ValueError("unsupported operation")
            await send({"id": correlation, "ok": True, "result": result})
        except (KeyError, TypeError, ValueError) as exc:
            await send(
                {
                    "id": correlation,
                    "ok": False,
                    "error": {"code": "INVALID_REQUEST", "message": str(exc)},
                }
            )
        except Exception as exc:
            await send(
                {
                    "id": correlation,
                    "ok": False,
                    "error": {"code": getattr(exc, "code", "EXECUTION_ERROR"), "message": str(exc)},
                }
            )

    while raw := await asyncio.to_thread(sys.stdin.buffer.readline, MAX_LINE + 1):
        if len(raw) > MAX_LINE or not raw.endswith(b"\n"):
            await send(
                {
                    "id": None,
                    "ok": False,
                    "error": {"code": "INVALID_REQUEST", "message": "line exceeds limit"},
                }
            )
            if len(raw) > MAX_LINE:
                break
            continue
        candidate = None
        try:
            candidate = json.loads(raw)
            request = validate_request(candidate)
        except (ValueError, UnicodeError) as exc:
            await send(
                {
                    "id": candidate.get("id")
                    if isinstance(candidate, dict) and isinstance(candidate.get("id"), str)
                    else None,
                    "ok": False,
                    "error": {"code": "INVALID_REQUEST", "message": str(exc)},
                }
            )
            continue
        task = asyncio.create_task(dispatch(request))
        pending.add(task)
        task.add_done_callback(pending.discard)
    if pending:
        await asyncio.gather(*pending)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    args = parser.parse_args()
    store = SQLiteStore(args.database)
    asyncio.run(serve(GraphService(Relay(store=store), registry=store)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
