"""Trusted host adapter contracts; executor names never trigger dynamic imports."""

from typing import Protocol

from openverify.model import Context, Decision, Result


class DeriveAdapter(Protocol):
    def execute(self, context: Context, config: Context) -> Context: ...


class EvaluateAdapter(Protocol):
    def execute(
        self, context: Context, prior_results: dict[str, Result], config: Context
    ) -> Result: ...


class ControlAdapter(Protocol):
    def execute(
        self, context: Context, results: dict[str, Result], config: Context
    ) -> Decision: ...


class Registry:
    def __init__(self) -> None:
        self.derivers: dict[str, DeriveAdapter] = {}
        self.evaluators: dict[str, EvaluateAdapter] = {}
        self.controllers: dict[str, ControlAdapter] = {}

    def register_derive(self, name: str, adapter: DeriveAdapter) -> None:
        self.derivers[name] = adapter

    def register_evaluate(self, name: str, adapter: EvaluateAdapter) -> None:
        self.evaluators[name] = adapter

    def register_control(self, name: str, adapter: ControlAdapter) -> None:
        self.controllers[name] = adapter
