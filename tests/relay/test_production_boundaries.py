"""Contract failures stop before invocation, including lazy port implementations."""

from collections import UserList
from collections.abc import Iterator, Sequence
from typing import cast

import pytest

from openverify import Relay
from openverify.model import OperationRequirement, ProviderBinding
from openverify.provider import ProviderContractError, ProviderManifest
from openverify.relay.adapters.binder import DeterministicBinder
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.config import RuntimeConfig
from openverify.relay.errors import RelayError
from openverify.relay.ports import (
    AvailableProvider,
    ProviderBinder,
    ProviderCatalog,
    ProviderTransport,
)
from tests.relay.helpers import echo_graph, echo_provider, local_catalog
from tests.relay.test_ports import HostDriver


class ReplacementCatalog:
    def __init__(self, values: object) -> None:
        self.values = values

    def providers(self) -> Sequence[AvailableProvider]:
        return cast(Sequence[AvailableProvider], self.values)


class ReplacementBinder:
    def __init__(self, value: object) -> None:
        self.value = value

    def bind(
        self,
        requirement: OperationRequirement,
        providers: Sequence[AvailableProvider],
        explicit: ProviderBinding | None = None,
    ) -> AvailableProvider:
        return cast(AvailableProvider, self.value)


class FailingSequence(UserList[AvailableProvider]):
    def __iter__(self) -> Iterator[AvailableProvider]:
        yield local_catalog().providers()[0]
        raise RuntimeError("lazy catalog lookup")


