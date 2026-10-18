"""All eight standard reducers execute as bound Contract providers in real graphs."""

from typing import cast

import pytest

from openverify import Graph, Relay, parse_run_record
from openverify.authoring import constant
from openverify.model import Context, Result
from openverify.relay import provider
from openverify.standard import standard_catalog
from openverify.standard.common import OBJECT
from tests.relay.helpers import known


@pytest.mark.parametrize(
    ("reducer", "expected"),
    [
        ("ALL", "FAIL"),
        ("ANY", "PASS"),
        ("MAJORITY", "PASS"),
        ("MIN_SCORE", 0.2),
        ("MAX_SCORE", 0.8),
        ("AVERAGE", 0.4),
        ("WEIGHTED_AVERAGE", 0.3),
        ("WORST_SEVERITY", "high"),
    ],
)
def test_real_bound_reducers(reducer: str, expected: str | float) -> None:
    @provider(
        provider_id="com.example.scored",
        capability_id="com.example.scored",
        kind="EVALUATE",
        input_schema=OBJECT,
        output_schema=OBJECT,
        config_schema=OBJECT,
    )
    async def scored(inputs: Context, config: Context) -> Result:
        return Result.model_validate(inputs["value"])

    catalog = standard_catalog()
    catalog.register(scored, concurrency_safe=True)
    graph = Graph("reducer")
    from openverify.serialization import to_data

    values = [
        known(score=0.2, severity={"domain": "risk", "label": "low"}),
        known("FAIL", score=0.8, severity={"domain": "risk", "label": "high"}),
        known(score=0.2, severity={"domain": "risk", "label": "low"}),
    ]
    refs = [
        graph.evaluate(
            f"source{i}", "com.example.scored", inputs={"value": constant(to_data(value))}
        )
        for i, value in enumerate(values)
    ]
    config: Context = {}
    if reducer == "WEIGHTED_AVERAGE":
        config["weights"] = {"a": 4, "b": 1, "c": 1}
    elif reducer == "WORST_SEVERITY":
        config["severity_domain"] = {
            "id": "risk",
            "levels": [{"label": "low", "rank": 0}, {"label": "high", "rank": 1}],
        }
    graph.aggregate(
        "all",
        {"c": refs[2].result, "b": refs[1].result, "a": refs[0].result},
        reducer=reducer,
        config=config,
    )
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    result = run.results["all"]
    if reducer in ("ALL", "ANY", "MAJORITY"):
        assert result.verdict == expected
    elif reducer == "WORST_SEVERITY":
        assert result.severity is not None and result.severity.label == expected
    else:
        assert result.score == pytest.approx(cast(float, expected))
    assert run.record.provider_bindings["all"].capability_id == "openverify.aggregate"
    assert parse_run_record(run.to_json()) == run.record
