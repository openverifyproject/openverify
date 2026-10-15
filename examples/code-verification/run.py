"""Disposable real Git repository: Ruff + ast-grep violation, fix, PASS."""

import subprocess
import tempfile
from pathlib import Path

from openverify import Relay
from openverify.relay.templates import code_graph
from openverify.standard import standard_catalog


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="openverify-code-") as directory:
        root = Path(directory)

        def git(*args: str) -> None:
            subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

        git("init", "-q")
        git("config", "user.name", "OpenVerify Example")
        git("config", "user.email", "example@example.invalid")
        source = root / "sample.py"
        source.write_text("value = 1\n")
        git("add", ".")
        git("commit", "-qm", "base")
        source.write_text("import os\nprint('violation')\n")
        relay = Relay(catalog=standard_catalog(roots=(root,)))
        inputs = {"cwd": str(root), "base": "HEAD"}
        failed = relay.run_sync(code_graph(), inputs=inputs)
        print(failed.to_json())
        assert failed.results["all"].verdict == "FAIL"
        source.write_text("value = 2\n")
        passed = relay.run_sync(code_graph(), inputs=inputs)
        print(passed.to_json())
        assert passed.results["all"].verdict == "PASS"


if __name__ == "__main__":
    main()
