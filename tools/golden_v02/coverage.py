"""Coverage accounting distinguishes declarations, model checks and SUT evidence."""

from __future__ import annotations

import json
from collections import Counter

from tools.golden_v02.verify_manifest import baseline

# These limitations concern the suite, not inferred implementation behavior.
KNOWN_GAPS = [
    {
        "dimension": "node_kind_interactions",
        "reason": "Per-kind input matrices exist; not every fault/policy/guard/resource interaction is independently frozen for every kind.",
    },
    {
        "dimension": "provider_rpc_sessions",
        "reason": "Lifecycle traces and byte framing are covered; the complete JSON-RPC session/correlation cross-product is not enumerated.",
    },
    {
        "dimension": "provider_schema_keywords",
        "reason": "The full Draft 2020-12 value/program space is infinite; representative schema boundaries only.",
    },
    {
        "dimension": "provenance_authenticity",
        "reason": "Opaque identity/coherent rewriting cannot be checked without an authenticated trust root; BLOCKED_BY_SPEC.",
    },
    {
        "dimension": "scheduler_coloring",
        "reason": "290 abstract scheduler states have no Cartesian multiplication with all terminal Results, guards and Control choices.",
    },
    {
        "dimension": "extension_port_rules",
        "reason": "Six variants for each public port are representative experiments, not an exhaustive formal interface state space.",
    },
    {
        "dimension": "standard_findings",
        "reason": "Finding/range object schemas are underspecified in public manifests; exact source-coordinate golden fixtures require profile adjudication.",
    },
    {
        "dimension": "mutation_sensitivity",
        "reason": "14 mutations of actual execution observations challenge Golden checks; no production source mutation campaign or exhaustive mutant claim.",
    },
    {
        "dimension": "experiment_independence",
        "reason": "Executable assertion programs are frozen with stimuli. Some inherited experiments still construct environments dynamically from public manifests; complete case-by-case independent portable wire expectations are not established for all experiments.",
    },
]


def report(rows=()):
    frozen = json.loads((baseline() / "coverage.json").read_text(encoding="utf-8"))
    matrix = json.loads((baseline() / "feature-matrix.json").read_text(encoding="utf-8"))
    indexed = {r["id"]: r for r in rows}
    assert len(indexed) == len(rows), "duplicate executed case count"
    dimensions = {}
    for f in matrix:
        ids = set(f["valid_case_ids"] + f["invalid_case_ids"])
        completed = [indexed[i] for i in ids if i in indexed]
        dimensions[f["feature_id"]] = {
            "normative_support": f["normative_support"],
            "implementation_support": f["implementation_support"],
            "declared_unique_cases": len(ids),
            "valid_cases": len(f["valid_case_ids"]),
            "invalid_cases": len(f["invalid_case_ids"]),
            "transition_cases": len(f["transition_case_ids"]),
            "boundary_cases": len(f["boundary_case_ids"]),
            "interaction_cases": len(f["interaction_case_ids"]),
            "statuses": dict(Counter(r["status"] for r in completed)),
            "sut_executed_cases": sum(r.get("sut_executed", False) for r in completed),
            "unexecuted_case_ids": sorted(ids - indexed.keys()),
            "case_ids": sorted(ids),
            "executed_assertion_case_ids": sorted(
                r["id"]
                for r in completed
                if r.get("sut_executed") and r["status"] in ("PASS", "FAIL")
            ),
            "failed_case_ids": sorted(
                r["id"] for r in completed if r["status"] in ("FAIL", "ERROR")
            ),
            "ambiguous_case_ids": sorted(
                r["id"]
                for r in completed
                if r.get("spec_ambiguity") or r["status"] == "BLOCKED_BY_SPEC"
            ),
            "finite_exhaustiveness": "only where separately bounded in enumeration metadata",
        }
    return {
        "unique_declared_cases": frozen["unique_cases"],
        "unique_reported_cases": len(indexed),
        "unique_sut_executed_cases": sum(r.get("sut_executed", False) for r in indexed.values()),
        "statuses": dict(Counter(r["status"] for r in indexed.values())),
        "result_enumeration": frozen["result_enumeration"],
        "graph_enumeration": frozen["graph_enumeration"],
        "reducer_enumeration": frozen["reducer_enumeration"],
        "category_totals": frozen["categories"],
        "dimensions": dimensions,
        "known_gaps": KNOWN_GAPS,
        "complete_for_requested_scope": False,
        "claim": "finite table coverage and bounded model coverage; no claim of exhaustive arbitrary programs or current full-system conformance",
    }


def markdown(data):
    lines = [
        "# Golden coverage report",
        "",
        f"Declared unique cases: {data['unique_declared_cases']}. Reported: {data['unique_reported_cases']}. SUT executed: {data['unique_sut_executed_cases']}.",
        "",
        "Full requested scope complete: **NO**.",
        "",
        "| Feature | Declared | Valid | Invalid | Boundary | Interaction | SUT executed |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, d in data["dimensions"].items():
        lines.append(
            f"| {name} | {d['declared_unique_cases']} | {d['valid_cases']} | {d['invalid_cases']} | {d['boundary_cases']} | {d['interaction_cases']} | {d['sut_executed_cases']} |"
        )
    lines += ["", "## Explicit coverage limits", ""]
    lines += [f"- **{g['dimension']}**: {g['reason']}" for g in data["known_gaps"]]
    return "\n".join(lines) + "\n"
