"""Optional typed Python binding; normative definitions live in provider-contract/."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator


class ProviderValue(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)


class Extensible(ProviderValue):
    extensions: dict[str, JsonValue] = Field(default_factory=dict)


class LifecycleFeatures(ProviderValue):
    streaming: bool
    cancellation: bool
    deadlines: bool
    resource_reporting: bool


class Capability(Extensible):
    capability_id: str
    capability_version: str
    input_schema: dict[str, JsonValue] | bool
    output_schema: dict[str, JsonValue] | bool
    config_schema: dict[str, JsonValue] | bool
    lifecycle_features: LifecycleFeatures
    vcp_version: str | None = None


class ProviderManifest(Extensible):
    provider_id: str
    provider_version: str
    supported_contract_versions: list[str]
    supported_vcp_versions: list[str]
    capabilities: list[Capability]


class Invocation(Extensible):
    invocation_id: str
    contract_version: Literal["0.1"]
    capability_id: str
    capability_version: str
    input: JsonValue
    config: JsonValue
    context: JsonValue = None
    vcp_version: str | None = None
    deadline: str | None = None
    resource_budget: dict[str, JsonValue] | None = None


class ProviderEvent(Extensible):
    invocation_id: str
    sequence: int
    kind: Literal["progress", "evidence", "artifact", "resource_usage", "diagnostic", "extension"]
    payload: JsonValue
    timestamp: str | None = None

    @field_validator("sequence", mode="before")
    @classmethod
    def integral_sequence(cls, value: object) -> object:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value


class CancelRequest(Extensible):
    invocation_id: str
    reason: str | None = None


class ProviderError(ProviderValue):
    code: str
    message: str
    details: JsonValue = None


class Outcome(Extensible):
    invocation_id: str
    state: Literal["COMPLETED", "ERROR", "CANCELLED", "DEADLINE_EXCEEDED"]
    output: JsonValue = None
    error: ProviderError | None = None
    resource_usage: dict[str, JsonValue] | None = None


class InitializeRequest(Extensible):
    supported_contract_versions: list[str]
    supported_vcp_versions: list[str]


class InitializeResult(Extensible):
    contract_version: Literal["0.1"]
    manifest: ProviderManifest
