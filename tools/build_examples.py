"""Domain-neutral runnable examples using only explicitly registered local demos."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
base = json.loads((ROOT / "examples/prose/definition.json").read_text(encoding="utf-8"))


def write(path, data):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


prose = copy.deepcopy(base)
prose["graph"]["nodes"].insert(
    0,
    {
        "id": "derive-length",
        "kind": "DERIVE",
        "executor_ref": "demo.length",
        "config": {"key": "text", "output_key": "length"},
    },
)
prose["graph"]["edges"].insert(0, {"from_node": "derive-length", "to_node": "length"})
write("examples/prose/definition.json", prose)
write("examples/prose/context.json", {"text": "Careful claims help readers."})
generic = copy.deepcopy(base)
generic.update(
    id="temperature-envelope",
    subject={"id": "reading-1", "type": "application/json", "locator": {"sensor": "local-mock"}},
    criterion={
        "id": "temperature-range",
        "description": "Temperature is within the declared envelope.",
    },
)
generic["graph"] = {
    "nodes": [
        {
            "id": "envelope",
            "kind": "EVALUATE",
            "executor_ref": "demo.range",
            "config": {"key": "temperature", "minimum": 18, "maximum": 25},
        }
    ],
    "edges": [],
}
write("examples/generic/definition.json", generic)
write("examples/generic/context.json", {"temperature": 21.5})
ai = copy.deepcopy(base)
ai.update(
    id="answer-review",
    subject={"id": "answer-1", "type": "text/plain", "locator": {"host_key": "answer"}},
    criterion={
        "id": "answer-acceptability",
        "description": "The answer has the requested form and receives review.",
    },
)
unknown = {
    "protocol": "draft",
    "disposition": "EXECUTED",
    "execution_outcome": "SUCCESS",
    "applicability": "APPLICABLE",
    "determination": "UNKNOWN",
}
passed = {**unknown, "determination": "KNOWN", "verdict": "PASS"}
ai["graph"] = {
    "nodes": [
        {
            "id": "form",
            "kind": "EVALUATE",
            "executor_ref": "demo.regex",
            "config": {"key": "answer", "pattern": "^Answer:", "must_match": True},
        },
        {
            "id": "mock-judge",
            "kind": "EVALUATE",
            "executor_ref": "demo.constant",
            "config": {"result": unknown},
        },
        {
            "id": "escalate",
            "kind": "CONTROL",
            "executor_ref": "demo.unknown-route",
            "config": {"destination": "human-review"},
        },
        {
            "id": "human-review",
            "kind": "EVALUATE",
            "executor_ref": "demo.constant",
            "config": {
                "result": {
                    **passed,
                    "evidence": [{"message": "Mock reviewer accepted the response."}],
                }
            },
        },
    ],
    "edges": [
        {"from_node": "form", "to_node": "escalate"},
        {"from_node": "mock-judge", "to_node": "escalate"},
        {
            "from_node": "escalate",
            "to_node": "human-review",
            "guard": {
                "node_id": "escalate",
                "field": "decision_destination",
                "value": "human-review",
            },
        },
    ],
}
write("examples/ai-output/definition.json", ai)
write(
    "examples/ai-output/context.json", {"answer": "Answer: the provided evidence is inconclusive."}
)
