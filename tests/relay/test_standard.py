"""Standard capability contracts, scopes, schema checks, and missing real tools."""

from pathlib import Path

import pytest

from openverify import Graph, Relay
from openverify.authoring import constant
from openverify.model import Context
from openverify.standard import standard_catalog
from openverify.standard.common import ARRAY, OBJECT, STRING, STRINGS
from openverify.standard.filesystem import FileAccess
from openverify.standard.scope import intersects, span_intersects
from openverify.standard.tools import Tools


@pytest.mark.parametrize(
    ("finding", "hunk", "expected"),
    [
        (
            {"file": "a", "line": 2, "column": 1, "end_line": 3, "end_column": 1},
            {"file": "a", "start": 3, "count": 1},
            False,
        ),
        (
            {"file": "a", "line": 2, "end_line": 3, "end_column": 2},
            {"file": "a", "start": 3, "count": 1},
            True,
        ),
        ({"file": "a", "line": 3}, {"file": "a", "start": 3, "count": 0}, False),
        ({"file": "a", "line": 3}, {"file": "b", "start": 3, "count": 1}, False),
    ],
)
def test_changed_line_conventions(finding: Context, hunk: Context, expected: bool) -> None:
    assert intersects(finding, hunk) == expected


def test_ast_column_intersection_is_half_open() -> None:
    finding: Context = {"file": "a", "line": 3, "column": 2, "end_line": 3, "end_column": 8}
    assert span_intersects(
        finding, {"file": "a", "line": 3, "column": 7, "end_line": 3, "end_column": 9}
    )
    assert not span_intersects(
        finding, {"file": "a", "line": 3, "column": 8, "end_line": 3, "end_column": 9}
    )


def test_json_parse_schema_boolean_number_and_pattern(tmp_path: Path) -> None:
    graph = Graph("json-schema")
    data = graph.input("text", STRING)
    parsed = graph.derive(
        "parse", "openverify.json_parse", inputs={"text": data}, outputs={"value": True}
    )
    graph.evaluate(
        "schema",
        "openverify.schema",
        inputs={"value": parsed["value"]},
        config={"schema": {"const": 1}},
    )
    relay = Relay()
    assert relay.run_sync(graph, inputs={"text": "1"}).results["schema"].verdict == "PASS"
    assert relay.run_sync(graph, inputs={"text": "true"}).results["schema"].verdict == "FAIL"
    assert (
        relay.run_sync(graph, inputs={"text": '{"x":1,"x":2}'}).results["parse"].execution_outcome
        == "ERROR"
    )
    pattern = Graph("regex")
    pattern.evaluate(
        "pattern",
        "openverify.text",
        inputs={"text": constant("abc123", STRING)},
        config={"patterns": [r"\d+"]},
    )
    assert relay.run_sync(pattern, inputs={}).results["pattern"].verdict == "PASS"


@pytest.mark.parametrize(
    "capability", ["openverify.ruff", "openverify.astgrep", "openverify.pytest"]
)
def test_missing_tool_is_execution_error_with_installation_help(
    capability: str, tmp_path: Path
) -> None:
    access = FileAccess((tmp_path,))
    catalog = standard_catalog(tools=Tools(access))
    graph = Graph("missing-tool")
    values = {"cwd": constant(str(tmp_path), STRING)}
    if capability == "openverify.pytest":
        graph.evaluate("tool", capability, inputs=values, config={"tests": []})
    else:
        values["files"] = constant([], STRINGS)
        if capability == "openverify.ruff":
            graph.evaluate(
                "tool",
                capability,
                inputs=values,
                outputs={"findings": ARRAY},
                config={"select": ["F"]},
            )
        else:
            graph.derive(
                "tool",
                capability,
                inputs=values,
                outputs={"findings": ARRAY},
                config={"language": "python", "pattern": "print($$$ARGS)"},
            )
    run = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert run.results["tool"].execution_outcome == "ERROR"
    assert "Install with" in str(run.results["tool"].output)


def test_filesystem_selection_and_binary_observation(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.bin").write_bytes(b"\x00binary")
    graph = Graph("files")
    graph.derive(
        "files",
        "openverify.select_files",
        inputs={"directory": constant(str(tmp_path))},
        outputs={"files": ARRAY},
        config={"mode": "glob", "glob": "*.txt"},
    )
    graph.derive(
        "binary",
        "openverify.read_file",
        inputs={"file": constant(str(tmp_path / "b.bin"))},
        outputs={"base64": STRING, "identity": OBJECT},
    )
    run = Relay(catalog=standard_catalog(roots=(tmp_path,))).run_sync(graph, inputs={})
    assert run.record.nodes[0].information["files"] == [str(tmp_path / "a.txt")]
    assert run.record.nodes[1].information["base64"] == "AGJpbmFyeQ=="
