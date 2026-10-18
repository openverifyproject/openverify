"""Trusted local implementations bound to exact capability ID/version requirements."""

from typing import Protocol

from openverify.model import Context, Decision, ExecutionObservation, Result


class Adapter(Protocol):
    def execute(
        self, inputs: Context, config: Context, /
    ) -> ExecutionObservation | Context | Result | Decision: ...


class Registry:
    def __init__(self) -> None:
        self.operations: dict[tuple[str, str], Adapter] = {}

    def register(self, capability_id: str, capability_version: str, adapter: Adapter) -> None:
        self.operations[(capability_id, capability_version)] = adapter

    def register_derive(self, name: str, adapter: Adapter, *, version: str = "1") -> None:
        self.register(name, version, adapter)

    def register_evaluate(self, name: str, adapter: Adapter, *, version: str = "1") -> None:
        self.register(name, version, adapter)

    def register_control(self, name: str, adapter: Adapter, *, version: str = "1") -> None:
        self.register(name, version, adapter)
