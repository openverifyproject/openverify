"""Host-authorized executable paths and file scopes for real OSS tool CLIs."""

import os
import shutil
import sysconfig
from dataclasses import dataclass
from pathlib import Path

from openverify.standard.filesystem import FileAccess


@dataclass(frozen=True)
class Tools:
    access: FileAccess
    ruff: str | None = None
    pytest: str | None = None
    astgrep: str | None = None

    def executable(self, name: str) -> str:
        value = {"ruff": self.ruff, "pytest": self.pytest, "astgrep": self.astgrep}[name]
        if value is None:
            instructions = {
                "ruff": "pip install ruff",
                "pytest": "pip install pytest",
                "astgrep": "npm install -g @ast-grep/cli",
            }[name]
            raise FileNotFoundError(
                f"{name} is not configured/installed. Install with: {instructions}"
            )
        return value

    def files(self, cwd: str, files: list[str]) -> tuple[Path, list[str]]:
        root = self.access.path(cwd)
        selected: list[str] = []
        for name in files:
            path = self.access.path(name, base=root)
            if not path.is_relative_to(root):
                raise PermissionError("Tool file is outside requested cwd")
            if path.is_file():
                selected.append(str(path))
        return root, selected


def installed_tools(access: FileAccess) -> Tools:
    # Executable lookup is trusted host composition, never graph-authored argv.
    path = sysconfig.get_path("scripts") + os.pathsep + os.environ.get("PATH", "")
    return Tools(
        access,
        shutil.which("ruff", path=path),
        shutil.which("pytest", path=path),
        shutil.which("ast-grep", path=path),
    )
