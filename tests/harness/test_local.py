# pyright: basic
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

from openverify_code import check as code_check
from openverify_english import check as english_check

from openverify.relay.local import changed
from openverify.validation import parse_result


def command(root: Path, *argv: str) -> None:
    subprocess.run(argv, cwd=root, check=True, capture_output=True)


def repository(tmp_path: Path) -> Path:
    command(tmp_path, "git", "init", "-q")
    command(tmp_path, "git", "config", "user.email", "test@example.invalid")
    command(tmp_path, "git", "config", "user.name", "Test")
    (tmp_path / "openverify.toml").write_text(
        '[rules.ruff]\nselect = ["F"]\n[rules.ruff-format]\nenabled = false\n',
        encoding="utf-8",
    )
    (tmp_path / "file with space.py").write_text("value = 1\n", encoding="utf-8")
    command(tmp_path, "git", "add", ".")
    command(tmp_path, "git", "commit", "-qm", "initial")
    return tmp_path


def test_staged_bytes_win_over_unstaged_fix(tmp_path: Path) -> None:
    root = repository(tmp_path)
    path = root / "file with space.py"
    path.write_text("import os\nvalue = 1\n", encoding="utf-8")
    command(root, "git", "add", "file with space.py")
    path.write_text("value = 1\n", encoding="utf-8")
    assert code_check(root, changed(root, True), True)["status"] == "FAIL"
    assert code_check(root, changed(root, False))["status"] == "PASS"
    command(root, "git", "add", "file with space.py")
    assert code_check(root, changed(root, True), True)["status"] == "PASS"


def test_staged_project_tool_config_wins(tmp_path: Path) -> None:
    root = repository(tmp_path)
    (root / "pyproject.toml").write_text("[tool.ruff.lint]\nselect = ['F']\n", encoding="utf-8")
    source = root / "file with space.py"
    source.write_text("import os\nvalue = 1\n", encoding="utf-8")
    command(root, "git", "add", "pyproject.toml", "file with space.py")
    (root / "pyproject.toml").write_text("[tool.ruff.lint]\nignore = ['F401']\n", encoding="utf-8")
    assert code_check(root, changed(root, True), True)["status"] == "FAIL"


def test_partially_staged_file_uses_index_bytes(tmp_path: Path) -> None:
    root = repository(tmp_path)
    source = root / "partial.py"
    source.write_text("value = 1\nother = 2\n", encoding="utf-8")
    command(root, "git", "add", "partial.py")
    command(root, "git", "commit", "-qm", "add partial file")
    source.write_text("import os\nvalue = 1\nother = 3\n", encoding="utf-8")
    patch = (
        "diff --git a/partial.py b/partial.py\n"
        "--- a/partial.py\n+++ b/partial.py\n"
        "@@ -1,2 +1,3 @@\n+import os\n value = 1\n other = 2\n"
    )
    subprocess.run(
        ["git", "apply", "--cached", "-"],
        cwd=root,
        input=patch.encode(),
        check=True,
        capture_output=True,
    )
    assert code_check(root, changed(root, True), True)["status"] == "FAIL"
    assert (root / "partial.py").read_text(encoding="utf-8").endswith("other = 3\n")


