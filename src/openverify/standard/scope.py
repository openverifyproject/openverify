"""Findings use one-based lines/columns and half-open end coordinates."""

from typing import cast

from pydantic import JsonValue

from openverify.model import Context, Result
from openverify.standard.common import ARRAY, STRING, STRINGS, judge, object_schema, standard
from openverify.standard.paths import in_directory, path_key


def intersects(finding: dict[str, JsonValue], hunk: dict[str, JsonValue]) -> bool:
    if (
        path_key(cast(str, finding["file"])) != path_key(cast(str, hunk["file"]))
        or hunk["count"] == 0
    ):
        return False
    start = cast(int, finding["line"])
    end = cast(int, finding.get("end_line", start))
    if (
        end == start
        and "end_column" in finding
        and cast(int, finding["end_column"]) <= cast(int, finding.get("column", 1))
    ):
        return False
    if end > start and finding.get("end_column") == 1:
        end -= 1
    return start < cast(int, hunk["start"]) + cast(int, hunk["count"]) and end >= cast(
        int, hunk["start"]
    )


def span_intersects(finding: Context, span: Context) -> bool:
    def coordinates(value: Context) -> tuple[tuple[int, int], tuple[int, int]]:
        line = cast(int, value["line"])
        column = cast(int, value.get("column", 1))
        end = (
            cast(int, value.get("end_line", line)),
            cast(int, value.get("end_column", column + 1)),
        )
        if "column" not in value:
            end = (cast(int, value.get("end_line", line)) + 1, 1)
        return (line, column), end

    a, b = coordinates(finding)
    c, d = coordinates(span)
    return (
        path_key(cast(str, finding["file"])) == path_key(cast(str, span["file"]))
        and a < b
        and c < d
        and a < d
        and c < b
    )


async def filter_findings(inputs: Context, config: Context) -> Context:
    findings = cast(list[dict[str, JsonValue]], inputs["findings"])
    mode = config["mode"]
    if mode in ("files", "changed_files"):
        files = {path_key(f) for f in cast(list[str], inputs.get("files", []))}
        selected = [f for f in findings if path_key(cast(str, f["file"])) in files]
    elif mode == "directory":
        directory = cast(str, config["directory"])
        path_key(directory)
        selected = [f for f in findings if in_directory(cast(str, f["file"]), directory)]
    elif mode in ("changed_spans", "ast_ranges"):
        hunks = cast(list[dict[str, JsonValue]], inputs.get("ranges", []))
        compare = span_intersects if mode == "ast_ranges" else intersects
        selected = [f for f in findings if any(compare(f, h) for h in hunks)]
    else:
        raise ValueError("Unknown scope mode")
    return {"findings": cast(JsonValue, selected)}


async def no_findings(inputs: Context, config: Context) -> Result:
    return judge(cast(list[JsonValue], inputs["findings"]))


def scope_providers():
    # Empty lists are explicit; no absent semantic inputs or hidden scope fallback.
    return [
        standard(
            "scope",
            "DERIVE",
            {"findings": ARRAY, "files": STRINGS, "ranges": ARRAY},
            {"findings": ARRAY},
            filter_findings,
            config=object_schema(
                {
                    "mode": {
                        "enum": [
                            "files",
                            "changed_files",
                            "directory",
                            "changed_spans",
                            "ast_ranges",
                        ]
                    },
                    "directory": STRING,
                },
                optional={"directory"},
            ),
        ),
        standard("no_findings", "EVALUATE", {"findings": ARRAY}, {}, no_findings),
    ]
