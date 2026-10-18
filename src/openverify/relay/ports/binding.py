"""Pure manifest compatibility and concrete identity values."""

from openverify.model import OperationRequirement, ProviderBinding
from openverify.provider import parse_provider_manifest, wire_data
from openverify.relay.ports import AvailableProvider


def compatible(requirement: OperationRequirement, provider: AvailableProvider) -> bool:
    manifest = parse_provider_manifest(wire_data(provider.manifest))
    return (
        "0.1" in manifest.supported_contract_versions
        and "draft" in manifest.supported_vcp_versions
        and any(
            c.capability_id == requirement.capability_id
            and c.capability_version == requirement.capability_version
            and c.vcp_version in (None, "draft")
            for c in manifest.capabilities
        )
    )


def identity(provider: AvailableProvider, requirement: OperationRequirement) -> ProviderBinding:
    return ProviderBinding(
        provider_id=provider.manifest.provider_id,
        provider_version=provider.manifest.provider_version,
        capability_id=requirement.capability_id,
        capability_version=requirement.capability_version,
    )
