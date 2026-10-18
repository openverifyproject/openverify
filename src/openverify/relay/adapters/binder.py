"""Exact matching, explicit precedence, and no ambiguous fallback."""

from collections.abc import Sequence

from openverify.model import OperationRequirement, ProviderBinding
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider
from openverify.relay.ports.binding import compatible, identity


class DeterministicBinder:
    def bind(
        self,
        requirement: OperationRequirement,
        providers: Sequence[AvailableProvider],
        explicit: ProviderBinding | None = None,
    ) -> AvailableProvider:
        matches = [p for p in providers if compatible(requirement, p)]
        if explicit is not None:
            matches = [p for p in matches if identity(p, requirement) == explicit]
            if len(matches) != 1:
                raise RelayError(
                    "PROVIDER_BINDING_MISMATCH", "Explicit binding is unavailable or incompatible"
                )
        if not matches:
            raise RelayError("CAPABILITY_UNAVAILABLE", f"No provider for {requirement}")
        if len(matches) != 1:
            raise RelayError(
                "PROVIDER_AMBIGUOUS", f"Bind one of {len(matches)} compatible providers explicitly"
            )
        return matches[0]
