"""Deterministic, language-neutral cases derived from the written draft."""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


handling = dict.fromkeys(
    ["UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING"], "REJECT"
)
result = {
    "protocol": "draft",
    "disposition": "EXECUTED",
    "execution_outcome": "SUCCESS",
    "applicability": "APPLICABLE",
    "determination": "KNOWN",
    "verdict": "PASS",
}
definition = {
    "protocol": "draft",
    "id": "prose-criterion",
    "version": "1",
    "subject": {"id": "article-1", "type": "text/plain", "locator": {"host_key": "text"}},
    "criterion": {
        "id": "readable-prose",
        "description": "Contains no banned phrase and is nonempty.",
    },
    "judgment_schema": {},
    "execution_policy": {
        "activation": {"executor_ref": "MANUAL"},
        "selection": {"executor_ref": "EXPLICIT"},
        "admission": {"strategy": "ALWAYS"},
    },
    "graph": {
        "nodes": [
            {
                "id": "phrase",
                "kind": "EVALUATE",
                "executor_ref": "demo.regex",
                "config": {"key": "text", "pattern": "guaranteed cure", "must_match": False},
            },
            {
                "id": "length",
                "kind": "EVALUATE",
                "executor_ref": "demo.range",
                "config": {"key": "length", "minimum": 1, "maximum": 10000},
            },
            {
                "id": "all",
                "kind": "AGGREGATE",
                "executor_ref": "standard.aggregate",
                "config": {"reducer": "ALL", "handling": handling},
            },
        ],
        "edges": [
            {"from_node": "phrase", "to_node": "all"},
            {"from_node": "length", "to_node": "all"},
        ],
    },
}
cases = []


def case(id, kind, value, code=None, section="wire-format", stage="semantic"):
    folder = "invalid" if code else "valid"
    path = f"conformance/{folder}/{id}.json"
    write(path, value)
    expected = {"valid": code is None, **({"error_code": code} if code else {})}
    write(f"conformance/expected/{id}.json", expected)
    cases.append(
        {
            "id": id,
            "description": id.replace("-", " "),
            "object_type": kind,
            "input": f"{folder}/{id}.json",
            **expected,
            "stage": stage if code else "both",
            "expected": f"expected/{id}.json",
            "spec": f"spec/draft/{section}.md",
        }
    )


case("minimal-result", "result", result, section="result")
rich = {
    **result,
    "score": 0.9,
    "judgment": {"category": "acceptable"},
    "evidence": [{"message": "Observed directly", "locator": {"paragraph": 2}}],
    "usage": {"energy": {"unit": "J", "kind": "EXACT", "value": 4}},
    "severity": {"domain": "standard-draft", "label": "INFO"},
    "extensions": [
        {
            "namespace": "org.example:note",
            "version": "1",
            "required": False,
            "data": {"note": "retained"},
        }
    ],
}
case("rich-result", "result", rich, section="result")
case(
    "unknown-result",
    "result",
    {**result, "determination": "UNKNOWN", "verdict": None},
    section="result",
)
case("skipped-result", "result", {"protocol": "draft", "disposition": "SKIPPED"}, section="result")
case("simple-definition", "verification-definition", definition, section="meaning")
case("simple-graph", "graph", definition["graph"], section="composition")
case(
    "resource-range",
    "resource",
    {"unit": "s", "kind": "RANGE", "minimum": 1, "maximum": 3},
    section="resources",
)
case(
    "route-decision",
    "decision",
    {"protocol": "draft", "kind": "ROUTE", "destination": "human-review"},
    section="result",
)
case("malformed-top-level", "result", [], "PROTOCOL_STRUCTURE", stage="schema")
case(
    "unsupported-version",
    "result",
    {**result, "protocol": "1.0"},
    "PROTOCOL_VERSION",
    stage="schema",
)
case(
    "score-out-of-bounds",
    "result",
    {**result, "score": 1.01},
    "PROTOCOL_STRUCTURE",
    section="result",
    stage="schema",
)
case(
    "boolean-score",
    "result",
    {**result, "score": True},
    "PROTOCOL_STRUCTURE",
    section="result",
    stage="schema",
)
case(
    "unknown-core-field",
    "result",
    {**result, "file_path": "x"},
    "PROTOCOL_STRUCTURE",
    stage="schema",
)
case(
    "invalid-result-state",
    "result",
    {**result, "determination": "UNKNOWN"},
    "RESULT_STATE",
    section="result",
)
case(
    "error-with-verdict",
    "result",
    {**result, "execution_outcome": "ERROR"},
    "RESULT_STATE",
    section="result",
)
case("empty-evidence", "evidence", {"id": "only-id"}, "EVIDENCE_EMPTY", section="knowledge")
case(
    "resource-inverted-range",
    "resource",
    {"unit": "s", "kind": "RANGE", "minimum": 3, "maximum": 1},
    "RESOURCE_MEASUREMENT",
    section="resources",
)
case(
    "resource-unexpected-value",
    "resource",
    {"unit": "s", "kind": "UNKNOWN", "value": 1},
    "RESOURCE_MEASUREMENT",
    section="resources",
)
case(
    "invalid-extension",
    "result",
    {
        **result,
        "extensions": [
            {"namespace": "unnamespaced", "version": "1", "required": False, "data": {}}
        ],
    },
    "PROTOCOL_STRUCTURE",
    section="extensions",
    stage="schema",
)
case(
    "required-extension",
    "result",
    {
        **result,
        "extensions": [
            {"namespace": "org.example:must", "version": "1", "required": True, "data": {}}
        ],
    },
    "EXTENSION_UNSUPPORTED",
    section="extensions",
)
for name, modify, code in [
    (
        "duplicate-node",
        lambda d: d["graph"]["nodes"].append(copy.deepcopy(d["graph"]["nodes"][0])),
        "GRAPH_DUPLICATE",
    ),
    (
        "missing-node",
        lambda d: d["graph"]["edges"].append({"from_node": "absent", "to_node": "all"}),
        "GRAPH_REFERENCE",
    ),
    (
        "cycle",
        lambda d: d["graph"]["edges"].append({"from_node": "all", "to_node": "phrase"}),
        "GRAPH_UNSUPPORTED",
    ),
    (
        "dynamic-expansion",
        lambda d: d["graph"].update(features=["DYNAMIC_EXPANSION"]),
        "GRAPH_UNSUPPORTED",
    ),
    (
        "invalid-guard",
        lambda d: d["graph"]["edges"][0].update(
            guard={"node_id": "phrase", "field": "verdict", "value": "MAYBE"}
        ),
        "GRAPH_REFERENCE",
    ),
    (
        "invalid-probability",
        lambda d: d["execution_policy"].update(
            admission={"strategy": "PROBABILITY", "probability": 1.1}
        ),
        "PROTOCOL_STRUCTURE",
    ),
    (
        "missing-probability",
        lambda d: d["execution_policy"].update(admission={"strategy": "PROBABILITY"}),
        "ADMISSION_POLICY",
    ),
    (
        "invalid-weights",
        lambda d: d["graph"]["nodes"][2]["config"].update(
            reducer="WEIGHTED_AVERAGE", weights=[-1, 1]
        ),
        "AGGREGATE_CONFIG",
    ),
]:
    d = copy.deepcopy(definition)
    modify(d)
    case(
        name,
        "verification-definition",
        d,
        code,
        "composition"
        if code.startswith("GRAPH")
        else "execution-policy"
        if "probability" in name
        else "aggregation",
        "schema" if code == "PROTOCOL_STRUCTURE" else "semantic",
    )
