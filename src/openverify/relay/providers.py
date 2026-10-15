"""Small Python provider authoring API, producing real Contract manifests/outcomes."""

import asyncio
import inspect
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import Literal, cast

from openverify.model import (
    Activation,
    Admission,
    Context,
    Decision,
    ExecutionObservation,
    JsonSchema,
    Result,
    Selection,
)
from openverify.provider import (
    Capability,
    Invocation,
    LifecycleFeatures,
    Outcome,
    ProviderError,
    ProviderEvent,
    ProviderManifest,
    parse_provider_manifest,
    wire_data,
)
from openverify.serialization import decode, to_data

type Computation = Callable[
    [Context, Context],
    Awaitable[
        Context | ExecutionObservation | Result | Decision | Activation | Selection | Admission
    ],
]
type OperationKind = Literal[
    "DERIVE", "EVALUATE", "CONTROL", "AGGREGATE", "ACTIVATION", "SELECTION", "ADMISSION"
]


@dataclass(frozen=True)
class FunctionProvider:
    specification: ProviderManifest
    kind: OperationKind
    function: Computation

    def manifest(self) -> ProviderManifest:
        return parse_provider_manifest(wire_data(self.specification))

    async def cancel(self, invocation_id: str, reason: str | None = None) -> None:
        # The in-process transport cancels the invocation task itself.
        return None

    async def invoke(self, invocation: Invocation) -> AsyncIterator[ProviderEvent | Outcome]:
        if invocation.resource_budget is not None:
            raise ValueError("Function providers cannot enforce resource budgets")
        try:
            value = await self.function(
                cast(Context, decode(invocation.input)), cast(Context, decode(invocation.config))
            )
            if isinstance(value, (Activation, Selection, Admission)):
                output = to_data(value)
                observation = ExecutionObservation()
            else:
                if isinstance(value, Result):
                    observation = ExecutionObservation(
                        outputs={"result": to_data(value)}, usage=value.usage
                    )
                elif isinstance(value, Decision):
                    observation = ExecutionObservation(outputs={"decision": to_data(value)})
                elif isinstance(value, ExecutionObservation):
                    observation = value
                else:
                    observation = ExecutionObservation(outputs=value)
                output = observation.outputs
            sequence = 0
            for evidence in observation.evidence:
                sequence += 1
                yield ProviderEvent(
                    invocation_id=invocation.invocation_id,
                    sequence=sequence,
                    kind="evidence",
                    payload=to_data(evidence),
                )
            usage: Context = {k: to_data(v) for k, v in observation.usage.items()}
            # Usage precedes final output validation, so invalid output cannot erase it.
            if usage:
                sequence += 1
                yield ProviderEvent(
                    invocation_id=invocation.invocation_id,
                    sequence=sequence,
                    kind="resource_usage",
                    payload=usage,
                )
            if observation.error is not None:
                error = observation.error
                yield Outcome(
                    invocation_id=invocation.invocation_id,
                    state="ERROR",
                    error=ProviderError(
                        code="openverify.computation_error",
                        message=f"{error.code}: {error.message}",
                    ),
                    resource_usage=usage,
                )
            else:
                yield Outcome(
                    invocation_id=invocation.invocation_id,
                    state="COMPLETED",
                    output=output,
                    resource_usage=usage,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            yield Outcome(
                invocation_id=invocation.invocation_id,
                state="ERROR",
                error=ProviderError(
                    code="openverify.computation_error", message=str(exc) or type(exc).__name__
                ),
            )


def provider(
    *,
    provider_id: str,
    capability_id: str,
    kind: OperationKind,
    input_schema: JsonSchema,
    output_schema: JsonSchema,
    config_schema: JsonSchema,
    provider_version: str = "1",
    capability_version: str = "1",
) -> Callable[[Computation], FunctionProvider]:
    """Decorate an async computation. Registration is an explicit host trust action."""
    manifest = ProviderManifest(
        provider_id=provider_id,
        provider_version=provider_version,
        supported_contract_versions=["0.1"],
        supported_vcp_versions=["draft"],
        capabilities=[
            Capability(
                capability_id=capability_id,
                capability_version=capability_version,
                input_schema=input_schema,
                output_schema=output_schema,
                config_schema=config_schema,
                vcp_version="draft",
                lifecycle_features=LifecycleFeatures(
                    streaming=True, cancellation=True, deadlines=False, resource_reporting=True
                ),
                extensions={"openverify.operation": {"kind": kind}},
            )
        ],
    )
    validated = parse_provider_manifest(wire_data(manifest))

    def decorate(function: Computation) -> FunctionProvider:
        if not inspect.iscoroutinefunction(function):
            raise TypeError("Python provider functions must be async; use stdio for blocking code")
        return FunctionProvider(validated, kind, function)

    return decorate
