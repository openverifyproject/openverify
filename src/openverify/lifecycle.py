"""Deterministic lifecycle effects shared by execution and provenance validation."""

from dataclasses import dataclass, field
from typing import Literal

from openverify.dataflow import guards_enabled
from openverify.model import Admission, Context, Decision, Graph, NodeRecord, Result

type Disposition = Literal["SKIPPED", "DEFERRED", "CANCELLED"]
type Cause = tuple[Disposition, str]


def nonexecution(cause: Cause) -> Result:
    disposition, reason = cause
    return Result(disposition=disposition, output={"reason": reason})


def reachable(graph: Graph, roots: set[str]) -> set[str]:
    found = set(roots)
    while True:
        expanded = found | {e.to_node for e in graph.edges if e.from_node in found}
        if expanded == found:
            return found
        found = expanded


@dataclass
class Lifecycle:
    admission: Admission
    stopped: Cause | None = None
    excluded: set[str] = field(default_factory=lambda: set[str]())
    cancelled: bool = False

    def cause(
        self,
        node_id: str,
        graph: Graph,
        values: Context,
        records: dict[str, NodeRecord],
        blocked: bool,
    ) -> Cause | None:
        if self.admission.outcome == "SKIP":
            return "SKIPPED", "ADMISSION_SKIP"
        if self.admission.outcome == "DEFER":
            return "DEFERRED", "ADMISSION_DEFER"
        if self.cancelled:
            return "CANCELLED", "CANCELLATION"
        if self.stopped is not None:
            return self.stopped
        if node_id in self.excluded:
            return "SKIPPED", "ROUTE_EXCLUDED"
        if not guards_enabled(node_id, graph, values, records):
            return "SKIPPED", "GUARD_FALSE"
        if blocked:
            return "SKIPPED", "INPUT_UNAVAILABLE"
        return None

    def control(self, node_id: str, decision: Decision, graph: Graph) -> None:
        if decision.kind in ("STOP_SUCCESS", "STOP_FAILURE"):
            self.stopped = "SKIPPED", "CONTROL_STOP"
        elif decision.kind == "DEFER":
            self.stopped = "DEFERRED", "CONTROL_DEFER"
        elif decision.kind == "RETRY":
            self.stopped = "SKIPPED", "RETRY_REQUESTED"
        elif decision.kind == "ROUTE":
            assert decision.destination is not None
            selected = reachable(graph, {decision.destination})
            others = {e.to_node for e in graph.edges if e.from_node == node_id} - {
                decision.destination
            }
            self.excluded |= reachable(graph, others) - selected


class Cancellation:
    """Host-owned cooperative token. It supplies no semantic computation inputs."""

    def __init__(self) -> None:
        self.reason: str | None = None

    def cancel(self, reason: str = "Host cancellation") -> None:
        if type(reason) is not str or not reason:
            raise ValueError("Cancellation requires a nonempty reason")
        if self.reason is None:
            self.reason = reason
