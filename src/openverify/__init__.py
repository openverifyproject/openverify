"""Draft domain-neutral verification protocol implementation."""

__version__ = "0.1.0"

from openverify.errors import ProtocolError
from openverify.fingerprint import fingerprint
from openverify.inspection import flattened_status, inspect_definition
from openverify.serialization import serialize
from openverify.validation import (
    load_schema,
    parse_definition,
    parse_result,
    parse_run_record,
    validate_definition,
    validate_result,
)

__all__ = [
    "ProtocolError",
    "fingerprint",
    "flattened_status",
    "inspect_definition",
    "load_schema",
    "parse_definition",
    "parse_result",
    "parse_run_record",
    "serialize",
    "validate_definition",
    "validate_result",
]
