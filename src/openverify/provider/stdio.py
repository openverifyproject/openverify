"""Baseline JSON-RPC frame codec and session validation; no process execution."""

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.serialization import decode

from .lifecycle import LifecycleValidator, negotiate_contract_version
from .model import InitializeRequest, InitializeResult
from .validation import (
    ProviderContractError,
    fail,
    parse_provider_object,
    wire_data,
)


def encode_frame(message: JsonValue) -> bytes:
    if not isinstance(message, dict):
        fail("PROTOCOL_VIOLATION", "Binding frames contain one JSON object")
    try:
        decode(message)
        body = json.dumps(
            message, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except (ProtocolError, ValueError, UnicodeError) as exc:
        raise ProviderContractError("PROTOCOL_VIOLATION", "Invalid frame JSON") from exc
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body


class FrameDecoder:
    """Incremental byte framing, with documented local size limits.

    A framing failure poisons the decoder; a complete invalid JSON body has an
    unambiguous boundary and raises PROTOCOL_VIOLATION (RPC servers map to -32700).
    """

    def __init__(self, *, max_body_bytes: int = 16 * 1024 * 1024, max_header_bytes: int = 8192):
        if max_body_bytes < 1 or max_header_bytes < 1:
            raise ValueError("Frame limits must be positive")
        self._body_limit = max_body_bytes
        self._header_limit = max_header_bytes
        self._buffer = bytearray()
        self._length: int | None = None
        self._failed = False

    def feed(self, chunk: bytes) -> list[dict[str, JsonValue]]:
        if self._failed:
            fail("PROTOCOL_VIOLATION", "Decoder closed after framing failure")
        self._buffer.extend(chunk)
        messages: list[dict[str, JsonValue]] = []
        try:
            while True:
                if self._length is None:
                    end = self._buffer.find(b"\r\n\r\n")
                    if end < 0:
                        if len(self._buffer) > self._header_limit:
                            fail("PROTOCOL_VIOLATION", "Header size limit exceeded")
                        break
                    if end + 4 > self._header_limit:
                        fail("PROTOCOL_VIOLATION", "Header size limit exceeded")
                    header = bytes(self._buffer[:end])
                    match = re.fullmatch(rb"Content-Length: ([0-9]+)", header, re.IGNORECASE)
                    if match is None:
                        fail("PROTOCOL_VIOLATION", "Invalid Content-Length framing")
                    assert match is not None
                    digits = match[1].lstrip(b"0") or b"0"
                    if len(digits) > len(str(self._body_limit)):
                        fail("PROTOCOL_VIOLATION", "Body size limit exceeded")
                    self._length = int(digits)
                    if not 1 <= self._length <= self._body_limit:
                        fail("PROTOCOL_VIOLATION", "Invalid body length or size limit exceeded")
                    del self._buffer[: end + 4]
                if len(self._buffer) < self._length:
                    break
                body = bytes(self._buffer[: self._length])
                del self._buffer[: self._length]
                self._length = None
                raw = decode(body)
                if not isinstance(raw, dict):
                    fail("PROTOCOL_VIOLATION", "Binding does not support batches/nonobjects")
                assert isinstance(raw, dict)
                messages.append(raw)
        except (ProtocolError, ProviderContractError) as exc:
            self._failed = True
            if isinstance(exc, ProviderContractError):
                raise
            raise ProviderContractError("PROTOCOL_VIOLATION", "Invalid UTF-8 JSON frame") from exc
        return messages

    def finish(self) -> None:
        if self._failed or self._buffer or self._length is not None:
            fail("PROTOCOL_VIOLATION", "Truncated or invalid stdio stream")


@dataclass
class _Pending:
    method: str
    params: dict[str, JsonValue]
    rejection: str | None = None


class StdioSessionValidator:
    """Validate an observed bidirectional session, including both correlation IDs.

    now is a provider-clock observation for deadline invocations, never a runner
    clock claim. Records provisional invocations until a response confirms
    acceptance/rejection; no acceptance message is added to the binding.
    """

    def __init__(self) -> None:
        self._lifecycle: LifecycleValidator | None = None
        self._initialize: InitializeRequest | None = None
        self._initialization_attempted = False
        self._pending: dict[str, _Pending] = {}
        self._used_ids: set[str] = set()
        self._closed = False

    def runner_message(self, data: JsonValue, *, now: str | None = None) -> None:
        if self._closed:
            fail("PROTOCOL_VIOLATION", "Session closed")
        if (
            not isinstance(data, dict)
            or set(data) != {"jsonrpc", "id", "method", "params"}
            or data.get("jsonrpc") != "2.0"
        ):
            fail("PROTOCOL_VIOLATION", "Invalid runner RPC envelope")
        assert isinstance(data, dict)
        identity, method, params = data["id"], data["method"], data["params"]
        if (
            not isinstance(identity, str)
            or not identity
            or identity in self._used_ids
            or not isinstance(params, dict)
            or not isinstance(method, str)
            or not method
        ):
            fail("PROTOCOL_VIOLATION", "Invalid/reused request ID, params, or method")
        assert isinstance(identity, str) and isinstance(method, str) and isinstance(params, dict)
        pending = _Pending(method, deepcopy(params))
        if method == "initialize":
            if self._initialization_attempted:
                fail("PROTOCOL_VIOLATION", "Repeated initialization")
            self._initialization_attempted = True
            self._initialize = cast(
                InitializeRequest, parse_provider_object("initialize-request", params)
            )
        elif method in ("invoke", "cancel"):
            if self._lifecycle is None:
                fail("PROTOCOL_VIOLATION", "Request before initialization success")
            assert self._lifecycle is not None
            try:
                if method == "invoke":
                    self._lifecycle.accept(params, now=now)
                elif method == "cancel":
                    self._lifecycle.cancel(params)
            except ProviderContractError as exc:
                pending.rejection = exc.code
        self._used_ids.add(identity)
        self._pending[identity] = pending

    def provider_message(self, data: JsonValue, *, now: str | None = None) -> None:
        if self._closed or not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
            fail("PROTOCOL_VIOLATION", "Invalid provider RPC envelope/session")
        assert isinstance(data, dict)
        if "method" in data:
            if (
                set(data) != {"jsonrpc", "method", "params"}
                or data["method"] != "event"
                or self._lifecycle is None
            ):
                fail("PROTOCOL_VIOLATION", "Invalid provider notification")
            assert self._lifecycle is not None
            self._lifecycle.event(data["params"])
            return
        identity = data.get("id")
        if (
            not isinstance(identity, str)
            or identity not in self._pending
            or (set(data) not in ({"jsonrpc", "id", "result"}, {"jsonrpc", "id", "error"}))
        ):
            fail("PROTOCOL_VIOLATION", "Unsolicited/malformed RPC response")
        assert isinstance(identity, str)
        pending = self._pending[identity]
        if pending.method not in ("initialize", "invoke", "cancel"):
            error = data.get("error")
            if (
                set(data) != {"jsonrpc", "id", "error"}
                or not isinstance(error, dict)
                or not {"code", "message"} <= set(error) <= {"code", "message", "data"}
                or type(error["code"]) is not int
                or error["code"] != -32601
                or not isinstance(error["message"], str)
            ):
                fail("PROTOCOL_VIOLATION", "Unknown method requires method-not-found response")
            del self._pending[identity]
            return
        if "error" in data:
            error = data["error"]
            if (
                not isinstance(error, dict)
                or set(error) != {"code", "message", "data"}
                or type(error["code"]) not in (int, float)
                or error["code"] not in (-32000, -32602)
            ):
                fail("PROTOCOL_VIOLATION", "Malformed contract rejection envelope")
            assert isinstance(error, dict)
            parsed = parse_provider_object("provider-error", error["data"])
            code = cast(str, wire_data(parsed)["code"])
            if (
                not isinstance(error["message"], str)
                or not error["message"]
                or (pending.rejection is not None and code != pending.rejection)
            ):
                fail("PROTOCOL_VIOLATION", "Rejection does not match contract error")
            if pending.method == "initialize":
                self._closed = True
            elif pending.method == "invoke" and pending.rejection is None:
                assert self._lifecycle is not None
                self._lifecycle.reject(pending.params)
            elif pending.method == "cancel" and pending.rejection is None:
                fail("PROTOCOL_VIOLATION", "Supported cancellation must be acknowledged")
        else:
            if pending.rejection is not None:
                fail("PROTOCOL_VIOLATION", "Provider accepted incompatible request")
            result = data["result"]
            if pending.method == "initialize":
                initialized = cast(
                    InitializeResult, parse_provider_object("initialize-result", result)
                )
                assert self._initialize is not None
                selected = negotiate_contract_version(
                    self._initialize.supported_contract_versions,
                    initialized.manifest.supported_contract_versions,
                )
                if selected != initialized.contract_version:
                    fail("CONTRACT_VERSION_UNSUPPORTED", "Wrong initialized version")
                lifecycle = LifecycleValidator(initialized.manifest)
                lifecycle.initialize(wire_data(self._initialize))
                self._lifecycle = lifecycle
            elif pending.method == "invoke":
                if not isinstance(result, dict) or result.get(
                    "invocation_id"
                ) != pending.params.get("invocation_id"):
                    fail("PROTOCOL_VIOLATION", "RPC/Invocation correlation mismatch")
                assert self._lifecycle is not None
                self._lifecycle.outcome(result, now=now)
            elif result is not None:
                fail("PROTOCOL_VIOLATION", "Cancel acknowledgement must be null")
        del self._pending[identity]

    def finish(self) -> None:
        if self._pending:
            fail("PROTOCOL_VIOLATION", "Pending RPC responses at session finish")
        if self._lifecycle is not None:
            self._lifecycle.finish()
        elif not self._closed:
            fail("PROTOCOL_VIOLATION", "Session was never initialized")
