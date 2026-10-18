"""Non-normative local convenience commands using an explicit demo registry."""

import argparse
import json
from pathlib import Path
from typing import cast

from openverify.adapters.demo import demo_registry
from openverify.engine import Engine
from openverify.errors import ProtocolError
from openverify.inspection import inspect_definition
from openverify.model import Context
from openverify.serialization import decode, serialize
from openverify.validation import parse_definition, parse_object


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft Openverify local SDK/reference commands")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("file", type=Path)
    validate.add_argument("--type", default="verification-definition")
    inspect = commands.add_parser("inspect")
    inspect.add_argument("file", type=Path)
    run = commands.add_parser("run")
    run.add_argument("file", type=Path)
    run.add_argument("--run-inputs", type=Path, required=True)
    run.add_argument("--opportunity-id", required=True)
    run.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = cast(Path, args.file).read_bytes()
        if args.command == "validate":
            parse_object(args.type, data)
            print(json.dumps({"valid": True}))
        elif args.command == "inspect":
            print(json.dumps(inspect_definition(parse_definition(data)), indent=2))
        else:
            run_inputs = decode(cast(Path, args.run_inputs).read_bytes())
            if not isinstance(run_inputs, dict):
                raise ProtocolError("PROTOCOL_STRUCTURE", "Run inputs must be a mapping")
            record = Engine(demo_registry()).run(
                parse_definition(data),
                cast(Context, run_inputs),
                opportunity_id=args.opportunity_id,
            )
            output = serialize(record)
            if args.output:
                cast(Path, args.output).write_text(output + "\n", encoding="utf-8")
            else:
                print(output)
        return 0
    except ProtocolError as exc:
        print(json.dumps(exc.as_dict()))
        return 1
    except OSError as exc:
        print(json.dumps({"code": "IO_ERROR", "message": str(exc)}))
        return 1
