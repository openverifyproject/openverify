"""Explicit trust-controlled provider registration and opt-in entry point loading."""

from collections.abc import Callable
from importlib.metadata import entry_points
from typing import cast

from openverify.provider import Provider, ProviderManifest, parse_provider_manifest, wire_data
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider, ProviderTransport


class Catalog:
    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], AvailableProvider] = {}

    def register_transport(self, manifest: ProviderManifest, transport: ProviderTransport) -> None:
        snapshot = parse_provider_manifest(wire_data(manifest))
        key = (snapshot.provider_id, snapshot.provider_version)
        if key in self._providers:
            raise RelayError("PROVIDER_CONFLICT", f"Provider already registered: {key}")
        self._providers[key] = AvailableProvider(snapshot, transport)

    def register(self, provider: Provider, *, concurrency_safe: bool = False) -> None:
        from openverify.relay.adapters.inprocess import InProcessTransport

        self.register_transport(provider.manifest(), InProcessTransport(provider, concurrency_safe))

    def load_entry_points(self, trusted: set[str]) -> None:
        """Only explicitly named installed entry points may execute their factory code."""
        for entry in entry_points(group="openverify.providers"):
            if entry.name in trusted:
                factory = cast("ProviderFactory", entry.load())
                self.register(factory())

    def providers(self) -> tuple[AvailableProvider, ...]:
        return tuple(
            AvailableProvider(parse_provider_manifest(wire_data(p.manifest)), p.transport)
            for p in self._providers.values()
        )


type ProviderFactory = Callable[[], Provider]
