"""One initialized, isolated stdio session per invocation, with SDK RPC validation."""

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from openverify.provider import (
    Outcome,
    ProviderContractError,
    parse_outcome,
    parse_provider_event,
    wire_data,
)
from openverify.provider.stdio import FrameDecoder, StdioSessionValidator, encode_frame
from openverify.relay.adapters.local import InvalidProviderOutput, ObservedTransportFailure
from openverify.relay.adapters.process import read_bounded, spawn, terminate
from openverify.relay.ports import EventSink, InvocationRequest
from openverify.serialization import json_equal


@dataclass(frozen=True)
class StdioTransport:
    argv: tuple[str, ...]
    cwd: str
    env: dict[str, str] | None = None
    max_message_bytes: int = 16 * 1024 * 1024
    max_stderr_bytes: int = 1024 * 1024

    async def invoke(self, request: InvocationRequest, emit: EventSink) -> Outcome:
        process = await spawn(self.argv, self.cwd, self.env)
        assert process.stdin and process.stdout and process.stderr
        errors = asyncio.create_task(read_bounded(process.stderr, self.max_stderr_bytes))
        decoder = FrameDecoder(max_body_bytes=self.max_message_bytes)
        session = StdioSessionValidator()
        queued: deque[dict[str, JsonValue]] = deque()
        observed_outcome: Outcome | None = None

        async def send(id: str, method: str, params: JsonValue) -> None:
            message: JsonValue = {"jsonrpc": "2.0", "id": id, "method": method, "params": params}
            session.runner_message(message)
            assert process.stdin
            process.stdin.write(encode_frame(message))
            await process.stdin.drain()

        async def receive() -> dict[str, JsonValue]:
            assert process.stdout
            while not queued:
                read = asyncio.create_task(process.stdout.read(65536))
                try:
                    done, _ = await asyncio.wait(
                        [read, errors], return_when=asyncio.FIRST_COMPLETED
                    )
                    if errors in done and errors.exception() is not None:
                        raise cast(Exception, errors.exception())
                    chunk = await read
                finally:
                    if not read.done():
                        read.cancel()
                    await asyncio.gather(read, return_exceptions=True)
                if not chunk:
                    decoder.finish()
                    raise ProviderContractError(
                        "PROTOCOL_VIOLATION", "Provider disconnected before outcome"
                    )
                queued.extend(decoder.feed(chunk))
            message = queued.popleft()
            try:
                session.provider_message(message)
            except ProviderContractError as exc:
                # Preserve valid raw successful output and usage on schema rejection.
                if exc.code == "INVALID_PROVIDER_OUTPUT" and message.get("id") == "invoke":
                    raw = parse_outcome(message.get("result"))
                    if (
                        raw.state == "COMPLETED"
                        and raw.invocation_id == request.invocation.invocation_id
                    ):
                        raise InvalidProviderOutput(raw, exc.message) from exc
                raise
            if "error" in message:
                error = cast(dict[str, JsonValue], message["error"])
                data = cast(dict[str, JsonValue], error["data"])
                raise ProviderContractError(cast(str, data["code"]), cast(str, data["message"]))
            return message

        try:
            await send(
                "initialize",
                "initialize",
                {"supported_contract_versions": ["0.1"], "supported_vcp_versions": ["draft"]},
            )
            initialized = await receive()
            result = cast(dict[str, JsonValue], initialized["result"])
            if not json_equal(result["manifest"], wire_data(request.manifest)):
                raise ProviderContractError(
                    "PROTOCOL_VIOLATION",
                    "Initialized manifest differs from trusted catalog snapshot",
                )
            await send("invoke", "invoke", wire_data(request.invocation))
            while True:
                message = await receive()
                if message.get("method") == "event":
                    emit(parse_provider_event(message["params"]))
                    continue
                outcome = parse_outcome(message["result"])
                observed_outcome = outcome
                # Close stdin and require a bounded orderly EOF; catch duplicate/trailing frames.
                process.stdin.close()
                while queued:
                    session.provider_message(queued.popleft())
                async with asyncio.timeout(0.5):
                    while chunk := await process.stdout.read(65536):
                        for extra in decoder.feed(chunk):
                            session.provider_message(extra)
                    decoder.finish()
                    session.finish()
                    await process.wait()
                await errors
                return outcome
        except asyncio.CancelledError:
            # Cooperatively request cancellation, then enforce a bounded physical shutdown.
            try:
                await send(
                    "cancel",
                    "cancel",
                    {
                        "invocation_id": request.invocation.invocation_id,
                        "reason": "Runner cancellation",
                    },
                )
                async with asyncio.timeout(0.2):
                    while True:
                        message = await receive()
                        if message.get("method") == "event":
                            emit(parse_provider_event(message["params"]))
                        elif message.get("id") == "invoke":
                            break
            except Exception:
                pass
            raise
        except Exception as exc:
            if observed_outcome is not None:
                raise ObservedTransportFailure(
                    observed_outcome,
                    exc.code if isinstance(exc, ProviderContractError) else "TRANSPORT_ERROR",
                    str(exc),
                ) from exc
            raise
        finally:
            await terminate(process)
            errors.cancel()
            await asyncio.gather(errors, return_exceptions=True)
