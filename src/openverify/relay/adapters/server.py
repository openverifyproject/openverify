"""Optional helper serving an SDK Provider on the published stdio Contract binding."""

import asyncio
import sys
from io import BufferedReader
from typing import cast

from pydantic import JsonValue

from openverify.provider import (
    InitializeRequest,
    Invocation,
    LifecycleValidator,
    Outcome,
    Provider,
    ProviderContractError,
    ProviderEvent,
    parse_invocation,
    parse_provider_object,
    wire_data,
)
from openverify.provider.stdio import FrameDecoder, StdioSessionValidator, encode_frame


async def serve_stdio(provider: Provider) -> None:
    decoder = FrameDecoder()
    session = StdioSessionValidator()
    lifecycle = LifecycleValidator(provider.manifest())
    tasks: dict[str, asyncio.Task[None]] = {}
    request_ids: dict[str, str] = {}

    def send(message: JsonValue) -> None:
        session.provider_message(message)
        sys.stdout.buffer.write(encode_frame(message))
        sys.stdout.buffer.flush()

    async def invoke(request_id: str, invocation: Invocation) -> None:
        terminal = False
        async for item in provider.invoke(invocation):
            if terminal:
                raise ProviderContractError("PROTOCOL_VIOLATION", "Provider emitted after outcome")
            if isinstance(item, ProviderEvent):
                lifecycle.event(wire_data(item))
                send({"jsonrpc": "2.0", "method": "event", "params": wire_data(item)})
            else:
                lifecycle.outcome(wire_data(item))
                terminal = True
                send({"jsonrpc": "2.0", "id": request_id, "result": wire_data(item)})
        if not terminal:
            raise ProviderContractError(
                "PROTOCOL_VIOLATION", "Provider ended without terminal outcome"
            )

    try:
        while chunk := await asyncio.to_thread(cast(BufferedReader, sys.stdin.buffer).read1, 65536):
            for message in decoder.feed(chunk):
                session.runner_message(message)
                id = cast(str, message["id"])
                params = message["params"]
                method = message["method"]
                try:
                    if method == "initialize":
                        initialized = cast(
                            InitializeRequest, parse_provider_object("initialize-request", params)
                        )
                        version = lifecycle.initialize(wire_data(initialized))
                        send(
                            {
                                "jsonrpc": "2.0",
                                "id": id,
                                "result": {
                                    "contract_version": version,
                                    "manifest": wire_data(provider.manifest()),
                                },
                            }
                        )
                    elif method == "invoke":
                        lifecycle.accept(params)
                        invocation = parse_invocation(params)
                        task = asyncio.create_task(invoke(id, invocation))
                        tasks[invocation.invocation_id] = task
                        request_ids[invocation.invocation_id] = id
                    elif method == "cancel":
                        assert isinstance(params, dict)
                        invocation_id = cast(str, params["invocation_id"])
                        lifecycle.cancel(params)
                        await provider.cancel(invocation_id, cast(str | None, params.get("reason")))
                        task = tasks[invocation_id]
                        if not task.done():
                            task.cancel()
                            await asyncio.gather(task, return_exceptions=True)
                            outcome = Outcome(invocation_id=invocation_id, state="CANCELLED")
                            lifecycle.outcome(wire_data(outcome))
                            send(
                                {
                                    "jsonrpc": "2.0",
                                    "id": request_ids[invocation_id],
                                    "result": wire_data(outcome),
                                }
                            )
                        send({"jsonrpc": "2.0", "id": id, "result": None})
                except ProviderContractError as exc:
                    send(
                        {
                            "jsonrpc": "2.0",
                            "id": id,
                            "error": {
                                "code": -32000,
                                "message": exc.message,
                                "data": exc.as_dict(),
                            },
                        }
                    )
            # Propagate failed provider streams; do not leave a caller waiting indefinitely.
            for task in tasks.values():
                if task.done() and not task.cancelled():
                    task.result()
        decoder.finish()
        if tasks:
            await asyncio.gather(*tasks.values())
        session.finish()
    finally:
        for task in tasks.values():
            task.cancel()
        await asyncio.gather(*tasks.values(), return_exceptions=True)
