"""Deterministic ready waves and control barriers."""

from openverify.model import Graph, Node


def ready_wave(graph: Graph, terminal: set[str], limit: int) -> list[Node]:
    ready = [
        n
        for n in graph.nodes
        if n.id not in terminal
        and all(e.from_node in terminal for e in graph.edges if e.to_node == n.id)
    ]
    wave: list[Node] = []
    for node in ready:
        if node.kind == "CONTROL":
            return wave or [node]
        wave.append(node)
        if len(wave) == limit:
            break
    return wave
