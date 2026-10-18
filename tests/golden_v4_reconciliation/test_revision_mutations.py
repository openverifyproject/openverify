"""Reintroduce actual defects and execute the corresponding real assertions."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from openverify import ProtocolError, dataflow

from . import test_snapshot as assertions


def test_cancelled_availability_mutation(request):
    case = next(
        c
        for c in assertions.CASES
        if c["context"].get("state") == "CANCELLED"
        and c["context"].get("kind") == "DERIVE"
        and c["expected"].get("handler") == "BLOCK"
    )
    witness_request = SimpleNamespace(node=SimpleNamespace())
    assertions.test_snapshot_relation(case, witness_request)
    original = dataflow.resolve_source

    def corrupt(source, values, records, graph):
        result = original(source, values, records, graph)
        if (
            getattr(source, "node_id", None) in records
            and records[source.node_id].state == "CANCELLED"
        ):
            return result.model_copy(update={"status": "PRODUCER_NOT_EXECUTED"})
        return result

    with patch.object(dataflow, "resolve_source", corrupt), pytest.raises(AssertionError):
        assertions.test_snapshot_relation(case, witness_request)
    request.node.expected = {"baseline": "PASS", "detected": True}
    request.node.actual = {"baseline": "PASS", "detected": True}


def test_custom_empty_membership_mutation(request):
    witness_request = SimpleNamespace(node=SimpleNamespace())
    assertions.test_custom_empty_invocation("PASS", witness_request)
    original = dataflow.validate_graph

    def corrupt(graph, *args, **kwargs):
        if any(n.kind == "AGGREGATE" and not n.aggregate_inputs for n in graph.nodes):
            raise ProtocolError("AGGREGATE_CONFIG", "Reintroduced universal nonempty restriction")
        return original(graph, *args, **kwargs)

    with (
        patch.object(dataflow, "validate_graph", corrupt),
        pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"),
    ):
        assertions.test_custom_empty_invocation("PASS", witness_request)
    request.node.expected = {"baseline": "PASS", "detected": True}
    request.node.actual = {"baseline": "PASS", "detected": True}


def test_usage_collision_mutation(request):
    from openverify import Relay

    from .test_boundary_regressions import test_timing_preserves_every_provider_dimension

    test_timing_preserves_every_provider_dimension()
    original = Relay.run

    async def corrupt(*args, **kwargs):
        run = await original(*args, **kwargs)
        usage = run.record.nodes[0].usage
        usage["relay_wall_time"] = usage["relay_wall_time_3"]
        return run

    with patch.object(Relay, "run", corrupt), pytest.raises(AssertionError):
        test_timing_preserves_every_provider_dimension()
    request.node.expected = {"baseline": "PASS", "detected": True}
    request.node.actual = {"baseline": "PASS", "detected": True}
