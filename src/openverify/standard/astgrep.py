"""Whole-file ast-grep scanning. Changed-span filtering is a separate graph node."""

from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context
from openverify.relay.adapters.process import capture
from openverify.serialization import decode
from openverify.standard.common import ARRAY, STRING, STRINGS, object_schema, standard
from openverify.standard.tools import Tools


def astgrep_provider(tools: Tools):
    async def scan(inputs: Context, config: Context) -> Context:
        executable = tools.executable("astgrep")
        cwd, files = tools.files(cast(str, inputs["cwd"]), cast(list[str], inputs["files"]))
        if "rule_file" in config:
            if "pattern" in config or "language" in config:
                raise ValueError("Use either rule_file or language/pattern")
            rule = tools.access.path(cast(str, config["rule_file"]), base=cwd)
            args = ["scan", "--rule", str(rule)]
        else:
            language = cast(str, config.get("language", ""))
            pattern = cast(str, config.get("pattern", ""))
            if not language.isalnum() or not pattern:
                raise ValueError("Nonempty AST pattern and language required")
            args = ["run", "--lang", language, "--pattern", pattern]
        if not files:
            return {"findings": []}
        result = await capture(
            [
                executable,
                *args,
                "--json=compact",
                "--",
                *files,
            ],
            str(cwd),
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(f"ast-grep runner failed: {result.stderr}")
        entries = cast(list[dict[str, JsonValue]], decode(result.stdout or "[]"))
        findings: list[JsonValue] = []
        for entry in entries:
            location = cast(Context, entry["range"])
            start = cast(dict[str, int], location["start"])
            end = cast(dict[str, int], location["end"])
            path = Path(cast(str, entry["file"]))
            path = path if path.is_absolute() else cwd / path
            findings.append(
                {
                    "file": path.relative_to(cwd).as_posix(),
                    "line": start["line"] + 1,
                    "column": start["column"] + 1,
                    "end_line": end["line"] + 1,
                    "end_column": end["column"] + 1,
                    "code": entry.get("ruleId", "ast_pattern"),
                    "text": entry["text"],
                }
            )
        return {"findings": findings}

    return standard(
        "astgrep",
        "DERIVE",
        {"cwd": STRING, "files": STRINGS},
        {"findings": ARRAY},
        scan,
        config=object_schema(
            {"language": STRING, "pattern": STRING, "rule_file": STRING},
            optional={"language", "pattern", "rule_file"},
        ),
    )