case(
    "malformed-edge",
    "graph",
    {"nodes": [], "edges": [{"from_node": "x"}]},
    "PROTOCOL_STRUCTURE",
    "composition",
    "schema",
)
case(
    "invalid-severity-domain",
    "severity-domain",
    {"id": "s", "levels": [{"label": "A", "rank": 1}, {"label": "B", "rank": 1}]},
    "PROFILE_DOMAIN",
    "aggregation",
)
case(
    "valid-severity-domain",
    "severity-domain",
    {"id": "s", "levels": [{"label": "A", "rank": 1}, {"label": "B", "rank": 2}]},
    section="aggregation",
)
case("valid-artifact", "artifact-ref", definition["subject"], section="knowledge")
case("valid-evidence", "evidence", {"structured_data": {}}, section="knowledge")
case(
    "optional-extension",
    "extension",
    {"namespace": "org.example:extra", "version": "1", "required": False, "data": None},
    section="extensions",
)
case(
    "custom-resource-dimension",
    "resource-dimension",
    {"id": "energy", "unit": "J", "description": "Energy consumed"},
    section="resources",
)
case(
    "route-missing-destination",
    "decision",
    {"protocol": "draft", "kind": "ROUTE"},
    "RESULT_STATE",
    "result",
)
timestamp = "2026-01-01T00:00:00Z"
node_records = []
final_results = {node["id"]: copy.deepcopy(result) for node in definition["graph"]["nodes"]}
for node in definition["graph"]["nodes"]:
    upstream = [
        edge["from_node"] for edge in definition["graph"]["edges"] if edge["to_node"] == node["id"]
    ]
    node_records.append(
        {
            "node_id": node["id"],
            "executor_ref": node["executor_ref"],
            "upstream_node_ids": upstream,
            "input_context": {"text": "Clear prose.", "length": 12},
            "upstream_results": {id: final_results[id] for id in upstream},
            "started_at": timestamp,
            "finished_at": timestamp,
            "usage": {"wall_time": {"unit": "s", "kind": "EXACT", "value": 0}},
            "result": final_results[node["id"]],
        }
    )
run = {
    "protocol": "draft",
    "run_id": "fixture-run",
    "definition": definition,
    "definition_fingerprint": "local-sha256:" + "a" * 64,
    "subject": definition["subject"],
    "initial_context": {"text": "Clear prose.", "length": 12},
    "opportunity_id": "fixture-opportunity",
    "admission": {"outcome": "RUN", "reason": "ALWAYS"},
    "started_at": timestamp,
    "finished_at": timestamp,
    "nodes": node_records,
    "final_results": final_results,
}
case("complete-run-record", "run-record", run, section="provenance")
bad_run = copy.deepcopy(run)
bad_run["nodes"][-1]["upstream_results"] = {}
case("invalid-upstream-lineage", "run-record", bad_run, "PROVENANCE_LINEAGE", "provenance")


