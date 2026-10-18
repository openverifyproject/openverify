"""Public, optional Python SDK for OpenVerify Provider Contract DRAFT 0.1."""

from collections.abc import AsyncIterator
from typing import Protocol

from .lifecycle import LifecycleValidator, negotiate_contract_version, validate_lifecycle
from .model import (
    CancelRequest,
    Capability,
    InitializeRequest,
    InitializeResult,
    Invocation,
    LifecycleFeatures,
    Outcome,
    ProviderError,
    ProviderEvent,
    ProviderManifest,
)
from .validation import (
    ProviderContractError,
    load_provider_schema,
    parse_cancel_request,
    parse_invocation,
    parse_outcome,
    parse_provider_event,
    parse_provider_manifest,
    parse_provider_object,
    serialize,
    validate_invocation,
    validate_outcome,
    validate_provider_event,
    validate_provider_manifest,
    wire_data,
)


class Provider(Protocol):
    """In-process convenience only; implementations still obey public wire semantics.

    invoke yields zero or more events followed by exactly one Outcome. Its caller
    supplies initialization, validates boundaries, and processes cancel concurrently.
    Exceptions before acceptance reject the call; after acceptance yield ERROR.
    """

    def manifest(self) -> ProviderManifest: ...

    def invoke(self, invocation: Invocation) -> AsyncIterator[ProviderEvent | Outcome]: ...

    async def cancel(self, invocation_id: str, reason: str | None = None) -> None: ...


__all__ = [
    "CancelRequest",
    "Capability",
    "InitializeRequest",
    "InitializeResult",
    "Invocation",
    "LifecycleFeatures",
    "LifecycleValidator",
    "Outcome",
    "Provider",
    "ProviderContractError",
    "ProviderError",
    "ProviderEvent",
    "ProviderManifest",
    "load_provider_schema",
    "negotiate_contract_version",
    "parse_cancel_request",
    "parse_invocation",
    "parse_outcome",
    "parse_provider_event",
    "parse_provider_manifest",
    "parse_provider_object",
    "serialize",
    "validate_invocation",
    "validate_lifecycle",
    "validate_outcome",
    "validate_provider_event",
    "validate_provider_manifest",
    "wire_data",
]
