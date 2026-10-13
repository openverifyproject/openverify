import pytest
from pydantic import JsonValue

from openverify import ProtocolError, parse_run_record, serialize
from openverify.adapters.demo import demo_registry, known
from openverify.engine import Engine
from openverify.model import AdmissionPolicy, Edge, Graph, Node, RunRecord
from openverify.serialization import json_equal, to_data
from tests.helpers import context, definition


def skipped_run() -> RunRecord:
    d = definition()
    d = d.model_copy(
        update={
            "execution_policy": d.execution_policy.model_copy(
                update={"admission": AdmissionPolicy(strategy="PROBABILITY", probability=0)}
            )
        }
    )
    return Engine(demo_registry()).run(d, context(), opportunity_id="skip-regression")


def test_admission_skip_complete_multinode_record() -> None:
    run = skipped_run()
    assert len(run.nodes) == 4
    assert all(n.result is not None and n.result.disposition == "SKIPPED" for n in run.nodes)
    assert json_equal(to_data(parse_run_record(serialize(run))), to_data(run))


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("disposition", ["DEFERRED", "CANCELLED"])
def test_admission_skip_rejects_each_node_disposition(index: int, disposition: str) -> None:
    run = skipped_run()
    result = run.nodes[index].result
    assert result is not None
    nodes = list(run.nodes)
    nodes[index] = nodes[index].model_copy(
        update={"result": result.model_copy(update={"disposition": disposition})}
    )
    bad = run.model_copy(update={"nodes": nodes})
    with pytest.raises(ProtocolError) as error:
        parse_run_record(serialize(bad))
    assert error.value.code == "PROVENANCE_LINEAGE"
    assert error.value.message == "Admission SKIP requires every node to be SKIPPED"


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("disposition", ["DEFERRED", "CANCELLED"])
def test_admission_skip_rejects_each_final_disposition(index: int, disposition: str) -> None:
    run = skipped_run()
    id = run.nodes[index].node_id
    final = dict(run.final_results)
    final[id] = final[id].model_copy(update={"disposition": disposition})
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(run.model_copy(update={"final_results": final})))


def snapshot_run(value: JsonValue) -> RunRecord:
    graph = Graph(
        nodes=[
            Node(
                id="source",
                kind="EVALUATE",
                executor_ref="demo.constant",
                config={"result": to_data(known("PASS").model_copy(update={"output": value}))},
            ),
            Node(
                id="dependent",
                kind="EVALUATE",
                executor_ref="demo.constant",
                config={"result": to_data(known("PASS"))},
            ),
        ],
        edges=[Edge(from_node="source", to_node="dependent")],
    )
    d = definition("generic")
    d = d.model_copy(
        update={"graph": graph, "subject": d.subject.model_copy(update={"locator": value})}
    )
    return Engine(demo_registry()).run(d, {}, opportunity_id="snapshot-regression")


@pytest.mark.parametrize("target", ["subject", "upstream", "final"])
@pytest.mark.parametrize(
    "original,changed",
    [(1, True), (0, False), ([1], [True]), ([0], [False]), ({"x": [1]}, {"x": [True]})],
)
def test_snapshot_json_type_substitution_rejected(
    target: str, original: JsonValue, changed: JsonValue
) -> None:
    run = snapshot_run(original)
    if target == "subject":
        bad = run.model_copy(
            update={"subject": run.subject.model_copy(update={"locator": changed})}
        )
    elif target == "upstream":
        node = run.nodes[-1]
        upstream = {
            "source": node.upstream_results["source"].model_copy(update={"output": changed})
        }
        bad = run.model_copy(
            update={"nodes": [run.nodes[0], node.model_copy(update={"upstream_results": upstream})]}
        )
    else:
        final = dict(run.final_results)
        final["source"] = final["source"].model_copy(update={"output": changed})
        bad = run.model_copy(update={"final_results": final})
    with pytest.raises(ProtocolError, match="PROVENANCE_LINEAGE"):
        parse_run_record(serialize(bad))


def test_snapshot_object_member_order_is_irrelevant() -> None:
    value: JsonValue = {"a": [1, True, None], "b": {"zero": 0}}
    reordered: JsonValue = {"b": {"zero": 0}, "a": [1, True, None]}
    run = snapshot_run(value)
    node = run.nodes[-1]
    final = dict(run.final_results)
    final["source"] = final["source"].model_copy(update={"output": reordered})
    bad = run.model_copy(
        update={
            "subject": run.subject.model_copy(update={"locator": reordered}),
            "nodes": [
                run.nodes[0],
                node.model_copy(update={"upstream_results": {"source": final["source"]}}),
            ],
            "final_results": final,
        }
    )
    parse_run_record(serialize(bad))


def timestamp_run(text: str) -> RunRecord:
    run = snapshot_run(None)
    return run.model_copy(
        update={
            "started_at": text,
            "finished_at": text,
            "nodes": [
                n.model_copy(update={"started_at": text, "finished_at": text}) for n in run.nodes
            ],
        }
    )


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-13T12:00:00Z",
        "2026-10-13T12:00:00+00:00",
        "2026-10-13t12:00:00z",
        "2026-10-13T12:00:00.1Z",
        "2026-10-13T12:00:00.123456789+00:00",
    ],
)
def test_utc_rfc3339_forms_preserved(text: str) -> None:
    run = timestamp_run(text)
    parsed = parse_run_record(serialize(run))
    assert parsed.started_at == parsed.finished_at == text
    assert all(n.started_at == n.finished_at == text for n in parsed.nodes)


@pytest.mark.parametrize(
    "text",
    [
        "2026-10-13T12:00:00+01:00",
        "2026-10-13T12:00:00-05:00",
        "2026-10-13T12:00:00",
        "2026-13-13T12:00:00Z",
        "2026-02-30T12:00:00Z",
        "not a timestamp",
    ],
)
@pytest.mark.parametrize("target", ["run", "node"])
def test_invalid_timestamp_at_each_record_level(text: str, target: str) -> None:
    run = timestamp_run("2026-10-13T12:00:00Z")
    if target == "run":
        bad = run.model_copy(update={"started_at": text})
    else:
        bad = run.model_copy(
            update={"nodes": [run.nodes[0].model_copy(update={"finished_at": text}), run.nodes[1]]}
        )
    with pytest.raises(ProtocolError, match="PROTOCOL_STRUCTURE"):
        parse_run_record(serialize(bad))


def test_equivalent_utc_forms_in_one_record() -> None:
    run = timestamp_run("2026-10-13T12:00:00Z")
    run = run.model_copy(
        update={
            "finished_at": "2026-10-13T12:00:00+00:00",
            "nodes": [
                n.model_copy(update={"started_at": "2026-10-13T12:00:00+00:00"}) for n in run.nodes
            ],
        }
    )
    parse_run_record(serialize(run))
