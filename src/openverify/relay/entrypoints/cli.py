"""Human and machine CLI; diagnostics exclusively on stderr in JSON mode."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import cast

from openverify.errors import ProtocolError
from openverify.inspection import inspect_definition
from openverify.json_schema import validate_value
from openverify.model import Context, ProviderBinding, RunRecord
from openverify.provider import parse_provider_manifest, wire_data
from openverify.relay import Relay, RuntimeConfig
from openverify.relay.adapters.catalog import Catalog
from openverify.relay.adapters.stdio import StdioTransport
from openverify.relay.templates import templates
from openverify.serialization import decode, to_data
from openverify.standard import standard_catalog
from openverify.standard.common import OBJECT, STRING, STRINGS, object_schema
from openverify.validation import parse_definition, parse_object


def read_json(path: str):
    return decode(sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes())


def configured_catalog(path: str | None, roots: list[str]) -> Catalog:
    catalog = standard_catalog(roots=tuple(Path(p).resolve() for p in roots) if roots else None)
    if path is None:
        return catalog
    raw = read_json(path)
    validate_value(
        object_schema(
            {
                "stdio": {
                    "type": "array",
                    "items": object_schema(
                        {
                            "argv": {"type": "array", "items": STRING, "minItems": 1},
                            "cwd": STRING,
                            "manifest": OBJECT,
                            "env": {"type": "object", "additionalProperties": STRING},
                        },
                        optional={"env"},
                    ),
                },
                "entry_points": STRINGS,
            },
            optional={"stdio", "entry_points"},
        ),
        raw,
        "PROVIDER_CONFIG",
    )
    assert isinstance(raw, dict)
    for item in cast(list[Context], raw.get("stdio", [])):
        manifest = parse_provider_manifest(item["manifest"])
        argv = cast(list[str], item["argv"])
        cwd = cast(str, item["cwd"])
        if not Path(cwd).is_absolute() or not argv:
            raise ValueError("Provider argv/cwd must be explicit")
        env = cast(dict[str, str] | None, item.get("env"))
        catalog.register_transport(manifest, StdioTransport(tuple(argv), cwd, env))
    catalog.load_entry_points(set(cast(list[str], raw.get("entry_points", []))))
    return catalog


def load_bindings(path: str | None) -> dict[str, ProviderBinding]:
    if path is None:
        return {}
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ValueError("Provider bindings must be an object")
    return {k: cast(ProviderBinding, parse_object("provider-binding", v)) for k, v in raw.items()}


def exit_code(record: RunRecord) -> int:
    if any(r.execution_outcome == "ERROR" for r in record.final_results.values()):
        return 2
    from openverify.lifecycle import reachable

    selected = {
        n: r
        for n, r in record.final_results.items()
        if not ((reachable(record.definition.graph, {n}) - {n}) & record.final_results.keys())
    }
    if any(r.verdict == "FAIL" for r in selected.values()):
        return 1
    if selected and all(r.verdict == "PASS" for r in selected.values()):
        return 0
    return 3


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenVerify DRAFT — Relay v0.1")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "inspect", "run"):
        command = commands.add_parser(name)
        command.add_argument("graph", help="VCP JSON path, '-' for stdin, or built-in graph name")
        if name == "validate":
            command.add_argument("--type", default="verification-definition")
        if name == "run":
            command.add_argument("--inputs", "--run-inputs", required=True)
            command.add_argument("--json", action="store_true")
            command.add_argument("--output", type=Path)
            command.add_argument("--opportunity-id")
            command.add_argument("--timeout", type=float, default=30)
            command.add_argument("--concurrency", type=int, default=8)
            command.add_argument("--providers", help="Trusted host configuration JSON")
            command.add_argument("--bindings", help="Trusted node-to-ProviderBinding JSON object")
            command.add_argument(
                "--root",
                action="append",
                default=[],
                help="Authorized filesystem root (repeatable)",
            )
    providers = commands.add_parser("providers")
    ps = providers.add_subparsers(dest="provider_command", required=True)
    ps.add_parser("list")
    ps.add_parser("inspect").add_argument("id")
    commands.add_parser("examples", aliases=["templates"])
    commands.add_parser("mcp")
    http = commands.add_parser("http")
    http.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        if args.command == "mcp":
            from openverify.relay.entrypoints.mcp import main as mcp_main

            return mcp_main()
        if args.command == "http":
            from openverify.relay.entrypoints.http import serve

            serve(args.port)
            return 0
        if args.command in ("examples", "templates"):
            print(
                json.dumps({name: inspect_definition(g.build()) for name, g in templates().items()})
            )
            return 0
        if args.command == "providers":
            manifests = [wire_data(p.manifest) for p in standard_catalog().providers()]
            if args.provider_command == "inspect":
                manifests = [m for m in manifests if m["provider_id"] == args.id]
                if not manifests:
                    raise ValueError("Unknown provider ID")
            print(json.dumps(manifests))
            return 0
        known = templates()
        raw = to_data(known[args.graph].build()) if args.graph in known else read_json(args.graph)
        if args.command == "validate":
            parse_object(args.type, raw)
            print(json.dumps({"valid": True}))
            return 0
        definition = parse_definition(raw)
        if args.command == "inspect":
            print(json.dumps(inspect_definition(definition)))
            return 0
        if args.graph == "-" and args.inputs == "-":
            raise ValueError("Only one input can consume stdin")
        inputs = read_json(args.inputs)
        if not isinstance(inputs, dict):
            raise ValueError("Run inputs must be an object")
        relay = Relay(
            catalog=configured_catalog(args.providers, args.root),
            config=RuntimeConfig(
                max_concurrency=args.concurrency,
                timeout=args.timeout,
                bindings=load_bindings(args.bindings),
            ),
        )
        run = asyncio.run(relay.run(definition, inputs=inputs, opportunity_id=args.opportunity_id))
        output = run.to_json()
        if args.output:
            args.output.write_text(output + "\n", encoding="utf-8")
        if args.json:
            print(output)
        else:
            print(f"Run {run.record.run_id}")
            for node in run.record.nodes:
                result = node.result
                status = (
                    (
                        result.verdict
                        or result.determination
                        or result.execution_outcome
                        or result.disposition
                    )
                    if result
                    else node.state
                )
                print(f"  {node.node_id}: {status}")
                for evidence in result.evidence if result else []:
                    print(f"    {evidence.message or json.dumps(to_data(evidence))}")
        return exit_code(run.record)
    except (ProtocolError, OSError, ValueError, ImportError) as exc:
        payload = (
            exc.as_dict()
            if isinstance(exc, ProtocolError)
            else {"code": "RELAY_ERROR", "message": str(exc)}
        )
        print(json.dumps(payload), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
