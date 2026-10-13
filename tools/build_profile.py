"""Maintain the standard named choices; this is not the core ontology."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
profile = {
    "protocol": "draft",
    "id": "standard-draft",
    "version": "0.1.0",
    "flattened_statuses": ["PASS", "FAIL", "UNKNOWN", "ERROR", "SKIP"],
    "severity_domain": {
        "id": "standard-draft",
        "levels": [
            {"label": label, "rank": rank}
            for label, rank in [("INFO", 10), ("WARNING", 20), ("ERROR", 30), ("BLOCKER", 40)]
        ],
    },
    "aggregators": [
        "ALL",
        "ANY",
        "MAJORITY",
        "MIN_SCORE",
        "MAX_SCORE",
        "AVERAGE",
        "WEIGHTED_AVERAGE",
        "WORST_SEVERITY",
    ],
    "admission_policies": ["ALWAYS", "PROBABILITY"],
    "decisions": ["CONTINUE", "STOP_SUCCESS", "STOP_FAILURE", "ROUTE", "RETRY", "DEFER"],
    "resource_dimensions": [
        {"id": id, "unit": unit, "description": description}
        for id, unit, description in [
            ("wall_time", "s", "Elapsed wall-clock duration"),
            ("money", "currency", "Monetary usage; measurement supplies the currency unit"),
            ("input_tokens", "token", "Input tokens consumed"),
            ("output_tokens", "token", "Output tokens consumed"),
            ("cpu_time", "s", "CPU time consumed"),
            ("gpu_time", "s", "GPU time consumed"),
            ("human_time", "s", "Reviewer time consumed"),
            ("network_bytes", "byte", "Network bytes transferred"),
        ]
    ],
}
for path in [
    "profiles/standard-draft/profile.json",
    "src/openverify/data/profile.json",
    "conformance/valid/standard-profile.json",
]:
    (ROOT / path).write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8", newline="\n")
manifest_path = ROOT / "conformance/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["cases"] = [c for c in manifest["cases"] if c["id"] != "standard-profile"]
manifest["cases"].append(
    {
        "id": "standard-profile",
        "description": "Valid standard profile reference",
        "object_type": "profile",
        "input": "valid/standard-profile.json",
        "valid": True,
        "stage": "both",
        "expected": "expected/standard-profile.json",
        "spec": "profiles/standard-draft/README.md",
    }
)
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
(ROOT / "conformance/expected/standard-profile.json").write_text(
    '{"valid": true}\n', encoding="utf-8", newline="\n"
)
