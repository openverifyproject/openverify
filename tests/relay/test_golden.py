"""Expectations authored independently from runtime output; no engine golden edits."""

import json
from pathlib import Path

from openverify import Relay, parse_definition, parse_run_record


def test_current_binding_golden() -> None:
    root = Path(__file__).resolve().parents[2]
    fixture = json.loads((Path(__file__).parent / "fixtures/text-golden.json").read_bytes())
    definition = parse_definition((root / fixture["definition"]).read_bytes())
    for case in fixture["cases"]:
        run = Relay().run_sync(definition, inputs=case["inputs"])
        assert {n: r.verdict for n, r in run.results.items()} == case["verdicts"]
        assert [n.state for n in run.record.nodes] == case["states"]
        assert {n: b.model_dump() for n, b in run.record.provider_bindings.items()} == fixture[
            "provider_bindings"
        ]
        assert parse_run_record(run.to_json()) == run.record
