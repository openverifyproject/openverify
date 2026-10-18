"""Local Python providers retain the same typed wire boundary as external peers."""

import asyncio
from typing import cast

from openverify.provider import Outcome, Provider, ProviderContractError, ProviderEvent
from openverify.relay.adapters.local import ObservedTransportFailure
from openverify.relay.ports import EventSink, InvocationRequest


class InProcessTransport:
    def __init__(self, provider: Provider, concurrency_safe: bool = False) -> None:
        self.provider = provider
        self._lock = None if concurrency_safe else asyncio.Lock()

    async def invoke(self, request: InvocationRequest, emit: EventSink) -> Outcome:
        if self._lock is not None:
            async with self._lock:
                return await self._invoke(request, emit)
        return await self._invoke(request, emit)

    async def _invoke(self, request: InvocationRequest, emit: EventSink) -> Outcome:
        terminal: Outcome | None = None
        try:
            async for raw in self.provider.invoke(request.invocation):
                item = cast(object, raw)
                if terminal is not None:
                    raise ProviderContractError("PROTOCOL_VIOLATION", "Data after terminal outcome")
                if isinstance(item, ProviderEvent):
                    emit(item)
                elif isinstance(item, Outcome):
                    terminal = item
                else:
                    raise ProviderContractError(
                        "INVALID_PROVIDER_OUTPUT", "Unexpected provider item"
                    )
        except asyncio.CancelledError:
            # A task cancellation owns physical cleanup. Never synthesize a provider Outcome.
            try:
                async with asyncio.timeout(0.5):
                    await self.provider.cancel(request.invocation.invocation_id, "Runner cancelled")
            except (Exception, asyncio.CancelledError):
                pass
            raise
        except Exception as exc:
            if terminal is not None:
                raise ObservedTransportFailure(
                    terminal,
                    exc.code if isinstance(exc, ProviderContractError) else "TRANSPORT_ERROR",
                    str(exc),
                ) from exc
            raise
        if terminal is None:
            raise ProviderContractError("PROTOCOL_VIOLATION", "Stream ended without an Outcome")
        return terminal
