"""Execute portable fixtures; the fixture format is documented independently."""

import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from .lifecycle import validate_lifecycle
from .stdio import FrameDecoder, StdioSessionValidator
from .validation import ProviderContractError, fail, parse_provider_object


def check_case(object_type: str, data: JsonValue) -> None:
    if object_type == "lifecycle":
        validate_lifecycle(data)
    elif object_type == "stdio-session":
        session = StdioSessionValidator()
        if not isinstance(data, list):
            fail("PROTOCOL_VIOLATION", "Expected session steps")
        assert isinstance(data, list)
        for step in data:
            if (
                not isinstance(step, dict)
                or set(step) - {"direction", "message", "now"}
                or "message" not in step
            ):
                fail("PROTOCOL_VIOLATION", "Malformed session step")
            assert isinstance(step, dict)
            now = step.get("now")
            if now is not None and not isinstance(now, str):
                fail("PROTOCOL_VIOLATION", "Invalid provider-clock observation")
            if step.get("direction") == "runner":
                session.runner_message(step["message"], now=cast(str | None, now))
            elif step.get("direction") == "provider":
                session.provider_message(step["message"], now=cast(str | None, now))
            else:
                fail("PROTOCOL_VIOLATION", "Invalid message direction")
        session.finish()
    elif object_type == "framing":
        if not isinstance(data, dict) or not isinstance(data.get("chunks"), list):
            fail("PROTOCOL_VIOLATION", "Invalid framing fixture")
        assert isinstance(data, dict)
        decoder = FrameDecoder()
        count = sum(len(decoder.feed(bytes.fromhex(c))) for c in cast(list[str], data["chunks"]))
        decoder.finish()
        if count != data.get("message_count"):
            fail("PROTOCOL_VIOLATION", "Wrong frame count")
    else:
        parse_provider_object(object_type, data)


def check_manifest(directory: Path) -> list[str]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in manifest["cases"]:
        try:
            check_case(
                case["object_type"],
                json.loads((directory / case["input"]).read_text(encoding="utf-8")),
            )
            code = None
        except ProviderContractError as exc:
            code = exc.code
        if code != case.get("error_code"):
            failures.append(case["id"])
    return failures
