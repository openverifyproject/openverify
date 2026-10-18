"""Explicit host bindings for the local proof engine, without discovery or selection."""

from copy import deepcopy
from dataclasses import dataclass

from openverify.adapters import Adapter
from openverify.errors import ProtocolError
from openverify.model import Context, JsonSchema, Node, ProviderBinding
from openverify.provider.model import Capability, ProviderManifest
from openverify.provider.validation import (
    ProviderContractError,
    validate_payload,
    validate_provider_manifest,
)
from openverify.serialization import to_data
from openverify.validation import parse_object


@dataclass(frozen=True)
class BoundProvider:
    binding: ProviderBinding
    manifest: ProviderManifest
    adapter: Adapter

    def snapshot(self) -> "BoundProvider":
        return BoundProvider(deepcopy(self.binding), deepcopy(self.manifest), self.adapter)

    def prepare(self, node: Node, inputs: Context) -> Capability:
        parse_object("provider-binding", to_data(self.binding))
        if (
            self.binding.capability_id != node.operation.capability_id
            or self.binding.capability_version != node.operation.capability_version
            or self.binding.provider_id != self.manifest.provider_id
            or self.binding.provider_version != self.manifest.provider_version
        ):
            raise ProtocolError("PROVIDER_BINDING_MISMATCH", "Binding identity does not match")
        try:
            validate_provider_manifest(self.manifest)
        except ProviderContractError as exc:
            raise ProtocolError("PROVIDER_MANIFEST_INVALID", exc.message) from exc
        if "0.1" not in self.manifest.supported_contract_versions:
            raise ProtocolError("CONTRACT_VERSION_UNSUPPORTED", "Provider does not support 0.1")
        matches = [
            c for c in self.manifest.capabilities if c.capability_id == self.binding.capability_id
        ]
        if not matches:
            raise ProtocolError("CAPABILITY_UNAVAILABLE", "Bound manifest does not declare ID")
        capability = next(
            (c for c in matches if c.capability_version == self.binding.capability_version), None
        )
        if capability is None:
            raise ProtocolError(
                "CAPABILITY_VERSION_UNSUPPORTED", "Bound manifest lacks exact version"
            )
        if capability.vcp_version not in (None, "draft") or (
            any(p.role in ("RESULT", "DECISION") for p in node.outputs)
            and capability.vcp_version != "draft"
        ):
            raise ProtocolError("INVALID_INVOCATION", "Capability must declare compatible VCP data")
        check_payload(capability.input_schema, inputs, "INVALID_INPUT")
        check_payload(capability.config_schema, node.config, "INVALID_CONFIG")
        return capability


def check_payload(schema: JsonSchema, value: Context, code: str) -> None:
    try:
        validate_payload(schema, value, code)
    except ProviderContractError as exc:
        raise ProtocolError(exc.code, exc.message, details=exc.details) from exc
