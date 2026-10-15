"""Stable errors at Relay's host boundary."""

from openverify.errors import ProtocolError


class RelayError(ProtocolError):
    """Configuration, availability, or host integration failure."""
