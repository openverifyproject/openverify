"""Explicit Git comparisons, working-content fingerprints, and staleness checks."""

import hashlib
import re
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, Result
from openverify.relay.adapters.process import capture
from openverify.standard.common import ARRAY, OBJECT, STRING, judge, object_schema, standard
from openverify.standard.filesystem import FileAccess


async def git(argv: list[str], cwd: Path) -> str:
    result = await capture(["git", "--no-pager", *argv], str(cwd))
    if result.returncode:
        raise RuntimeError(f"Git failed ({result.returncode}): {result.stderr}")
    return result.stdout


def fingerprints(access: FileAccess, cwd: Path, files: list[str]) -> Context:
    values: Context = {}
    for name in files:
        path = access.path(name, base=cwd)
        if path.exists():
            _, identity = access.read(path)
            values[name] = identity["sha256"]
        else:
            values[name] = None
    return values


def git_providers(access: FileAccess):
    async def scope(inputs: Context, config: Context) -> Context:
        cwd = access.path(cast(str, inputs["cwd"]))
        root = access.path((await git(["rev-parse", "--show-toplevel"], cwd)).strip())
        if cwd != root:
            raise ValueError("Git cwd must identify the repository/worktree root")
        head = (await git(["rev-parse", "HEAD"], cwd)).strip()
        branch = (
            (await git(["symbolic-ref", "-q", "--short", "HEAD"], cwd)).strip()
            if (await capture(["git", "symbolic-ref", "-q", "HEAD"], str(cwd))).returncode == 0
            else None
        )
        base = cast(str, inputs["base"])
        mode = config["mode"]
        if base.startswith("-"):
            raise ValueError("Git base must be a revision, not an option")
        resolved_base = None
        if mode == "UNSTAGED":
            if base:
                raise ValueError("UNSTAGED compares index to worktree: supply empty base")
            args: list[str] = []
        else:
            resolved_base = (await git(["rev-parse", "--verify", base + "^{commit}"], cwd)).strip()
            args = (["--cached"] if mode == "STAGED" else []) + [resolved_base]
        if mode not in ("WORKTREE", "STAGED", "UNSTAGED"):
            raise ValueError("Unsupported Git comparison")
        common = ["diff", "--no-ext-diff", "--no-textconv", "--find-renames", *args]
        raw = await git([*common, "--name-status", "-z", "--"], cwd)
        fields = iter(raw.rstrip("\0").split("\0") if raw else [])
        changes: list[JsonValue] = []
        paths: list[str] = []
        deleted: list[str] = []
        untracked_paths: list[str] = []
        for status in fields:
            original = next(fields)
            name = next(fields) if status.startswith(("R", "C")) else original
            access.path(name, base=cwd)
            changes.append({"status": status, "file": name, "old_file": original})
            (deleted if status == "D" else paths).append(name)
        if config.get("include_untracked"):
            untracked = (
                await git(["ls-files", "--others", "--exclude-standard", "-z"], cwd)
            ).rstrip("\0")
            for name in untracked.split("\0") if untracked else []:
                access.path(name, base=cwd)
                paths.append(name)
                untracked_paths.append(name)
                changes.append({"status": "?", "file": name})
        if len(paths) + len(deleted) > access.max_files:
            raise ValueError("Git scope exceeds configured file count")
        before = fingerprints(access, cwd, paths + deleted)
        hunks: list[JsonValue] = []
        for name in paths:
            patch = await git([*common, "--unified=0", "--", name], cwd)
            for match in re.finditer(
                r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", patch, re.MULTILINE
            ):
                hunks.append({"file": name, "start": int(match[1]), "count": int(match[2] or 1)})
            if any(
                isinstance(c, dict) and c.get("file") == name and c.get("status") == "?"
                for c in changes
            ):
                content, _ = access.read(access.path(name, base=cwd))
                hunks.append({"file": name, "start": 1, "count": len(content.splitlines())})
        diff = await git([*common, "--unified=0", "--"], cwd)
        after = fingerprints(access, cwd, paths + deleted)
        raw_after = await git([*common, "--name-status", "-z", "--"], cwd)
        untracked_after = (
            (await git(["ls-files", "--others", "--exclude-standard", "-z"], cwd)).rstrip("\0")
            if config["include_untracked"]
            else ""
        )
        if (
            before != after
            or raw_after != raw
            or sorted(untracked_after.split("\0") if untracked_after else [])
            != sorted(untracked_paths)
            or head != (await git(["rev-parse", "HEAD"], cwd)).strip()
        ):
            raise RuntimeError("Workspace changed while deriving Git scope; invoke again")
        candidate: Context = {
            "cwd": str(cwd),
            "worktree": str(root),
            "head": head,
            "branch": branch,
            "base": resolved_base,
            "mode": mode,
            "files": after,
            "untracked": cast(JsonValue, sorted(untracked_paths)),
            "include_untracked": config["include_untracked"],
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        }
        return {
            "changed_files": cast(JsonValue, paths),
            "changed_hunks": hunks,
            "diff": diff,
            "candidate": candidate,
            "changes": changes,
            "deleted_files": cast(JsonValue, deleted),
        }

    async def unchanged(inputs: Context, config: Context) -> Result:
        candidate = cast(Context, inputs["candidate"])
        cwd = access.path(cast(str, inputs["cwd"]))
        if str(cwd) != candidate["cwd"]:
            return judge([{"code": "candidate_worktree_mismatch"}])
        previous = cast(Context, candidate["files"])
        current = fingerprints(access, cwd, list(previous))
        head = (await git(["rev-parse", "HEAD"], cwd)).strip()
        mode = candidate["mode"]
        args = (
            []
            if mode == "UNSTAGED"
            else (["--cached"] if mode == "STAGED" else []) + [cast(str, candidate["base"])]
        )
        diff = await git(
            [
                "diff",
                "--no-ext-diff",
                "--no-textconv",
                "--find-renames",
                *args,
                "--unified=0",
                "--",
            ],
            cwd,
        )
        diff_digest = hashlib.sha256(diff.encode()).hexdigest()
        untracked = []
        if candidate["include_untracked"]:
            names = (await git(["ls-files", "--others", "--exclude-standard", "-z"], cwd)).rstrip(
                "\0"
            )
            untracked = sorted(names.split("\0") if names else [])
        findings: list[JsonValue] = []
        if (
            previous != current
            or head != candidate["head"]
            or candidate["diff_sha256"] != diff_digest
            or candidate["untracked"] != untracked
        ):
            findings.append(
                {
                    "code": "stale_candidate",
                    "checked": candidate,
                    "current_files": current,
                    "current_head": head,
                }
            )
        return judge(findings)

    return [
        standard(
            "git_scope",
            "DERIVE",
            {"cwd": STRING, "base": STRING},
            {
                "changed_files": ARRAY,
                "changed_hunks": ARRAY,
                "diff": STRING,
                "candidate": OBJECT,
                "changes": ARRAY,
                "deleted_files": ARRAY,
            },
            scope,
            config=object_schema(
                {
                    "mode": {"enum": ["WORKTREE", "STAGED", "UNSTAGED"]},
                    "include_untracked": {"type": "boolean"},
                }
            ),
        ),
        standard(
            "candidate_unchanged", "EVALUATE", {"cwd": STRING, "candidate": OBJECT}, {}, unchanged
        ),
    ]
