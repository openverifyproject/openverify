"""Bind through the injected port, then independently check its choice."""

from collections.abc import Sequence

from openverify.model import OperationRequirement, ProviderBinding
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider, ProviderBinder
from openverify.relay.ports.binding import compatible, identity


def bind(
    requirement: OperationRequirement,
    providers: Sequence[AvailableProvider],
    binder: ProviderBinder,
    explicit: ProviderBinding | None = None,
) -> AvailableProvider:
    chosen = binder.bind(requirement, providers, explicit)
    if not compatible(requirement, chosen) or (
        explicit is not None and identity(chosen, requirement) != explicit
    ):
        raise RelayError("PROVIDER_BINDING_MISMATCH", "Binder returned an incompatible provider")
    if not any(
        chosen.transport is p.transport and chosen.manifest == p.manifest for p in providers
    ):
        raise RelayError("PROVIDER_UNTRUSTED", "Binder returned an unregistered provider")
    return chosen
