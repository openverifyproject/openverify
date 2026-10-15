"""Authorized filesystem observations with explicit size, encoding, and identity."""

import asyncio
import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context
from openverify.standard.common import ARRAY, OBJECT, STRING, STRINGS, object_schema, standard


@dataclass(frozen=True)
class FileAccess:
    roots: tuple[Path, ...]
    max_bytes: int = 2 * 1024 * 1024
    max_files: int = 10000

    def __post_init__(self) -> None:
        if (
            not self.roots
            or type(self.max_bytes) is not int
            or type(self.max_files) is not int
            or self.max_bytes < 1
            or self.max_files < 1
        ):
            raise ValueError("FileAccess requires roots and positive integer byte/file limits")

    def path(self, value: str, *, base: Path | None = None) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            if base is None:
                if len(self.roots) != 1:
                    raise ValueError("Relative paths require exactly one configured root")
                base = self.roots[0]
            candidate = base / candidate
        resolved = candidate.resolve()
        if not any(resolved.is_relative_to(root.resolve()) for root in self.roots):
            raise PermissionError("Path is outside authorized roots")
        return resolved

    def read(self, path: Path) -> tuple[bytes, Context]:
        path = self.path(str(path))
        with path.open("rb") as stream:
            content = stream.read(self.max_bytes + 1)
        if len(content) > self.max_bytes:
            raise ValueError(f"File exceeds configured {self.max_bytes} byte limit")
        return content, {
            "path": str(path),
            "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content),
        }


def filesystem_providers(access: FileAccess):
    async def read_text(inputs: Context, config: Context) -> Context:
        data, identity = await asyncio.to_thread(
            access.read, access.path(cast(str, inputs["file"]))
        )
        if b"\x00" in data:
            raise ValueError("Binary file is not UTF-8 document content; use read_file")
        return {"text": data.decode("utf-8"), "identity": identity}

    async def read_file(inputs: Context, config: Context) -> Context:
        data, identity = await asyncio.to_thread(
            access.read, access.path(cast(str, inputs["file"]))
        )
        return {"base64": base64.b64encode(data).decode("ascii"), "identity": identity}

    async def select(inputs: Context, config: Context) -> Context:
        directory = access.path(cast(str, inputs["directory"]))
        mode = config["mode"]
        if mode == "files":
            paths = [
                access.path(name, base=directory)
                for name in cast(list[str], config.get("files", []))
            ]
            if any(not path.is_file() for path in paths):
                raise FileNotFoundError("Explicit selection contains a missing or non-file path")
        elif mode in ("glob", "directory"):
            pattern = cast(str, config.get("glob", "**/*")) if mode == "glob" else "**/*"
            paths: list[Path] = []
            for path in directory.glob(pattern):
                path = access.path(str(path))
                if path.is_file():
                    paths.append(path)
                if len(paths) > access.max_files:
                    raise ValueError("File selection exceeds configured limit")
        else:
            raise ValueError("Unknown file selection mode")
        if len(paths) > access.max_files:
            raise ValueError("File selection exceeds configured limit")
        return {"files": cast(JsonValue, sorted(str(path) for path in paths))}

    return [
        standard(
            "read_text", "DERIVE", {"file": STRING}, {"text": STRING, "identity": OBJECT}, read_text
        ),
        standard(
            "read_file",
            "DERIVE",
            {"file": STRING},
            {"base64": STRING, "identity": OBJECT},
            read_file,
        ),
        standard(
            "select_files",
            "DERIVE",
            {"directory": STRING},
            {"files": ARRAY},
            select,
            config=object_schema(
                {
                    "mode": {"enum": ["files", "glob", "directory"]},
                    "files": STRINGS,
                    "glob": STRING,
                },
                optional={"files", "glob"},
            ),
        ),
    ]
