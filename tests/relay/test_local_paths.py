"""Local scope is lexical, component based, and preserves observation locations."""

import asyncio
import os
from pathlib import Path

import pytest
from pydantic import JsonValue

from openverify.model import Context
from openverify.standard.control import action_policy
from openverify.standard.paths import path_key
from openverify.standard.scope import filter_findings, intersects, span_intersects


@pytest.mark.parametrize("trailing", ["", "/"])
@pytest.mark.parametrize("absolute", [False, True])
def test_directory_membership(tmp_path: Path, trailing: str, absolute: bool) -> None:
    root = str(tmp_path / "selected") if absolute else "selected"
    locations = [root + "/a", root + "/nested/b", root + "-other/a"]
    findings: list[JsonValue] = [{"file": p, "line": 1} for p in locations]
    result = asyncio.run(
        filter_findings({"findings": findings}, {"mode": "directory", "directory": root + trailing})
    )
    assert result == {"findings": findings[:2]}
    assert result["findings"] == findings[:2]  # exact original spelling, including separators


@pytest.mark.parametrize("mode", ["files", "changed_files"])
def test_exact_files_relative_absolute_and_missing(mode: str) -> None:
    finding: Context = {"file": "missing/deleted.py", "line": 1}
    result = asyncio.run(
        filter_findings(
            {"findings": [finding], "files": [str(Path("missing/deleted.py").absolute())]},
            {"mode": mode},
        )
    )
    assert result == {"findings": [finding]}
    assert asyncio.run(filter_findings({"findings": [finding], "files": []}, {"mode": mode})) == {
        "findings": []
    }


@pytest.mark.skipif(os.name != "nt", reason="native Windows separators")
def test_windows_native_and_mixed_separators() -> None:
    findings: list[JsonValue] = [
        {"file": r"selected\a", "line": 1},
        {"file": r"selected/nested\b", "line": 2},
        {"file": r"selected-other\a", "line": 1},
    ]
    assert asyncio.run(
        filter_findings({"findings": findings}, {"mode": "directory", "directory": "selected\\"})
    ) == {"findings": findings[:2]}
    assert path_key("SELECTED/a") == path_key(r"selected\a")
    assert (
        asyncio.run(
            action_policy(
                {"action": "delete", "target": r"tmp\nested/item", "allowed_prefixes": ["tmp\\"]},
                {},
            )
        ).verdict
        == "PASS"
    )


@pytest.mark.skipif(os.name == "nt", reason="POSIX case and separator behavior")
def test_posix_paths_preserve_case_and_backslash() -> None:
    assert path_key("Selected/a") != path_key("selected/a")
    assert path_key(r"selected\a") != path_key("selected/a")


@pytest.mark.parametrize(
    "value", ["", "selected/../outside", "selected/../../outside", "bad\x00path"]
)
def test_invalid_scope_paths_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        asyncio.run(filter_findings({"findings": []}, {"mode": "directory", "directory": value}))
    with pytest.raises(ValueError):
        asyncio.run(
            filter_findings(
                {"findings": [{"file": value}]}, {"mode": "directory", "directory": "selected"}
            )
        )


@pytest.mark.skipif(os.name != "nt", reason="ambiguous Windows paths")
@pytest.mark.parametrize(
    "value",
    [r"C:relative", r"\rooted", r"C:tmp\..\outside", "tmp/item:stream", "tmp/item.", "tmp/NUL"],
)
def test_windows_ambiguous_paths(value: str) -> None:
    with pytest.raises(ValueError):
        path_key(value)


def test_half_open_ranges_and_empty_ranges() -> None:
    finding: Context = {"file": "a", "line": 2, "column": 3, "end_line": 2, "end_column": 5}
    assert span_intersects(finding, {"file": "./a", "line": 2, "column": 4, "end_column": 6})
    assert not span_intersects(finding, {"file": "a", "line": 2, "column": 5, "end_column": 6})
    assert not span_intersects(finding, {"file": "a", "line": 2, "column": 4, "end_column": 4})
    empty = {**finding, "end_column": 3}
    assert not span_intersects(empty, finding)
    assert not intersects(empty, {"file": "a", "start": 2, "count": 1})
    assert not intersects(finding, {"file": "a", "start": 2, "count": 0})
    assert not intersects(
        {**finding, "end_line": 3, "end_column": 1}, {"file": "a", "start": 3, "count": 1}
    )


@pytest.mark.parametrize("prefix", ["tmp", "tmp/"])
@pytest.mark.parametrize(
    "target,allowed",
    [
        ("tmp/item", True),
        ("tmp/nested/item", True),
        ("tmp-other/item", False),
        ("tmp", False),
        ("tmp/../outside", False),
        ("/tmp/item", False),
        ("", False),
    ],
)
def test_action_directory_prefixes(prefix: str, target: str, allowed: bool) -> None:
    result = asyncio.run(
        action_policy({"action": "delete", "target": target, "allowed_prefixes": [prefix]}, {})
    )
    assert result.verdict == ("PASS" if allowed else "FAIL")
    if not allowed:
        assert result.evidence[0].structured_data == {
            "code": "action_denied",
            "action": "delete",
            "target": target,
        }


@pytest.mark.parametrize("prefix", ["", ".", "tmp/../outside", "/tmp"])
def test_invalid_action_prefix_fails_closed(prefix: str) -> None:
    result = asyncio.run(
        action_policy({"action": "delete", "target": "tmp/item", "allowed_prefixes": [prefix]}, {})
    )
    assert result.verdict == "FAIL"
