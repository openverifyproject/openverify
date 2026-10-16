"""Stable errors at Relay's host boundary."""

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.relay.error_codes import RelayErrorCode


class RelayError(ProtocolError):
    """Configuration, availability, or host integration failure."""

    def __init__(self, code: str, message: str, path: str = "", details: JsonValue = None):
        try:
            typed: str = RelayErrorCode(str.__str__(code))
        except ValueError:
            typed = code
        super().__init__(typed, message, path, details)
