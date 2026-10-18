"""Explicit run-local state transitions, without side effects."""

from dataclasses import dataclass, field
from typing import Literal

from openverify.model import NodeRecord

type Phase = Literal["PENDING", "READY", "RUNNING", "TERMINAL"]


@dataclass
class RunState:
    phases: dict[str, Phase]
    records: dict[str, NodeRecord] = field(default_factory=lambda: dict[str, NodeRecord]())

    def transition(self, node_id: str, target: Phase) -> None:
        allowed: dict[Phase, set[Phase]] = {
            "PENDING": {"READY", "TERMINAL"},
            "READY": {"RUNNING", "TERMINAL"},
            "RUNNING": {"TERMINAL"},
            "TERMINAL": set(),
        }
        if target not in allowed[self.phases[node_id]]:
            raise ValueError(f"Illegal transition {self.phases[node_id]} -> {target}")
        self.phases[node_id] = target
