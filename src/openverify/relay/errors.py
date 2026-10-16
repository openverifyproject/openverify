"""Stable errors at Relay's host boundary."""

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.relay.error_codes import RelayErrorCode


class RelayError(ProtocolError):
    """Configuration, availability, or host integration failure."""

    def __init__(self, code: str, message: str, path: str = "", details: JsonValue = None):
        super().__init__(code, message, path, details)
        try:
            self.code = RelayErrorCode(str.__str__(code))
        except ValueError:
            pass
