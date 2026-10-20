"""Git index materialization and local verification scope helpers."""
# pyright: basic

import fnmatch
import os
import subprocess
import tempfile
import tomllib
from contextlib import contextmanager
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Result
from openverify.serialization import to_data
from openverify.standard.common import judge


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode("utf-8", "replace").strip())
    return result.stdout


def paths(raw: bytes) -> list[str]:
    return [os.fsdecode(p) for p in raw.split(b"\0") if p]


def changed(root: Path, staged: bool) -> list[str]:
    args = ["diff", "--name-only", "-z", "--diff-filter=ACMRT"]
    if staged:
        args.append("--cached")
    else:
        args.append("HEAD")
    selected = paths(git(root, *args))
    if not staged:
        selected += paths(git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(set(selected))


@contextmanager
def scope(root: Path, staged: bool):
    if not staged:
        yield root
        return
    with tempfile.TemporaryDirectory(prefix=".openverify-index-", dir=root) as directory:
        target = Path(directory)
        for entry in git(root, "ls-files", "--stage", "-z").split(b"\0"):
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, oid, stage = metadata.split(b" ")
            path = Path(os.fsdecode(raw_path))
            if stage != b"0" or mode not in (b"100644", b"100755"):
                raise ValueError(f"Unsupported Git index entry: {os.fsdecode(raw_path)}")
            if path.is_absolute() or ".." in path.parts:
                raise ValueError("Unsafe Git index path")
            blob = git(root, "cat-file", "blob", oid.decode("ascii"))
            destination = target / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(blob)
            if mode == b"100755":
                destination.chmod(0o755)
        yield target


def configuration(root: Path) -> dict:
    path = root / "openverify.toml"
    return tomllib.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def selected_files(root: Path, names: list[str], profile: str, config: dict) -> list[str]:
    settings = config.get("profiles", {}).get(profile, {})
    includes = settings.get(
        "include", ["*.py", "*.pyi"] if profile == "code" else ["*.md", "*.txt"]
    )
    excludes = settings.get("exclude", [])
    output = []
    for name in names:
        if not (root / name).is_file():
            continue
        if not any(
            fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(Path(name).name, pattern)
            for pattern in includes
        ):
            continue
        if any(
            fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(Path(name).name, pattern)
            for pattern in excludes
        ):
            continue
        output.append(name)
    return output


def finding(rule: str, file: str, line: int, column: int, message: str, **extra) -> dict:
    return {
        "rule_id": rule,
        "file": file,
        "line": line,
        "column": column,
        "message": message,
        **extra,
    }


def run_rules(profile, root, names, staged, rules, evaluate):
    with scope(root, staged) as effective_root:
        config = configuration(effective_root)
        files = selected_files(effective_root, names, profile, config)
        outcomes = {}
        all_findings = []
        for rule in rules:
            settings = dict(config.get("rules", {}).get(rule, {}))
            settings["_staged"] = staged
            if settings.get("enabled", rule not in ("pytest", "ast-grep")) is False:
                continue
            try:
                found = evaluate(rule, effective_root, files, settings)
                result = judge(
                    found, observations=cast(JsonValue, {"scope": files, "staged": staged})
                )
                all_findings.extend(found)
            except (OSError, ValueError, RuntimeError, UnicodeError) as exc:
                result = Result(
                    disposition="EXECUTED", execution_outcome="ERROR", output={"error": str(exc)}
                )
            outcomes[rule] = to_data(result)
    statuses = [r.get("execution_outcome") for r in outcomes.values()]
    verdicts = [r.get("verdict") for r in outcomes.values()]
    status = "ERROR" if "ERROR" in statuses else "FAIL" if "FAIL" in verdicts else "PASS"
    return {
        "profile": profile,
        "scope": "staged" if staged else "working-tree",
        "status": status,
        "files": files,
        "rules": outcomes,
        "findings": all_findings,
    }
