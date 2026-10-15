"""Disposable real-tool and filesystem integration experiments."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

from tools.golden.build_baseline import node, definition, port, constant
from tools.golden.compare import equal, fields
from tools.golden.execution import AdapterGap, EnvironmentUnavailable


def tool(name):
    found = shutil.which(
        name, path=sysconfig.get_path("scripts") + os.pathsep + os.environ.get("PATH", "")
    )
    if not found:
        raise EnvironmentUnavailable("optional external executable absent: " + name)
    return found


def git(cwd, *args):
    return subprocess.run(
        [tool("git"), "-C", str(cwd), *args],
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


def repository(root):
    git(root, "init")
    git(root, "config", "user.email", "golden@example.invalid")
    git(root, "config", "user.name", "Golden fixture")
    (root / "sample.py").write_text("answer = 1\n", encoding="utf-8")
    git(root, "add", "sample.py")
    git(root, "commit", "-m", "golden fixture base")
    return git(root, "rev-parse", "HEAD")


async def invoke(capability, inputs, config, root, *, catalog=None):
    """Use published manifest schemas to construct an invocation, never an oracle."""
    from openverify import Relay
    from openverify.standard import standard_catalog

    catalog = catalog or standard_catalog(roots=(root,))
    advertised = [
        (p, c)
        for p in catalog.providers()
        for c in p.manifest.capabilities
        if c.capability_id == "openverify." + capability
    ]
    if not advertised:
        raise AssertionError("documented shipped capability not advertised: " + capability)
    p, c = advertised[0]
    kind = c.extensions.get("openverify.operation", {}).get("kind")
    if kind not in ("DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"):
        raise AdapterGap("manifest lacks advertised operation role for " + capability)
    input_properties = (
        c.input_schema.get("properties", {}) if isinstance(c.input_schema, dict) else {}
    )
    outputs = [
        {
            "name": name,
            "role": "RESULT"
            if name == "result"
            else "DECISION"
            if name == "decision"
            else "INFORMATION",
            "schema": schema,
        }
        for name, schema in c.output_schema.get("properties", {}).items()
    ]
    n = node(
        "operation",
        kind,
        [port(k, input_properties.get(k, True)) for k in inputs],
        {k: constant(v) for k, v in inputs.items()},
        outputs=outputs,
        config=config,
        capability="openverify." + capability,
    )
    if kind == "AGGREGATE":
        raise AdapterGap("standard aggregate requires graph membership fixture")
    run = await Relay(catalog=catalog).run(json.dumps(definition([n])), inputs={})
    return json.loads(run.to_json())


def success(record):
    equal("SUCCESS", record["nodes"][0]["state"])
    return record["nodes"][0]


def failed_execution(record):
    equal("ERROR", record["nodes"][0]["state"])
    equal("ERROR", record["nodes"][0]["result"]["execution_outcome"])


def verdict(record, expected):
    r = record["nodes"][0]["result"]
    equal("SUCCESS", r["execution_outcome"])
    equal(expected, r["verdict"])
    return r


async def filesystem(capability, variant, root):
    path = root / "document.txt"
    content = "Unicode é 😀\n"
    path.write_text(content, encoding="utf-8", newline="\n")
    if capability == "select_files":
        (root / "other.txt").write_text("other", encoding="utf-8")
        config = {"mode": variant}
        if variant == "files":
            config["files"] = ["other.txt", "document.txt"]
        if variant == "glob":
            config["glob"] = "*.txt"
        record = await invoke(capability, {"directory": str(root)}, config, root)
        equal(sorted([str(path), str(root / "other.txt")]), success(record)["information"]["files"])
        return record
    if variant == "missing":
        path.unlink()
    if variant == "binary":
        path.write_bytes(b"\x00\xff\x80")
    if variant in ("oversized", "bounded"):
        path.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    record = await invoke(capability, {"file": str(path)}, {}, root)
    if (
        variant in ("missing", "oversized", "bounded")
        or capability == "read_text"
        and variant == "binary"
    ):
        failed_execution(record)
    else:
        information = success(record)["information"]
        if capability == "read_text":
            equal(content, information["text"])
        else:
            equal(path.read_bytes().hex(), base64.b64decode(information["base64"]).hex())
        raw = path.read_bytes()
        fields(
            {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "path": str(path)},
            information["identity"],
        )
    return record


async def git_scope(variant, root):
    base = repository(root)
    (root / "sample.py").write_text("answer = 2\n", encoding="utf-8")
    mode = variant if variant in ("WORKTREE", "STAGED", "UNSTAGED") else "WORKTREE"
    if mode == "STAGED":
        git(root, "add", "sample.py")
    if variant == "untracked":
        (root / "new.py").write_text("new = 1\n", encoding="utf-8")
    if variant == "rename":
        git(root, "mv", "sample.py", "renamed.py")
    if variant == "deleted":
        (root / "sample.py").unlink()
    record = await invoke(
        "git_scope",
        {"cwd": str(root), "base": "" if mode == "UNSTAGED" else base},
        {"mode": mode, "include_untracked": variant == "untracked"},
        root,
    )
    data = success(record)["information"]
    if variant == "deleted":
        assert any(str(x).endswith("sample.py") for x in data["deleted_files"])
        assert not any(str(x).endswith("sample.py") for x in data["changed_files"])
    else:
        assert data["changed_files"], "changed file absent"
        assert data["changed_hunks"], "changed hunk absent"
        if variant == "untracked":
            assert any(str(x).endswith("new.py") for x in data["changed_files"])
        if variant == "rename":
            assert "renamed.py" in str(data["changes"])
    return record


async def candidate(variant, root):
    base = repository(root)
    captured = await invoke(
        "git_scope",
        {"cwd": str(root), "base": base},
        {"mode": "WORKTREE", "include_untracked": True},
        root,
    )
    snap = success(captured)["information"]["candidate"]
    if variant == "content_changed":
        (root / "sample.py").write_text("answer = 3\n", encoding="utf-8")
    if variant == "head_changed":
        (root / "sample.py").write_text("answer = 4\n", encoding="utf-8")
        git(root, "add", "sample.py")
        git(root, "commit", "-m", "new head")
    record = await invoke("candidate_unchanged", {"cwd": str(root), "candidate": snap}, {}, root)
    verdict(record, "PASS" if variant == "fresh" else "FAIL")
    return record


async def code_tool(capability, variant, root):
    tool("ast-grep" if capability == "astgrep" else capability)
    if capability == "ruff":
        (root / "sample.py").write_text(
            "import os\n" if variant == "violation" else "answer = 1\n", encoding="utf-8"
        )
        record = await invoke(
            capability,
            {"cwd": str(root), "files": [str(root / "sample.py")]},
            {"select": ["F401"]},
            root,
        )
    elif capability == "astgrep":
        (root / "sample.py").write_text(
            "print('debug')\n" if variant == "violation" else "answer = 1\n", encoding="utf-8"
        )
        record = await invoke(
            capability,
            {"cwd": str(root), "files": [str(root / "sample.py")]},
            {"language": "python", "pattern": "print($A)"},
            root,
        )
    else:
        (root / "test_example.py").write_text(
            "def test_value():\n    assert " + ("True" if variant == "pass" else "False") + "\n"
            if variant != "collection_error"
            else "not valid python !!!\n",
            encoding="utf-8",
        )
        record = await invoke(capability, {"cwd": str(root)}, {"tests": []}, root)
    if variant == "collection_error":
        failed_execution(record)
    else:
        if capability == "astgrep":
            findings = success(record)["information"]["findings"]
            equal(variant == "violation", bool(findings))
        else:
            verdict(record, "FAIL" if variant in ("violation", "fail") else "PASS")
        if variant == "violation":
            findings = record["nodes"][0]["information"]["findings"]
            assert findings and "sample.py" in json.dumps(findings)
            assert any(key in json.dumps(findings) for key in ("line", "start")), (
                "source coordinates absent"
            )
    return record


async def command(variant, root):
    from openverify.standard.command import Command, command_provider
    from openverify.standard import standard_catalog

    program = (
        "import sys; print('golden stdout'); print('golden stderr',file=sys.stderr); sys.exit(7)"
    )
    argv = (sys.executable, "-c", program)
    if variant == "argv":
        argv = (sys.executable, "-c", "import sys; print(sys.argv[1])", "literal ; & $(echo never)")
    if variant == "missing_executable":
        argv = (str(root / "nonexistent-executable"),)
    if variant == "bounded_output":
        argv = (sys.executable, "-c", "print('x'*8192)")
    if variant == "descendant_cleanup":
        child = "import os,threading; print(os.getpid(),flush=True); threading.Event().wait()"
        parent = (
            "import subprocess,sys; p=subprocess.Popen([sys.executable,'-c',"
            + repr(child)
            + "],stdout=subprocess.PIPE,stderr=subprocess.PIPE); print(p.stdout.readline().decode().strip(),flush=True)"
        )
        argv = (sys.executable, "-c", parent)
    catalog = standard_catalog(roots=(root,))
    catalog.register(
        command_provider(
            Command(argv, root, max_output_bytes=1024 if variant == "bounded_output" else 8192)
        )
    )
    record = await invoke("command", {}, {}, root, catalog=catalog)
    if variant in ("missing_executable", "bounded_output"):
        failed_execution(record)
    else:
        obs = success(record)["information"]["observation"]
        equal(list(argv), obs["argv"])
        if variant == "descendant_cleanup":
            pid = int(obs["stdout"].strip())
            await asyncio.to_thread(assert_process_terminated, pid)
        elif variant == "argv":
            equal("literal ; & $(echo never)", obs["stdout"].strip())
        else:
            equal(7, obs["returncode"])
            assert "golden stdout" in obs["stdout"] and "golden stderr" in obs["stderr"]
    return record


def assert_process_terminated(pid):
    """Independent OS handle check; readiness comes from the child's pipe message."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
        handle = kernel.OpenProcess(0x00100001, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return
            raise EnvironmentUnavailable("cannot inspect child process handle")
        try:
            status = kernel.WaitForSingleObject(handle, 3000)
            if status != 0:
                kernel.TerminateProcess(handle, 1)
                raise AssertionError("command descendant remained alive after cleanup")
        finally:
            kernel.CloseHandle(handle)
    elif hasattr(os, "pidfd_open"):
        import select

        try:
            descriptor = os.pidfd_open(pid)
        except ProcessLookupError:
            return
        try:
            if not select.select([descriptor], [], [], 3)[0]:
                os.kill(pid, 9)
                raise AssertionError("command descendant remained alive after cleanup")
        finally:
            os.close(descriptor)
    else:
        raise EnvironmentUnavailable(
            "no supported independent process-lifetime observation API on this platform"
        )


async def text(variant, root):
    if variant == "missing":
        try:
            record = await invoke("text", {}, {}, root)
        except Exception as exc:
            return {"rejection": getattr(exc, "code", type(exc).__name__)}
        failed_execution(record)
        return record
    inputs = {
        "text": "é😀 TODO\n"
        if variant == "unicode_offsets"
        else "Migration TODO"
        if variant == "fail"
        else "Migration Rollback"
    }
    config = {"required": ["Migration", "Rollback"], "prohibited": ["TODO"]}
    if variant == "unicode_offsets":
        config = {"prohibited": ["TODO"]}
    if variant == "terms_combine":
        inputs["required_terms"] = ["Additional"]
        config = {"required": ["Migration"]}
    record = await invoke("text", inputs, config, root)
    verdict(record, "FAIL" if variant in ("fail", "unicode_offsets", "terms_combine") else "PASS")
    if variant == "unicode_offsets":
        assert "TODO" in json.dumps(record["nodes"][0]["result"], ensure_ascii=False)
        # Coordinate field names are provider-owned; mandatory exact coordinate
        # comparison needs a published finding schema, not source-derived guesses.
    return record


async def structured(capability, variant, root):
    if capability == "json_parse":
        raw = {
            "valid": '{"value":[true,1,null]}',
            "duplicate": '{"a":1,"a":2}',
            "nonfinite": '{"a":NaN}',
            "malformed": "{oops",
        }[variant]
        record = await invoke(capability, {"text": raw}, {}, root)
        if variant == "valid":
            equal({"value": [True, 1, None]}, success(record)["information"]["value"])
        else:
            failed_execution(record)
    else:
        inputs = {
            "value": True if variant == "bool_number" else "value" if variant == "invalid" else 2
        }
        record = await invoke("schema", inputs, {"schema": {"type": "integer"}}, root)
        verdict(record, "PASS" if variant == "valid" else "FAIL")
    return record


async def scope(variant, root):
    # Published prose specifies coordinate semantics but not a complete wire
    # finding/range shape. Do not mine implementation helpers to invent it.
    if variant in ("changed_spans", "ast_ranges", "zero_deletion", "half_open_boundary"):
        raise AdapterGap(
            "precise finding/range fixture wire shape requires independent published profile adjudication: "
            + variant
        )
    record = await invoke(
        "scope",
        {"findings": [], "files": [], "ranges": []},
        {"mode": variant, **({"directory": str(root)} if variant == "directory" else {})},
        root,
    )
    equal([], success(record)["information"]["findings"])
    return record


async def experiment(payload):
    cap, variant = payload["capability"], payload["variant"]
    if payload.get("external_tool"):
        tool(payload["external_tool"])
    with tempfile.TemporaryDirectory(prefix="golden-standard-") as folder:
        root = Path(folder).resolve()
        if cap in ("read_text", "read_file", "select_files"):
            record = await filesystem(cap, variant, root)
        elif cap == "git_scope":
            record = await git_scope(variant, root)
        elif cap == "candidate_unchanged":
            record = await candidate(variant, root)
        elif cap in ("ruff", "pytest", "astgrep"):
            record = await code_tool(cap, variant, root)
        elif cap == "command":
            record = await command(variant, root)
        elif cap == "text":
            record = await text(variant, root)
        elif cap in ("json_parse", "schema"):
            record = await structured(cap, variant, root)
        elif cap == "scope":
            record = await scope(variant, root)
        elif cap == "no_findings":
            record = await invoke(
                cap, {"findings": [] if variant == "empty" else [{"code": "deliberate"}]}, {}, root
            )
            verdict(record, "PASS" if variant == "empty" else "FAIL")
        elif cap == "command_check":
            record = await invoke(
                cap,
                {
                    "observation": {
                        "returncode": 0 if variant == "pass" else 1,
                        "stdout": "",
                        "stderr": "",
                    }
                },
                {"exit_code": 0},
                root,
            )
            verdict(record, "PASS" if variant == "pass" else "FAIL")
        elif cap == "action_policy":
            targets = {
                "allowed": "tmp/item",
                "denied": "protected/item",
                "traversal": "tmp/../protected/item",
                "absolute": "/tmp/item",
            }
            record = await invoke(
                cap,
                {"action": "delete", "target": targets[variant], "allowed_prefixes": ["tmp"]},
                {},
                root,
            )
            verdict(record, "PASS" if variant == "allowed" else "FAIL")
        elif cap == "gate":
            from tools.golden.oracle import result

            record = await invoke(cap, {"checked": result(variant)}, {}, root)
            equal(
                "CONTINUE" if variant == "PASS" else "STOP_FAILURE",
                success(record)["decision"]["kind"],
            )
        elif cap == "aggregate":
            from tests.golden_current.adapters.public import reducer
            from tools.golden.oracle import EXCEPTIONAL, result

            record = await reducer(
                {
                    "members": [result("PASS"), result("PASS")],
                    "config": {"reducer": "ALL", "handling": dict.fromkeys(EXCEPTIONAL, "REJECT")},
                }
            )
            equal("PASS", record["outcome"]["output"]["result"]["verdict"])
        else:
            raise AdapterGap("standard capability " + cap)
        return {"verified": True, "observed": record}


async def security_experiment(variant):
    from openverify.standard import standard_catalog

    with (
        tempfile.TemporaryDirectory(prefix="golden-authorized-") as folder,
        tempfile.TemporaryDirectory(prefix="golden-outside-") as outside,
    ):
        root = Path(folder).resolve()
        other = Path(outside) / "secret.txt"
        other.write_text("outside", encoding="utf-8")
        if variant == "untrusted_command":
            catalog = standard_catalog(roots=(root,))
            assert all(
                c.capability_id != "openverify.command"
                for p in catalog.providers()
                for c in p.manifest.capabilities
            )
            return {"verified": True, "command_launcher_absent": True}
        if variant == "argv_no_shell":
            return {"verified": True, "record": await command("argv", root)}
        target = other
        if variant == "symlink_escape":
            target = root / "link.txt"
            try:
                target.symlink_to(other)
            except OSError as exc:
                raise EnvironmentUnavailable("host cannot create symlink: " + str(exc)) from exc
        record = await invoke("read_text", {"file": str(target)}, {}, root)
        failed_execution(record)
        return {"verified": True}


async def worktree_isolation():
    with tempfile.TemporaryDirectory(prefix="golden-worktrees-") as folder:
        root = Path(folder)
        repo = root / "repo"
        repo.mkdir()
        repository(repo)
        first, second = root / "first", root / "second"
        git(repo, "worktree", "add", "--detach", str(first))
        git(repo, "worktree", "add", "--detach", str(second))
        (first / "sample.py").write_text("first = True\n", encoding="utf-8")
        (second / "sample.py").write_text("second = 1\n", encoding="utf-8")
        a, b = await asyncio.gather(
            invoke("read_text", {"file": str(first / "sample.py")}, {}, first),
            invoke("read_text", {"file": str(second / "sample.py")}, {}, second),
        )
        equal("first = True\n", success(a)["information"]["text"])
        equal("second = 1\n", success(b)["information"]["text"])
        assert a["run_id"] != b["run_id"]
        return {"verified": True, "run_ids": [a["run_id"], b["run_id"]]}