@pytest.mark.parametrize("values", [None, {}, "invalid", (object(),)])
def test_invalid_catalog(values: object) -> None:
    driver = HostDriver()
    with pytest.raises(RelayError) as caught:
        Relay(catalog=ReplacementCatalog(values), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert caught.value.code == "CATALOG_INVALID"
    assert driver.calls == 0


def test_lazy_catalog_iteration_failure_is_wrapped() -> None:
    driver = HostDriver()
    with pytest.raises(RelayError) as caught:
        Relay(catalog=ReplacementCatalog(FailingSequence()), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert caught.value.code == "CATALOG_FAILURE"
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert caught.value.details == {
        "cause_type": "RuntimeError",
        "cause_message": "lazy catalog lookup",
    }
    assert driver.calls == 0


def test_generator_is_not_a_catalog_sequence() -> None:
    def values() -> Iterator[AvailableProvider]:
        yield local_catalog().providers()[0]
        raise RuntimeError("generator failure")

    with pytest.raises(RelayError, match="CATALOG_INVALID"):
        Relay(catalog=ReplacementCatalog(values())).run_sync(echo_graph(), inputs={"x": 1})


def test_catalog_manifest_and_duplicate_validation() -> None:
    value = local_catalog().providers()[0]
    malformed = AvailableProvider(
        value.manifest.model_copy(update={"provider_id": "invalid"}), value.transport
    )
    driver = HostDriver()
    with pytest.raises(ProviderContractError) as caught:
        Relay(catalog=ReplacementCatalog((malformed,)), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert caught.value.code == "INVALID_PROVIDER_OUTPUT"
    with pytest.raises(RelayError, match="PROVIDER_CONFLICT"):
        Relay(catalog=ReplacementCatalog((value, value)), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    catalog = local_catalog()
    with pytest.raises(RelayError, match="PROVIDER_CONFLICT"):
        catalog.register(echo_provider())
    assert driver.calls == 0


def test_catalog_initialization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = RuntimeError("initialization failed")

    def broken() -> Catalog:
        raise failure

    monkeypatch.setattr("openverify.standard.standard_catalog", broken)
    with pytest.raises(RelayError, match="CATALOG_FAILURE") as caught:
        Relay()
    assert caught.value.__cause__ is failure


def test_registration_manifest_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    implementation = echo_provider()
    failure = RuntimeError("manifest lookup failed")

    def broken(_: object) -> object:
        raise failure

    monkeypatch.setattr(type(implementation), "manifest", broken)
    with pytest.raises(RelayError, match="CATALOG_FAILURE") as caught:
        Catalog().register(implementation)
    assert caught.value.__cause__ is failure


def test_trusted_entry_point_initialization_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    failure = RuntimeError("entry point initialization failed")

    class Entry:
        name = "trusted"

        def load(self) -> object:
            raise failure

    def entries(*, group: str) -> tuple[Entry]:
        assert group == "openverify.providers"
        return (Entry(),)

    monkeypatch.setattr("openverify.relay.adapters.catalog.entry_points", entries)
    Catalog().load_entry_points(set())
    with pytest.raises(RelayError, match="CATALOG_FAILURE") as caught:
        Catalog().load_entry_points({"trusted"})
    assert caught.value.__cause__ is failure


@pytest.mark.parametrize("value", [None, object()])
def test_invalid_binder_choice(value: object) -> None:
    driver = HostDriver()
    with pytest.raises(RelayError, match="PROVIDER_BINDING_MISMATCH"):
        Relay(catalog=local_catalog(), binder=ReplacementBinder(value), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert driver.calls == 0


@pytest.mark.parametrize("field", ["capability_id", "capability_version"])
def test_binder_cannot_select_incompatible_capability(field: str) -> None:
    value = local_catalog().providers()[0]
    capability = value.manifest.capabilities[0].model_copy(update={field: "com.example.other"})
    value = AvailableProvider(
        value.manifest.model_copy(update={"capabilities": [capability]}), value.transport
    )
    driver = HostDriver()
    with pytest.raises(RelayError, match="PROVIDER_BINDING_MISMATCH"):
        Relay(
            catalog=ReplacementCatalog((value,)), binder=ReplacementBinder(value), driver=driver
        ).run_sync(echo_graph(), inputs={"x": 1})
    assert driver.calls == 0


def test_unavailable_ambiguous_and_explicit_binding() -> None:
    driver = HostDriver()
    with pytest.raises(RelayError, match="CAPABILITY_UNAVAILABLE"):
        Relay(catalog=ReplacementCatalog(()), driver=driver).run_sync(echo_graph(), inputs={"x": 1})
    catalog = local_catalog()
    catalog.register(echo_provider(provider_id="com.example.second"))
    values = catalog.providers()
    with pytest.raises(RelayError, match="PROVIDER_AMBIGUOUS"):
        Relay(catalog=ReplacementCatalog(values), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert driver.calls == 0
    binding = ProviderBinding(
        provider_id="com.example.second",
        provider_version="1",
        capability_id="com.example.echo",
        capability_version="1",
    )
    run = Relay(
        catalog=ReplacementCatalog(values),
        binder=DeterministicBinder(),
        config=RuntimeConfig(bindings={"echo": binding}),
    ).run_sync(echo_graph(), inputs={"x": 1})
    assert run.record.provider_bindings == {"echo": binding}
    assert run.record.nodes[0].executor_ref == binding.provider_id


def test_port_structured_errors_are_not_reclassified() -> None:
    failure = ProviderContractError("INVALID_INPUT", "host rejection", {"field": "x"})

    class Broken:
        def providers(self) -> Sequence[AvailableProvider]:
            raise failure

        def bind(self, *args: object) -> AvailableProvider:
            raise failure

    for relay in (
        Relay(catalog=cast(ProviderCatalog, Broken())),
        Relay(catalog=local_catalog(), binder=cast(ProviderBinder, Broken())),
    ):
        with pytest.raises(ProviderContractError) as caught:
            relay.run_sync(echo_graph(), inputs={"x": 1})
        assert caught.value is failure


def test_binder_cannot_rewrite_trusted_manifest_schemas() -> None:
    class RewritingBinder:
        def bind(
            self,
            requirement: OperationRequirement,
            providers: Sequence[AvailableProvider],
            explicit: ProviderBinding | None = None,
        ) -> AvailableProvider:
            provider = providers[0]
            schema = provider.manifest.capabilities[0].input_schema
            assert isinstance(schema, dict)
            schema.clear()
            return provider

    catalog = local_catalog()
    driver = HostDriver()
    with pytest.raises(RelayError, match="PROVIDER_UNTRUSTED"):
        Relay(catalog=catalog, binder=RewritingBinder(), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    assert driver.calls == 0
    assert catalog.providers()[0].manifest.capabilities[0].input_schema != {}


@pytest.mark.parametrize("field", ["manifest", "transport"])
def test_invalid_provider_members_at_both_ports_and_registration(field: str) -> None:
    valid = local_catalog().providers()[0]
    invalid = AvailableProvider(
        cast(ProviderManifest, None) if field == "manifest" else valid.manifest,
        cast(ProviderTransport, None) if field == "transport" else valid.transport,
    )
    driver = HostDriver()
    with pytest.raises(RelayError, match="CATALOG_INVALID"):
        Relay(catalog=ReplacementCatalog((invalid,)), driver=driver).run_sync(
            echo_graph(), inputs={"x": 1}
        )
    with pytest.raises(RelayError, match="PROVIDER_BINDING_MISMATCH"):
        Relay(
            catalog=ReplacementCatalog((valid,)), binder=ReplacementBinder(invalid), driver=driver
        ).run_sync(echo_graph(), inputs={"x": 1})
    with pytest.raises(RelayError, match="CATALOG_INVALID"):
        Catalog().register_transport(invalid.manifest, invalid.transport)
    assert driver.calls == 0


def test_unserializable_manifest_registration_is_structured() -> None:
    value = local_catalog().providers()[0]
    malformed = value.manifest.model_copy(update={"extensions": {"invalid": object()}})
    with pytest.raises(RelayError, match="CATALOG_INVALID") as caught:
        Catalog().register_transport(malformed, value.transport)
    assert caught.value.__cause__ is not None
    assert caught.value.details is not None
