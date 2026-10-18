"""Complete labeled DAG enumeration and bounded abstract interleavings."""

from __future__ import annotations

import itertools
import random


def topological(n: int, edges: tuple) -> tuple | None:
    remaining = set(range(n))
    order = []
    while remaining:
        ready = sorted(v for v in remaining if not any(b == v and a in remaining for a, b in edges))
        if not ready:
            return None
        order.extend(ready)
        remaining.difference_update(ready)
    return tuple(order)


def labeled_dags(bound: int = 4):
    for n in range(bound + 1):
        possible = tuple((a, b) for a in range(n) for b in range(n) if a != b)
        for bits in itertools.product((False, True), repeat=len(possible)):
            edges = tuple(e for e, chosen in zip(possible, bits) if chosen)
            if topological(n, edges) is not None:
                yield n, edges


def explore(n: int, edges: tuple) -> dict:
    """Every reachable PENDING/RUNNING/TERMINAL state and transition, n<=3.

    Starts require all predecessors terminal. Independent running nodes may end in
    either order. Terminal outcome coloring is orthogonal and enumerated separately.
    No work implementation, clocks, output publication or arbitrary user programs.
    """
    initial = ("P",) * n
    seen, pending, transitions = {initial}, [initial], set()
    while pending:
        state = pending.pop()
        for i in range(n):
            action = "finish" if state[i] == "R" else "start"
            eligible = state[i] == "R" or (
                state[i] == "P" and all(state[a] == "T" for a, b in edges if b == i)
            )
            if not eligible:
                continue
            target = list(state)
            target[i] = "T" if state[i] == "R" else "R"
            target = tuple(target)
            transitions.add((state, action, i, target))
            if target not in seen:
                seen.add(target)
                pending.append(target)
    return {
        "states": [list(s) for s in sorted(seen)],
        "transitions": [[list(s), a, i, list(t)] for s, a, i, t in sorted(transitions)],
    }


def generated(seed: int, count: int = 32, bound: int = 12):
    rng = random.Random(seed)
    for _ in range(count):
        n = rng.randint(5, bound)
        order = list(range(n))
        rng.shuffle(order)
        edges = tuple(
            sorted(
                (order[a], order[b])
                for a in range(n)
                for b in range(a + 1, n)
                if rng.random() < 0.25
            )
        )
        yield n, edges


def shrink(n: int, edges: tuple):
    """Stable edge deletion then isolated highest-label removal; preserves DAGs."""
    for i in range(len(edges)):
        yield n, edges[:i] + edges[i + 1 :]
    if n and all(n - 1 not in e for e in edges):
        yield n - 1, edges


if __name__ == "__main__":
    import json
    from collections import Counter

    print(json.dumps(dict(Counter(n for n, _ in labeled_dags())), sort_keys=True))
