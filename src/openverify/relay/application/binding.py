"""Bind through the injected port, then independently check its choice."""

from collections.abc import Sequence
from copy import deepcopy
from typing import cast

from openverify.errors import ProtocolError
from openverify.model import OperationRequirement, ProviderBinding
from openverify.provider import (
    ProviderContractError,
    ProviderManifest,
    parse_provider_manifest,
    wire_data,
)
from openverify.relay.error_codes import RelayErrorCode
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider, ProviderBinder
from openverify.relay.ports.binding import compatible, identity


def validate_choice(value: object) -> AvailableProvider:
    if (
        not isinstance(value, AvailableProvider)
        or not isinstance(cast(object, value.manifest), ProviderManifest)
        or not callable(getattr(value.transport, "invoke", None))
    ):
        raise RelayError("PROVIDER_BINDING_MISMATCH", "Binder returned an invalid provider value")
    return AvailableProvider(parse_provider_manifest(wire_data(value.manifest)), value.transport)


def bind(
    requirement: OperationRequirement,
    providers: Sequence[AvailableProvider],
    binder: ProviderBinder,
    explicit: ProviderBinding | None = None,
) -> AvailableProvider:
    try:
        candidates = tuple(AvailableProvider(deepcopy(p.manifest), p.transport) for p in providers)
        chosen = validate_choice(binder.bind(requirement, candidates, explicit))
        if not compatible(requirement, chosen) or (
            explicit is not None and identity(chosen, requirement) != explicit
        ):
            raise RelayError(
                "PROVIDER_BINDING_MISMATCH", "Binder returned an incompatible provider"
            )
        if not any(
            chosen.transport is p.transport and chosen.manifest == p.manifest for p in providers
        ):
            raise RelayError("PROVIDER_UNTRUSTED", "Binder returned an unregistered provider")
    except (ProtocolError, ProviderContractError):
        raise
    except Exception as exc:
        raise RelayError(
            RelayErrorCode.BINDER_FAILURE,
            "Provider binder failed",
            details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
        ) from exc
    return chosen
