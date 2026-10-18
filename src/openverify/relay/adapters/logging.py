"""Metadata-only logging: input values and provider diagnostics are not logged."""

import logging
from collections.abc import Callable

from openverify.relay.ports import RelayEvent


class LoggingObserver:
    def observe(self, event: RelayEvent) -> None:
        logging.getLogger("openverify.relay").info(
            "%s run=%s node=%s invocation=%s",
            event.kind,
            event.run_id,
            event.node_id,
            event.invocation_id,
        )


class CallbackObserver:
    def __init__(self, callback: Callable[[RelayEvent], None]) -> None:
        self.callback = callback

    def observe(self, event: RelayEvent) -> None:
        self.callback(event)
