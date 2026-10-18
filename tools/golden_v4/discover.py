"""Text-only source indexing. This module never imports the system under test."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "conformance/golden-v4"
PIN = "5f17f402a270882f244a54dde25eda92a085eb39"
BLUEPRINT = "3c73fee1826a65d7101c375d21421988a798ae6ee336824546b055ca92d5a6d2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_lines(path: Path, rows) -> None:
    path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def source_files():
    # Explicit allowlist: no tests, fixtures, conformance builders or historical paths.
    for directory, pattern in [("spec/draft", "*.md"), ("provider-contract/spec/draft", "*.md"),
                               ("schemas/draft", "*.json"), ("provider-contract/schemas/draft", "*.json"),
                               ("docs/relay", "*.md"), ("profiles/standard-draft", "*.json"),
                               ("src/openverify", "*.py"), ("src/openverify", "*.json")]:
        yield from sorted((ROOT / directory).rglob(pattern))
    yield ROOT / "README.md"
    yield ROOT / "provider-contract/README.md"
    yield ROOT / "pyproject.toml"


def reference(path, start, end=None, pointer=None):
    raw = path.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    return {"path": path.relative_to(ROOT).as_posix(), "line_start": start,
            "line_end": end or start, "source_sha256": digest(raw),
            "text_sha256": digest("\n".join(lines[start-1:(end or start)]).encode()),
            **({"pointer": pointer} if pointer is not None else {})}


def clause_index():
    rows = []
    for directory, layer in [("spec/draft", "VCP"), ("provider-contract/spec/draft", "PROVIDER"),
                             ("docs/relay", "RELAY")]:
        for p in sorted((ROOT / directory).glob("*.md")):
            lines = p.read_text(encoding="utf-8").splitlines()
            active = layer != "VCP"
            # Entire open-question documents are scope constraints, never expected semantics.
            scope = p.name in {"open-questions.md", "conceptual-audit.md"}
            for n, line in enumerate(lines, 1):
                if line.startswith("## ") and layer == "VCP":
                    if line in {"## NON-NORMATIVE EXAMPLES", "## OPEN QUESTIONS"}:
                        active = False
                    elif line not in {"## Breaking changes"}:
                        active = True
                if not active or scope or not line.strip() or line.startswith(("#", "```")):
                    continue
                # Conservative indexing: every substantive line, including non-MUST constraints.
                occurrences = list(re.finditer(r"\bMUST NOT\b|\bMUST\b|\bSHOULD NOT\b|\bSHOULD\b|\bMAY\b", line))
                for i in range(max(1, len(occurrences))):
                    cid = f"V4.C.{layer}.{p.stem}.L{n:04d}.{i+1}"
                    rows.append({"clause_id": cid, **reference(p, n), "rule": line.strip(),
                                 "owner_layer": layer, "kind": "PROSE", "obligation_ids": ["V4.O." + cid[5:]],
                                 "triage": "REQUIRES_SEMANTIC_REVIEW"})
    # JSON pointers address each individual field requirement/enum member/constraint.
    keywords = {"type", "const", "minimum", "maximum", "minLength", "maxLength", "pattern", "minItems",
                "maxItems", "uniqueItems", "additionalProperties", "oneOf", "anyOf", "allOf", "if", "then", "else", "not", "$ref"}
    for directory, layer in [("schemas/draft", "VCP"), ("provider-contract/schemas/draft", "PROVIDER")]:
        for p in sorted((ROOT / directory).glob("*.schema.json")):
            raw = p.read_text(encoding="utf-8")
            def walk(v, pointer=""):
                if isinstance(v, dict):
                    for key, child in v.items():
                        ptr = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
                        if key in {"required", "enum"}:
                            for i, item in enumerate(child):
                                yield ptr + "/" + str(i), key, item
                        elif key in keywords:
                            yield ptr, key, child
                        yield from walk(child, ptr)
                elif isinstance(v, list):
                    for i, child in enumerate(v):
                        yield from walk(child, pointer + "/" + str(i))
            for pointer, key, value in walk(json.loads(raw)):
                # Whole schema line range is exact, deliberately not a guessed key occurrence.
                cid = f"V4.C.{layer}.SCHEMA.{p.stem.removesuffix('.schema')}.{pointer}"
                rows.append({"clause_id": cid, **reference(p, 1, len(raw.splitlines()), pointer),
                             "rule": {key: value}, "owner_layer": layer, "kind": "SCHEMA",
                             "obligation_ids": ["V4.O." + cid[5:]], "triage": "REQUIRES_ASSERTION_REVIEW"})
    p = ROOT / "src/openverify/relay/ports/__init__.py"
    for cls in ast.parse(p.read_text(encoding="utf-8")).body:
        if isinstance(cls, ast.ClassDef) and any(isinstance(b, ast.Name) and b.id == "Protocol" for b in cls.bases):
            for method in cls.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    cid = f"V4.C.RELAY.PORT.{cls.name}.{method.name}"
                    rows.append({"clause_id": cid, **reference(p, method.lineno, method.end_lineno),
                                 "rule": ast.unparse(method), "owner_layer": "RELAY", "kind": "METHOD",
                                 "obligation_ids": ["V4.O."+cid[5:]], "triage": "REQUIRES_ASSERTION_REVIEW"})
    return rows


def error_inventory():
    rows = []
    prose_paths = sorted((ROOT / "spec/draft").glob("*.md"))
    for filename, layer in [("src/openverify/error_codes.py", "VCP"), ("src/openverify/relay/error_codes.py", "RELAY")]:
        p = ROOT / filename
        for cls in ast.parse(p.read_text(encoding="utf-8")).body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for node in cls.body:
                if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
                    continue
                code = node.value.value
                authority = "SDK_SPECIFIC" if code in {"POLICY_ERROR", "RESULT_PROJECTION"} else ("NORMATIVE_VCP" if layer == "VCP" else "RELAY_SPECIFIC")
                refs = [reference(p, node.lineno, node.end_lineno)]
                if authority == "NORMATIVE_VCP":
                    for q in prose_paths:
                        if q.name in {"open-questions.md", "conceptual-audit.md"}:
                            continue
                        for n, line in enumerate(q.read_text(encoding="utf-8").splitlines(), 1):
                            if re.search(r"(?<![A-Z_])" + re.escape(code) + r"(?![A-Z_])", line):
                                refs.append(reference(q, n))
                    assert len(refs) > 1, f"No prose authority for {code}"
                rows.append({"declaration_id": f"V4.ERROR.{layer}.{code}", "identifier": code,
                             "authority": authority, "sources": refs, "portable": authority.startswith("NORMATIVE"),
                             "obligation_ids": [f"V4.O.ERROR.{layer}.{code}"]})
    p = ROOT / "provider-contract/spec/draft/errors.md"
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("| "):
            code = line.split("|")[1].strip()
            if code.isupper():
                rows.append({"declaration_id": f"V4.ERROR.PROVIDER.{code}", "identifier": code,
                             "authority": "NORMATIVE_PROVIDER_CONTRACT", "sources": [reference(p, n)],
                             "portable": True, "obligation_ids": [f"V4.O.ERROR.PROVIDER.{code}"]})
    assert len(rows) == 53
    return rows


def main():
    assert digest((OUT / "BLUEPRINT.md").read_bytes()) == BLUEPRINT
    assert not (OUT / "FROZEN_EXPECTATIONS/MANIFEST.json").exists(), "Already frozen"
    hashes = {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in source_files()}
    roots = {layer: [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / directory).glob("*.schema.json"))]
             for layer, directory in [("VCP", "schemas/draft"), ("PROVIDER", "provider-contract/schemas/draft")]}
    write_json(OUT / "NORMATIVE_SOURCE_HASHES.json", {"production_commit": PIN, "files": hashes, "schema_roots": roots})
    clauses = clause_index()
    write_lines(OUT / "NORMATIVE_CLAUSES.jsonl", clauses)
    errors = error_inventory()
    write_json(OUT / "ERROR_INVENTORY.json", {"blueprint_correction": "D-001; expressly approved by user: 53 declarations, 33 normative VCP, 8 normative Provider, 2 SDK diagnostics, 10 Relay-specific", "declarations": errors})
    rows = (OUT / "BLUEPRINT.md").read_text(encoding="utf-8").splitlines()
    families = []
    for line in rows:
        if line.startswith("| `V4."):
            cells = [s.strip() for s in line.strip("|").split("|")]
            families.append({"family": cells[0].strip("`"), "domain": cells[1], "blueprint_formula": cells[2], "blueprint_partition": cells[3], "mode": cells[4], "status": "MISSING"})
    write_json(OUT / "FAMILY_INVENTORY.json", families)
    text = ["# Golden v4 contract inventory\n", "Status: discovery in progress; NOT CERTIFIED.\n",
            f"Pinned production: `{PIN}`. Blueprint SHA-256: `{BLUEPRINT}`.\n",
            "D-001 is explicitly adjudicated by the user: retain all 53 declared identifiers; distinguish authority. The unchanged blueprint's 51-declaration row is corrected to 53 declarations, not 53 portable VCP requirements.\n",
            f"Schema roots independently counted: {len(roots['VCP'])} VCP, {len(roots['PROVIDER'])} Provider.\n",
            "The two SDK diagnostics are covered only at implementation boundaries. Error code membership does not establish exact error precedence.\n",
            "| Identifier | Authority | Source references |\n| --- | --- | --- |"]
    for r in errors:
        text.append(f"| `{r['identifier']}` | {r['authority']} | " + "; ".join(f"`{s['path']}:{s['line_start']}-{s['line_end']}`" for s in r['sources']) + " |")
    text += ["\nCounts: normative VCP 33; normative Provider Contract 8; SDK-specific 2; Relay-specific 10. These are declarations partitioned by authority; codes with identical spelling across layers remain separate entries.\n",
             "Exact byte hashes and source ranges are retained in ERROR_INVENTORY.json and NORMATIVE_SOURCE_HASHES.json. Indexing is conservative and is not itself proof of obligation coverage. No historical Golden material is an oracle input.\n"]
    (OUT / "CONTRACT_INVENTORY.md").write_text("\n".join(text), encoding="utf-8")
    print(json.dumps({"schema_roots": {k: len(v) for k,v in roots.items()}, "indexed_units": len(clauses), "error_declarations": len(errors), "families": len(families)}))


if __name__ == "__main__":
    main()
