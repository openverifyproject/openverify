from openverify import parse_definition, serialize
from openverify.adapters.demo import demo_registry
from openverify.engine import Engine
from openverify.model import Measurement
from tests.helpers import context, definition


def test_estimate_and_actual_are_retained_separately() -> None:
    d = definition("generic")
    graph = d.graph.model_copy(deep=True)
    graph.nodes[0] = graph.nodes[0].model_copy(
        update={
            "resource_estimate": {
                "wall_time": Measurement(unit="s", kind="ESTIMATED", value=100),
                "energy": Measurement(unit="J", kind="RANGE", minimum=1, maximum=10),
            }
        }
    )
    d = d.model_copy(update={"graph": graph})
    assert parse_definition(serialize(d)) == d
    run = Engine(demo_registry()).run(d, context("generic"), opportunity_id="o")
    assert run.definition.graph.nodes[0].resource_estimate["wall_time"].kind == "ESTIMATED"
    assert run.nodes[0].usage["wall_time"].kind == "EXACT"
