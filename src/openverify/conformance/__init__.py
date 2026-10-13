"""Run a portable manifest using this SDK; no engine execution is required."""

import json
from pathlib import Path

from openverify.errors import ProtocolError
from openverify.validation import parse_object


def check_manifest(directory: Path) -> list[str]:
    failures: list[str] = []
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    for case in manifest["cases"]:
        try:
            parse_object(case["object_type"], (directory / case["input"]).read_bytes())
            code = None
        except ProtocolError as exc:
            code = exc.code
        if code != case.get("error_code"):
            failures.append(case["id"])
    return failures