def refresh_results(record):
    """Keep portable snapshots coherent before introducing one targeted defect."""
    record["final_results"] = {
        node["node_id"]: copy.deepcopy(node["result"]) for node in record["nodes"]
    }
    for node in record["nodes"]:
        node["upstream_results"] = {
            id: copy.deepcopy(record["final_results"][id]) for id in node["upstream_node_ids"]
        }


skip_run = copy.deepcopy(run)
skip_run["definition"]["execution_policy"]["admission"] = {
    "strategy": "PROBABILITY",
    "probability": 0,
}
skip_run["admission"] = {"outcome": "SKIP", "reason": "PROBABILITY p=0"}
for node in skip_run["nodes"]:
    node["result"] = {"protocol": "draft", "disposition": "SKIPPED"}
refresh_results(skip_run)
case("admission-skip-run", "run-record", skip_run, section="provenance")
for disposition in ["DEFERRED", "CANCELLED"]:
    bad = copy.deepcopy(skip_run)
    bad["nodes"][1]["result"]["disposition"] = disposition
    refresh_results(bad)
    case(
        f"admission-skip-{disposition.lower()}-node",
        "run-record",
        bad,
        "PROVENANCE_LINEAGE",
        "provenance",
    )
bad = copy.deepcopy(skip_run)
bad["final_results"]["length"]["disposition"] = "DEFERRED"
case("admission-skip-final-mismatch", "run-record", bad, "PROVENANCE_LINEAGE", "provenance")

snapshot_run = copy.deepcopy(run)
for node in snapshot_run["nodes"]:
    node["result"]["output"] = {"v": 1, "nested": [None, False, {}, []]}
refresh_results(snapshot_run)
bad = copy.deepcopy(snapshot_run)
bad["nodes"][-1]["upstream_results"]["phrase"]["output"]["v"] = True
case("upstream-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE", "provenance")
bad = copy.deepcopy(snapshot_run)
for node in bad["nodes"]:
    node["result"]["output"]["v"] = 0
refresh_results(bad)
bad["final_results"]["length"]["output"]["v"] = False
case("final-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE", "provenance")
bad = copy.deepcopy(run)
bad["subject"] = copy.deepcopy(bad["subject"])
bad["definition"]["subject"]["locator"] = 1
bad["subject"]["locator"] = True
case("subject-number-boolean-mismatch", "run-record", bad, "PROVENANCE_LINEAGE", "provenance")

for id, rank, code in [
    ("integral-severity-rank", 1.0, None),
    ("boolean-severity-rank", True, "PROTOCOL_STRUCTURE"),
    ("string-severity-rank", "1", "PROTOCOL_STRUCTURE"),
    ("fractional-severity-rank", 1.5, "PROTOCOL_STRUCTURE"),
]:
    case(
        id,
        "severity-domain",
        {"id": "custom", "levels": [{"label": "one", "rank": rank}]},
        code,
        "aggregation",
        "schema",
    )

for id, time, code in [
    ("utc-offset-run-record", "2026-01-01T00:00:00+00:00", None),
    ("utc-fractional-run-record", "2026-01-01T00:00:00.1234567+00:00", None),
    ("utc-lowercase-run-record", "2026-01-01t00:00:00z", None),
    ("non-utc-positive-run-record", "2026-01-01T00:00:00+01:00", "PROTOCOL_STRUCTURE"),
    ("non-utc-negative-run-record", "2026-01-01T00:00:00-05:00", "PROTOCOL_STRUCTURE"),
    ("timezone-missing-run-record", "2026-01-01T00:00:00", "PROTOCOL_STRUCTURE"),
    ("malformed-timestamp-run-record", "2026-13-01T00:00:00Z", "PROTOCOL_STRUCTURE"),
]:
    record = copy.deepcopy(run)
    for item in [record, *record["nodes"]]:
        item["started_at"] = item["finished_at"] = time
    case(id, "run-record", record, code, "provenance", "schema")

for id, derive in [
    ("weighted-graph-unsupported", False),
    ("weighted-mixed-graph-unsupported", True),
]:
    d = copy.deepcopy(definition)
    if derive:
        d["graph"]["nodes"][0]["kind"] = "DERIVE"
        d["graph"]["nodes"][0]["executor_ref"] = "local.derive"
    d["graph"]["nodes"][-1]["config"] = {
        "reducer": "WEIGHTED_AVERAGE",
        "handling": dict.fromkeys(handling, "IGNORE"),
        "weights": [1] if derive else [1, 3],
    }
    case(id, "verification-definition", d, "GRAPH_UNSUPPORTED", "aggregation")

write("conformance/manifest.json", {"protocol": "draft", "cases": cases})
write("examples/prose/definition.json", definition)
write("examples/prose/context.json", {"text": "Careful claims help readers.", "length": 26})
