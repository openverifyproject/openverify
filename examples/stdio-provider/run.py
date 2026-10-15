"""Invoke the real external provider; optionally export usable trusted CLI config."""

import argparse
import json
import runpy
import sys
from pathlib import Path
from typing import cast

from openverify import Graph, Relay
from openverify.provider import wire_data
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.adapters.stdio import StdioTransport
from openverify.relay.providers import FunctionProvider


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-dir", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    namespace = runpy.run_path(str(here.parent / "custom-provider/check.py"))
    implementation = cast(FunctionProvider, namespace["prohibited_phrase"])
    graph = cast(Graph, namespace["graph"]())
    argv = (sys.executable, str(here / "provider.py"))
    catalog = Catalog()
    catalog.register_transport(implementation.manifest(), StdioTransport(argv, str(here)))
    result = Relay(catalog=catalog).run_sync(graph, inputs={"text": "Release TBD"})
    print(result.to_json())
    assert result.results["phrase"].verdict == "FAIL"
    if args.export_dir:
        directory = cast(Path, args.export_dir)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "graph.json").write_text(graph.to_json(), encoding="utf-8")
        (directory / "inputs.json").write_text(
            json.dumps({"text": "Release TBD"}), encoding="utf-8"
        )
        (directory / "providers.json").write_text(
            json.dumps(
                {
                    "stdio": [
                        {
                            "argv": list(argv),
                            "cwd": str(here),
                            "manifest": wire_data(implementation.manifest()),
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
