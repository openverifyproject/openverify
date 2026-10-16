"""Explicit trust-controlled provider registration and opt-in entry point loading."""

from collections.abc import Callable
from importlib.metadata import entry_points
from typing import cast

from openverify.errors import ProtocolError
from openverify.provider import (
    Provider,
    ProviderContractError,
    ProviderManifest,
    parse_provider_manifest,
    wire_data,
)
from openverify.relay.errors import RelayError
from openverify.relay.ports import AvailableProvider, ProviderTransport


class Catalog:
    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], AvailableProvider] = {}

    def register_transport(self, manifest: ProviderManifest, transport: ProviderTransport) -> None:
        try:
            if not isinstance(cast(object, manifest), ProviderManifest) or not callable(
                getattr(transport, "invoke", None)
            ):
                raise RelayError(
                    "CATALOG_INVALID", "Registration requires a manifest and transport"
                )
            snapshot = parse_provider_manifest(wire_data(manifest))
        except (ProtocolError, ProviderContractError):
            raise
        except Exception as exc:
            raise RelayError(
                "CATALOG_INVALID",
                "Invalid provider registration",
                details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
            ) from exc
        key = (snapshot.provider_id, snapshot.provider_version)
        if key in self._providers:
            raise RelayError("PROVIDER_CONFLICT", f"Provider already registered: {key}")
        self._providers[key] = AvailableProvider(snapshot, transport)

    def register(self, provider: Provider, *, concurrency_safe: bool = False) -> None:
        from openverify.relay.adapters.inprocess import InProcessTransport

        try:
            manifest = provider.manifest()
        except (ProtocolError, ProviderContractError):
            raise
        except Exception as exc:
            raise RelayError(
                "CATALOG_FAILURE",
                "Provider catalog initialization failed",
                details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
            ) from exc
        self.register_transport(manifest, InProcessTransport(provider, concurrency_safe))

    def load_entry_points(self, trusted: set[str]) -> None:
        """Only explicitly named installed entry points may execute their factory code."""
        try:
            for entry in entry_points(group="openverify.providers"):
                if entry.name in trusted:
                    factory = cast("ProviderFactory", entry.load())
                    self.register(factory())
        except (ProtocolError, ProviderContractError):
            raise
        except Exception as exc:
            raise RelayError(
                "CATALOG_FAILURE",
                "Trusted provider entry point initialization failed",
                details={"cause_type": type(exc).__name__, "cause_message": str(exc)},
            ) from exc

    def providers(self) -> tuple[AvailableProvider, ...]:
        return tuple(
            AvailableProvider(parse_provider_manifest(wire_data(p.manifest)), p.transport)
            for p in self._providers.values()
        )


type ProviderFactory = Callable[[], Provider]
