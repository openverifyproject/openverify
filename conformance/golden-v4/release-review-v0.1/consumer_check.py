"""Run with the installed wheel's interpreter and -I, outside src imports."""

import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path

import openverify
from openverify import Graph, Relay
from openverify.authoring import constant


def main():
    package = Path(openverify.__file__).resolve()
    assert "site-packages" in package.parts, package
    graph = Graph("installed-consumer")
    graph.evaluate(
        "check",
        "openverify.text",
        inputs={"text": constant("hello")},
        config={"required": ["hello"]},
    )
    run = Relay().run_sync(graph, inputs={})
    assert run.results["check"].verdict == "PASS", run.results["check"]
    resources = package.parent
    schemas = sorted((resources / "data/schemas").glob("*.json"))
    provider = sorted((resources / "provider/data/schemas").glob("*.json"))
    assert len(schemas) == 24, len(schemas)
    assert len(provider) == 9, len(provider)
    assert (resources / "py.typed").is_file()
    assert (resources / "data/profile.json").is_file()
    cli_environment = dict(os.environ)
    cli_environment.pop("PYTHONPATH", None)
    cli_environment.pop("PYTHONHOME", None)
    launcher = Path(sys.executable).with_name("openverify.exe" if os.name == "nt" else "openverify")
    cli = subprocess.run(
        [str(launcher), "--help"],
        cwd=sys.prefix,
        env=cli_environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert cli.returncode == 0, (cli.stdout, cli.stderr)
    assert "usage:" in cli.stdout.lower(), cli.stdout
    print(
        json.dumps(
            {
                "status": "PASS",
                "python": sys.version,
                "import_path": str(package),
                "version": importlib.metadata.version("openverify"),
                "result": run.results["check"].verdict,
                "cli_exit": cli.returncode,
                "vcp_schema_roots": len(schemas),
                "provider_schema_roots": len(provider),
                "resource_hashes": {
                    str(p.relative_to(resources)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in schemas + provider
                },
                "scope": (
                    "Core wheel install, packaged resources, in-process standard text execution, "
                    "CLI help. Optional extras and other platforms are not covered."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