def test_cli_staged_json_and_exit_codes(tmp_path: Path) -> None:
    root = repository(tmp_path)
    source = root / "file with space.py"
    source.write_text("import os\nvalue = 1\n", encoding="utf-8")
    command(root, "git", "add", "file with space.py")
    source.write_text("value = 1\n", encoding="utf-8")
    repository_root = Path(__file__).resolve().parents[2]
    environment = {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            str(repository_root / part)
            for part in ("src", "packages/code/src", "packages/english/src")
        ),
    }
    argv = [sys.executable, "-m", "openverify.relay.entrypoints.cli", "code", "check"]
    staged = subprocess.run(
        [*argv, "--staged", "--json", "--root", str(root)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
    )
    working = subprocess.run(
        [*argv, "--changed", "--json", "--root", str(root)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
    )
    assert staged.returncode == 1
    assert json.loads(staged.stdout)["scope"] == "staged"
    assert working.returncode == 0


def test_staged_rename_and_deletion_scope(tmp_path: Path) -> None:
    root = repository(tmp_path)
    command(root, "git", "mv", "file with space.py", "renamed file.py")
    assert changed(root, True) == ["renamed file.py"]
    assert code_check(root, changed(root, True), True)["files"] == ["renamed file.py"]
    command(root, "git", "commit", "-qm", "rename")
    command(root, "git", "rm", "renamed file.py")
    assert changed(root, True) == []
    assert code_check(root, changed(root, True), True)["status"] == "PASS"


def test_english_excludes_markdown_fences(tmp_path: Path) -> None:
    (tmp_path / "openverify.toml").write_text(
        '[rules.phrase]\nprohibited = ["very unique"]\n', encoding="utf-8"
    )
    (tmp_path / "doc.md").write_text(
        "```\nvery unique —\n```\nThis is very unique —\n", encoding="utf-8"
    )
    report = english_check(tmp_path, ["doc.md"])
    assert report["status"] == "FAIL"
    assert len(report["findings"]) == 2
    assert all(f["line"] == 4 for f in report["findings"])
    assert report["rules"]["phrase"]["evidence"][0]["structured_data"]["rule_id"] == "phrase"
    parsed = parse_result(report["rules"]["phrase"])
    assert cast(dict, parsed.evidence[0].structured_data)["rule_id"] == "phrase"


def test_ruff_format_and_exclusion(tmp_path: Path) -> None:
    (tmp_path / "openverify.toml").write_text(
        '[profiles.code]\nexclude = ["skip.py"]\n[rules.ruff]\nenabled = false\n', encoding="utf-8"
    )
    (tmp_path / "check.py").write_text("x=1\n", encoding="utf-8")
    (tmp_path / "skip.py").write_text("y=2\n", encoding="utf-8")
    report = code_check(tmp_path, ["check.py", "skip.py"])
    assert report["status"] == "FAIL"
    assert report["files"] == ["check.py"]
    (tmp_path / "check.py").write_text("x = 1\n", encoding="utf-8")
    assert code_check(tmp_path, ["check.py", "skip.py"])["status"] == "PASS"


def test_ruff_format_reports_only_unformatted_files(tmp_path: Path) -> None:
    (tmp_path / "openverify.toml").write_text("[rules.ruff]\nenabled = false\n")
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "dirty.py").write_text("y=2\n", encoding="utf-8")
    report = code_check(tmp_path, ["clean.py", "dirty.py"])
    assert [item["file"] for item in report["findings"]] == ["dirty.py"]


def test_configured_pytest_failure_and_missing_tool(tmp_path: Path) -> None:
    pytest_exe = Path(sys.executable).with_name(
        "pytest.exe" if sys.platform == "win32" else "pytest"
    )
    (tmp_path / "test_sample.py").write_text("def test_failure():\n    assert False\n")
    (tmp_path / "openverify.toml").write_text(
        "[rules.ruff]\nenabled = false\n[rules.ruff-format]\nenabled = false\n"
        '[rules.pytest]\nenabled = true\ntests = ["test_sample.py"]\n'
        f"executable = '{pytest_exe}'\n",
        encoding="utf-8",
    )
    assert code_check(tmp_path, ["test_sample.py"])["status"] == "FAIL"
    (tmp_path / "test_sample.py").write_text("def test_success():\n    assert True\n")
    assert code_check(tmp_path, ["test_sample.py"])["status"] == "PASS"
    (tmp_path / "openverify.toml").write_text(
        "[rules.ruff]\nexecutable = 'missing-ruff-executable'\n"
        "[rules.ruff-format]\nenabled = false\n",
        encoding="utf-8",
    )
    assert code_check(tmp_path, ["test_sample.py"])["status"] == "ERROR"


def test_ast_grep_match(tmp_path: Path) -> None:
    executable = Path(sys.executable).with_name(
        "ast-grep.exe" if sys.platform == "win32" else "ast-grep"
    )
    if not executable.exists():
        import pytest

        pytest.skip("ast-grep is unavailable")
    (tmp_path / "check.py").write_text('print("hello")\n', encoding="utf-8")
    (tmp_path / "openverify.toml").write_text(
        "[rules.ruff]\nenabled = false\n[rules.ruff-format]\nenabled = false\n"
        '[rules.ast-grep]\nenabled = true\nlanguage = "python"\n'
        f"pattern = \"print($$$ARGS)\"\nexecutable = '{executable}'\n",
        encoding="utf-8",
    )
    report = code_check(tmp_path, ["check.py"])
    assert report["status"] == "FAIL"
    assert report["findings"][0]["rule_id"] == "ast-grep"


def test_english_terminology_replacement_and_clean_text(tmp_path: Path) -> None:
    (tmp_path / "openverify.toml").write_text(
        '[rules.terminology.terms]\nwhitelist = "allowlist"\n'
        '[rules.replacement.replacements]\nutilize = "use"\n',
        encoding="utf-8",
    )
    document = tmp_path / "note.md"
    document.write_text("Please utilize the whitelist.\n", encoding="utf-8")
    report = english_check(tmp_path, ["note.md"])
    assert {f["rule_id"] for f in report["findings"]} == {"terminology", "replacement"}
    document.write_text("Please use the allowlist.\n", encoding="utf-8")
    assert english_check(tmp_path, ["note.md"])["status"] == "PASS"
