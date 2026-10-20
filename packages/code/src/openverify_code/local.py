"""Python code rules owned by openverify-code."""
# pyright: basic

import json
import shutil
import subprocess
from pathlib import Path

from openverify.relay.local import finding, run_rules

RULES = {
    "ruff": "Ruff lint with project configuration",
    "ruff-format": "Ruff format check with project configuration",
    "pytest": "Configured project tests",
    "ast-grep": "Configured structural code pattern",
}


def run_command(argv: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=root, text=True, capture_output=True, encoding="utf-8")


def code_rule(rule: str, root: Path, files: list[str], settings: dict) -> list[dict]:
    for name in files:
        if b"\0" in (root / name).read_bytes():
            raise ValueError(f"Binary selected file: {name}")
    if rule == "pytest":
        tests = settings.get("tests")
        if not tests:
            return []
        if any(not isinstance(t, str) or t.startswith("-") for t in tests):
            raise ValueError("pytest tests must be explicit paths")
        executable = settings.get("executable") or shutil.which("pytest")
        if not executable:
            raise FileNotFoundError("pytest is required")
        pytest_config = []
        if settings.get("_staged"):
            candidate = next(
                (
                    root / name
                    for name in ("pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")
                    if (root / name).is_file()
                ),
                None,
            )
            if candidate is None:
                candidate = root / ".openverify-empty-pytest.ini"
                candidate.write_text("[pytest]\n", encoding="utf-8")
            pytest_config = ["-c", str(candidate)]
        result = run_command([executable, "-q", *pytest_config, "--", *tests], root)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"pytest exit {result.returncode}: {result.stderr}")
        return (
            []
            if result.returncode == 0
            else [finding(rule, "", 0, 0, "Tests failed", stdout=result.stdout[-8000:])]
        )
    if not files:
        return []
    if rule in ("ruff", "ruff-format"):
        executable = settings.get("executable") or shutil.which("ruff")
        if not executable:
            raise FileNotFoundError("Ruff is required")
        ruff_config = []
        if settings.get("_staged"):
            candidate = next(
                (
                    root / name
                    for name in ("ruff.toml", ".ruff.toml", "pyproject.toml")
                    if (root / name).is_file()
                ),
                None,
            )
            ruff_config = ["--config", str(candidate)] if candidate else ["--isolated"]
        if rule == "ruff":
            argv = [executable, "check", *ruff_config, "--output-format", "json"]
            if settings.get("select"):
                argv += ["--select", ",".join(settings["select"])]
            result = run_command([*argv, "--", *files], root)
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Ruff exit {result.returncode}: {result.stderr}")
            return [
                finding(
                    rule,
                    Path(item["filename"]).relative_to(root).as_posix(),
                    item["location"]["row"],
                    item["location"]["column"],
                    item["message"],
                    code=item["code"],
                )
                for item in json.loads(result.stdout)
            ]
        findings = []
        for name in files:
            result = run_command([executable, "format", *ruff_config, "--check", "--", name], root)
            if result.returncode not in (0, 1):
                raise RuntimeError(f"Ruff format exit {result.returncode}: {result.stderr}")
            if result.returncode == 1:
                findings.append(finding(rule, name, 1, 1, "Formatting differs"))
        return findings
    executable = settings.get("executable") or shutil.which("ast-grep")
    if not executable:
        raise FileNotFoundError("ast-grep is required")
    if "rule_file" in settings:
        argv = [executable, "scan", "--rule", settings["rule_file"]]
    elif settings.get("pattern") and settings.get("language"):
        argv = [executable, "run", "--lang", settings["language"], "--pattern", settings["pattern"]]
    else:
        return []
    result = run_command([*argv, "--json=compact", "--", *files], root)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"ast-grep exit {result.returncode}: {result.stderr}")
    return [
        finding(
            rule,
            item["file"],
            item["range"]["start"]["line"] + 1,
            item["range"]["start"]["column"] + 1,
            "Pattern matched",
            text=item["text"],
        )
        for item in json.loads(result.stdout or "[]")
    ]


def check(root: Path, names: list[str], staged: bool = False) -> dict:
    return run_rules("code", root, names, staged, RULES, code_rule)
