"""Explicit Git comparison modes and renamed/deleted/untracked handling."""

from pathlib import Path
from typing import cast

import pytest

from openverify import Graph, Relay
from openverify.authoring import constant
from openverify.model import Context
from openverify.standard import standard_catalog
from openverify.standard.common import ARRAY, OBJECT, STRING
from tests.relay.test_tools import git, repository


def scope(relay: Relay, cwd: Path, mode: str, base: str, untracked: bool = False) -> Context:
    graph = Graph("git-scope")
    graph.derive(
        "scope",
        "openverify.git_scope",
        inputs={"cwd": constant(str(cwd)), "base": constant(base)},
        config={"mode": mode, "include_untracked": untracked},
        outputs={
            "changed_files": ARRAY,
            "changed_hunks": ARRAY,
            "diff": STRING,
            "candidate": OBJECT,
            "changes": ARRAY,
            "deleted_files": ARRAY,
        },
    )
    run = relay.run_sync(graph, inputs={})
    assert run.record.nodes[0].state == "SUCCESS", run.to_json()
    return run.record.nodes[0].information


def test_comparison_modes_are_distinct(tmp_path: Path) -> None:
    cwd = repository(tmp_path / "repo")
    source = cwd / "sample.py"
    source.write_text("value = 2\n")
    git(cwd, "add", ".")
    source.write_text("value = 3\n")
    relay = Relay(catalog=standard_catalog(roots=(cwd,)))
    staged = scope(relay, cwd, "STAGED", "HEAD")
    unstaged = scope(relay, cwd, "UNSTAGED", "")
    worktree = scope(relay, cwd, "WORKTREE", "HEAD")
    assert "+value = 2" in str(staged["diff"]) and "+value = 3" not in str(staged["diff"])
    assert "-value = 2" in str(unstaged["diff"]) and "+value = 3" in str(unstaged["diff"])
    assert "-value = 1" in str(worktree["diff"]) and "+value = 3" in str(worktree["diff"])


def test_renamed_deleted_and_untracked(tmp_path: Path) -> None:
    cwd = repository(tmp_path / "repo")
    deleted = cwd / "deleted.txt"
    deleted.write_text("delete me")
    git(cwd, "add", ".")
    git(cwd, "commit", "-qm", "deletion base")
    git(cwd, "mv", "sample.py", "renamed.py")
    deleted.unlink()
    (cwd / "untracked.txt").write_text("new content\n")
    relay = Relay(catalog=standard_catalog(roots=(cwd,)))
    found = scope(relay, cwd, "WORKTREE", "HEAD", True)
    assert set(cast(list[str], found["changed_files"])) == {"renamed.py", "untracked.txt"}
    assert found["deleted_files"] == ["deleted.txt"]
    changes = cast(list[Context], found["changes"])
    assert any(
        c["old_file"] == "sample.py" and c["file"] == "renamed.py"
        for c in changes
        if "old_file" in c
    )
    assert {"file": "untracked.txt", "start": 1, "count": 1} in cast(
        list[Context], found["changed_hunks"]
    )


def test_scope_changes_during_derivation_reject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import openverify.standard.git as adapter

    cwd = repository(tmp_path / "repo")
    other = cwd / "other.py"
    other.write_text("value = 1\n")
    git(cwd, "add", ".")
    git(cwd, "commit", "-qm", "second file")
    (cwd / "sample.py").write_text("value = 2\n")
    original = adapter.git
    changed = False

    async def racing(argv: list[str], path: Path) -> str:
        nonlocal changed
        result = await original(argv, path)
        if "--name-status" in argv and not changed:
            changed = True
            other.write_text("print('must be checked')\n")
        return result

    monkeypatch.setattr(adapter, "git", racing)
    from openverify.relay.templates import code_graph

    run = Relay(catalog=standard_catalog(roots=(cwd,))).run_sync(
        code_graph(), inputs={"cwd": str(cwd), "base": "HEAD"}
    )
    assert run.results["git"].execution_outcome == "ERROR"
    assert "changed while deriving" in str(run.results["git"].output)
