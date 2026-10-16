"""Bind through the injected port, then independently check its choice."""

from collections.abc import Sequence

from openverify.errors import ProtocolError
from openverify.model import OperationRequirement, ProviderBinding
from openverify.provider import ProviderContractError
from openverify.relay.error_codes import RelayErrorCode
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider, ProviderBinder
from openverify.relay.ports.binding import compatible, identity


def validate_choice(value: object) -> AvailableProvider:
    if not isinstance(value, AvailableProvider):
        raise RelayError("PROVIDER_BINDING_MISMATCH", "Binder returned an invalid provider value")
    return value


def bind(
    requirement: OperationRequirement,
    providers: Sequence[AvailableProvider],
    binder: ProviderBinder,
    explicit: ProviderBinding | None = None,
) -> AvailableProvider:
    try:
        chosen = binder.bind(requirement, providers, explicit)
    except (ProtocolError, ProviderContractError):
        raise
    except Exception as exc:
        raise RelayError(
            RelayErrorCode.BINDER_FAILURE,
            "Provider binder failed",
            details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
        ) from exc
    chosen = validate_choice(chosen)
    if not compatible(requirement, chosen) or (
        explicit is not None and identity(chosen, requirement) != explicit
    ):
        raise RelayError("PROVIDER_BINDING_MISMATCH", "Binder returned an incompatible provider")
    if not any(
        chosen.transport is p.transport and chosen.manifest == p.manifest for p in providers
    ):
        raise RelayError("PROVIDER_UNTRUSTED", "Binder returned an unregistered provider")
    return chosen
