"""Package unchanged normative schemas and explicitly scoped prose-derived checks.

This is packaging code, not a normative schema generator. Never edits spec/Golden.
"""

import hashlib
import json
from importlib.metadata import distribution
from pathlib import Path
from urllib.parse import urldefrag, urljoin

from jsonschema_specifications import REGISTRY

ROOT = Path(__file__).resolve().parents[1]
DRAFT = "https://json-schema.org/draft/2020-12/schema"


def present(key):
    return {"required": [key], "properties": {key: {"not": {"type": "null"}}}}


def absent(keys):
    return {"properties": {k: {"type": "null"} for k in keys}}


def equal(key, value):
    return {"required": [key], "properties": {key: {"const": value}}}


def build():
    schemas = {}
    hashes = {}
    for folder in ("schemas/draft", "provider-contract/schemas/draft"):
        for path in sorted((ROOT / folder).glob("*.json")):
            raw = path.read_bytes()
            value = json.loads(raw)
            schemas[value["$id"]] = value
            hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(raw).hexdigest()
    rules = {}

    def rule(name, code, schema, source):
        rules.setdefault(name, []).append(
            {"code": code, "schema": {"$schema": DRAFT, **schema}, "source": source}
        )

    fields = [
        "execution_outcome",
        "applicability",
        "determination",
        "judgment",
        "verdict",
        "score",
        "severity",
    ]
    evaluations = fields[1:]
    observations = fields[3:]
    for state in ("SKIPPED", "DEFERRED", "CANCELLED"):
        # judgment is arbitrary JSON: explicit null is an observation.
        rule(
            "result",
            "RESULT_STATE",
            {
                "if": equal("disposition", state),
                "then": {"allOf": [absent(fields), {"not": {"required": ["judgment"]}}]},
            },
            "spec/draft/result.md",
        )
    rule(
        "result",
        "RESULT_STATE",
        {"if": equal("disposition", "EXECUTED"), "then": present("execution_outcome")},
        "spec/draft/result.md",
    )
    rule(
        "result",
        "RESULT_STATE",
        {
            "if": equal("execution_outcome", "ERROR"),
            "then": {"allOf": [absent(evaluations), {"not": {"required": ["judgment"]}}]},
        },
        "spec/draft/result.md",
    )
    rule(
        "result",
        "RESULT_STATE",
        {"if": equal("execution_outcome", "SUCCESS"), "then": present("applicability")},
        "spec/draft/result.md",
    )
    rule(
        "result",
        "RESULT_STATE",
        {
            "if": equal("applicability", "NOT_APPLICABLE"),
            "then": {"allOf": [absent(fields[2:]), {"not": {"required": ["judgment"]}}]},
        },
        "spec/draft/result.md",
    )
    rule(
        "result",
        "RESULT_STATE",
        {"if": equal("applicability", "APPLICABLE"), "then": present("determination")},
        "spec/draft/result.md",
    )
    rule(
        "result",
        "RESULT_STATE",
        {
            "if": equal("determination", "UNKNOWN"),
            "then": {"allOf": [absent(observations), {"not": {"required": ["judgment"]}}]},
        },
        "spec/draft/result.md",
    )
    # Decision failure classification is deliberately unspecified here: the draft
    # lists no dedicated Decision code. The wrapper uses PROTOCOL_STRUCTURE.
    rule(
        "decision",
        "PROTOCOL_STRUCTURE",
        {
            "if": equal("kind", "ROUTE"),
            "then": present("destination"),
            "else": absent(["destination"]),
        },
        "spec/draft/result.md",
    )
    rule(
        "evidence",
        "EVIDENCE_EMPTY",
        {"anyOf": [present(k) for k in ("message", "artifact_ref", "locator", "structured_data")]},
        "spec/draft/knowledge.md",
    )
    rule(
        "extension",
        "EXTENSION_UNSUPPORTED",
        {"properties": {"required": {"const": False}}},
        "spec/draft/extensions.md",
    )
    rule(
        "resource",
        "RESOURCE_MEASUREMENT",
        {
            "oneOf": [
                {
                    "allOf": [
                        {"properties": {"kind": {"enum": ["EXACT", "ESTIMATED"]}}},
                        present("value"),
                        absent(["minimum", "maximum"]),
                    ]
                },
                {
                    "allOf": [
                        equal("kind", "RANGE"),
                        present("minimum"),
                        present("maximum"),
                        absent(["value"]),
                    ]
                },
                {"allOf": [equal("kind", "UNKNOWN"), absent(["value", "minimum", "maximum"])]},
            ]
        },
        "spec/draft/resources.md",
    )
    supported = [
        "result",
        "decision",
        "resource",
        "evidence",
        "artifact-ref",
        "extension",
        "resource-dimension",
    ]

    def localize(value):
        if isinstance(value, list):
            return [localize(v) for v in value]
        if isinstance(value, dict):
            return {
                k: (
                    "#/$defs/" + v.replace("~", "~0").replace("/", "~1")
                    if k == "$ref" and v in schemas
                    else localize(v)
                )
                for k, v in value.items()
                if k != "$id"
            }
        return value

    meta_root = "https://json-schema.org/draft/2020-12/schema"
    meta_resources = {
        uri: REGISTRY.contents(uri)
        for uri in REGISTRY
        if uri.startswith("https://json-schema.org/draft/2020-12/")
    }

    def meta_local(value, base):
        if isinstance(value, list):
            return [meta_local(v, base) for v in value]
        if not isinstance(value, dict):
            return value
        result = {}
        for k, v in value.items():
            if k in ("$id", "$dynamicAnchor", "$schema"):
                continue
            if k in ("$ref", "$dynamicRef") and isinstance(v, str):
                target, fragment = urldefrag(urljoin(base, v))
                if k == "$dynamicRef":
                    target, fragment = meta_root, ""
                result["$ref"] = (
                    "#/$defs/"
                    + target.replace("~", "~0").replace("/", "~1")
                    + ("/" + fragment.lstrip("/") if fragment else "")
                )
            else:
                result[k] = meta_local(v, base)
        return result

    meta = {
        "$schema": DRAFT,
        "$ref": "#/$defs/" + meta_root.replace("/", "~1"),
        "$defs": {uri: meta_local(value, uri) for uri, value in meta_resources.items()},
    }
    bundle = {
        "bundle_format": 1,
        "vcp_version": "draft",
        "provider_version": "0.1",
        "revision": "5f17f402a270882f244a54dde25eda92a085eb39",
        "schemas": schemas,
        "rules": rules,
        "compound": {"$schema": DRAFT, "$defs": {k: localize(v) for k, v in schemas.items()}},
        "meta": meta,
        "semantic_vcp_types": supported,
        "source_sha256": hashes,
    }
    return bundle


if __name__ == "__main__":
    bundle = build()
    for language, target in {
        "node": "schemas/bundle.json",
        "rust": "schemas/bundle.json",
        "go": "bundle.json",
        "jvm": "src/main/resources/bundle.json",
        "dotnet": "bundle.json",
        "ruby": "lib/openverify/bundle.json",
        "php": "resources/bundle.json",
        "python": "src/openverify_sdk/bundle.json",
    }.items():
        directory = ROOT / "sdk" / language
        path = directory / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8", newline="\n")
        notice = distribution("jsonschema-specifications").read_text("licenses/COPYING")
        if not notice:
            raise RuntimeError("Missing third-party metaschema license notice")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        license_text += (
            "\n\nBundled JSON Schema metaschemas (jsonschema-specifications):\n\n" + notice
        )
        (directory / "LICENSE").write_text(license_text, encoding="utf-8", newline="\n")
