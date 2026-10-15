"""Real Git/Ruff/ast-grep/pytest/command/filesystem acceptance, no mock tools."""

import asyncio
import subprocess
import sys
from pathlib import Path

from openverify import Graph, Relay, parse_run_record
from openverify.authoring import constant
from openverify.model import Context
from openverify.relay.templates import code_graph, text_graph
from openverify.standard import standard_catalog
from openverify.standard.command import Command, command_provider
from openverify.standard.common import OBJECT, STRING


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=directory, text=True, stderr=subprocess.STDOUT
    )


def repository(path: Path) -> Path:
    path.mkdir()
    git(path, "init", "-q")
    git(path, "config", "user.name", "Relay Test")
    git(path, "config", "user.email", "relay@example.invalid")
    (path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    git(path, "add", ".")
    git(path, "commit", "-qm", "base")
    return path


def test_real_code_fail_fix_pass_and_changed_span_scoping(tmp_path: Path) -> None:
    cwd = repository(tmp_path / "repo")
    source = cwd / "sample.py"
    source.write_text("import os\nprint('violation')\n", encoding="utf-8")
    relay = Relay(catalog=standard_catalog(roots=(cwd,)))
    inputs: Context = {"cwd": str(cwd), "base": "HEAD"}
    failed = relay.run_sync(code_graph(), inputs=inputs)
    assert failed.results["all"].verdict == "FAIL", failed.to_json()
    assert failed.results["ruff"].evidence[0].structured_data is not None
    assert failed.results["no_ast_violations"].evidence[0].structured_data == {
        "file": "sample.py",
        "line": 2,
        "column": 1,
        "end_line": 2,
        "end_column": 19,
        "code": "ast_pattern",
        "text": "print('violation')",
    }
    candidate = failed.record.nodes[0].information["candidate"]
    assert (
        isinstance(candidate, dict) and candidate["head"] == git(cwd, "rev-parse", "HEAD").strip()
    )
    source.write_text("value = 2\n", encoding="utf-8")
    passed = relay.run_sync(code_graph(), inputs=inputs)
    assert passed.results["all"].verdict == "PASS", passed.to_json()
    source.write_text("import os\n\nvalue = 1\n", encoding="utf-8")
    git(cwd, "add", ".")
    git(cwd, "commit", "-qm", "preexisting lint")
    source.write_text("import os\n\nvalue = 2\n", encoding="utf-8")
    files = relay.run_sync(code_graph(), inputs=inputs)
    spans = relay.run_sync(code_graph(changed_spans=True), inputs=inputs)
    assert files.results["all"].verdict == "FAIL"
    assert spans.results["all"].verdict == "PASS", spans.to_json()
    assert parse_run_record(spans.to_json()) == spans.record


def test_text_document_actual_files_missing_binary_large_and_path_scope(tmp_path: Path) -> None:
    file = tmp_path / "release-notes.md"
    relay = Relay(catalog=standard_catalog(roots=(tmp_path,)))
    file.write_text("Migration TODO", encoding="utf-8")
    assert (
        relay.run_sync(text_graph(document=True), inputs={"file": str(file)}).results["all"].verdict
        == "FAIL"
    )
    file.write_text("Migration\nRollback", encoding="utf-8")
    assert (
        relay.run_sync(text_graph(document=True), inputs={"file": str(file)}).results["all"].verdict
        == "PASS"
    )
    for content in (b"\x00binary", b"a" * (2 * 1024 * 1024 + 1)):
        file.write_bytes(content)
        assert (
            relay.run_sync(text_graph(document=True), inputs={"file": str(file)})
            .results["read"]
            .execution_outcome
            == "ERROR"
        )
    for path in (tmp_path / "missing", tmp_path.parent / "outside"):
        assert (
            relay.run_sync(text_graph(document=True), inputs={"file": str(path)})
            .results["read"]
            .execution_outcome
            == "ERROR"
        )


def test_command_capture_host_observation_and_pytest(tmp_path: Path) -> None:
    catalog = standard_catalog(roots=(tmp_path,))
    catalog.register(
        command_provider(Command((sys.executable, "-c", "print('observed')"), tmp_path))
    )
    graph = Graph("command")
    observed = graph.derive("observe", "openverify.command", outputs={"observation": OBJECT})
    graph.evaluate(
        "verify",
        "openverify.command_check",
        inputs={"observation": observed["observation"]},
        config={"exit_code": 0, "stdout": "observed"},
    )
    result = Relay(catalog=catalog).run_sync(graph, inputs={})
    assert result.results["verify"].verdict == "PASS"
    external = Graph("host-output")
    data = external.input("observation", OBJECT)
    external.evaluate(
        "verify", "openverify.command_check", inputs={"observation": data}, config={"exit_code": 0}
    )
    assert (
        Relay()
        .run_sync(
            external, inputs={"observation": {"returncode": 1, "stdout": "", "stderr": "failed"}}
        )
        .results["verify"]
        .verdict
        == "FAIL"
    )
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_example():\n    assert False\n")
    tests = Graph("tests")
    tests.evaluate(
        "tests",
        "openverify.pytest",
        inputs={"cwd": constant(str(tmp_path), STRING)},
        config={"tests": []},
    )
    relay = Relay(catalog=catalog)
    assert relay.run_sync(tests, inputs={}).results["tests"].verdict == "FAIL"
    test_file.write_text("def test_example():\n    assert True\n")
    assert relay.run_sync(tests, inputs={}).results["tests"].verdict == "PASS"


def test_multi_agent_real_worktrees_and_stale_detection(tmp_path: Path) -> None:
    cwd = repository(tmp_path / "repo")
    worktree = tmp_path / "agent-b"
    git(cwd, "worktree", "add", "-qb", "agent-b", str(worktree))
    (cwd / "sample.py").write_text("print('only A')\n")
    (worktree / "sample.py").write_text("value = 2\n")
    relay = Relay(catalog=standard_catalog(roots=(tmp_path,)))

    async def scenario():
        a, b = await asyncio.gather(
            relay.run(code_graph(), inputs={"cwd": str(cwd), "base": "HEAD"}),
            relay.run(
                code_graph(changed_spans=True), inputs={"cwd": str(worktree), "base": "HEAD"}
            ),
        )
        assert a.results["all"].verdict == "FAIL"
        assert b.results["all"].verdict == "PASS"
        ca = a.record.nodes[0].information["candidate"]
        cb = b.record.nodes[0].information["candidate"]
        assert ca != cb
        return ca

    candidate = asyncio.run(scenario())
    (cwd / "sample.py").write_text("value = 3\n")
    graph = Graph("staleness")
    graph.evaluate(
        "fresh",
        "openverify.candidate_unchanged",
        inputs={"cwd": constant(str(cwd)), "candidate": constant(candidate)},
    )
    assert relay.run_sync(graph, inputs={}).results["fresh"].verdict == "FAIL"
    # A newly changed/untracked path outside the captured file list is stale too.
    (cwd / "sample.py").write_text("print('only A')\n")
    (cwd / "new.py").write_text("value = 'new scope'\n")
    assert relay.run_sync(graph, inputs={}).results["fresh"].verdict == "FAIL"
