# ruff: noqa: E501
"""Conservative release dispositions; no requirement extraction or expectation updates.

Run from the repository root AFTER verification. Existing links remain partial:
an AST predicate list is not an execution trace or a domain completeness proof.
"""

import ast
import collections
import gzip
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = ROOT / "conformance/golden-v4"


def rows(path):
    with (
        gzip.open(path, "rt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(encoding="utf-8")
    ) as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def assertions(row):
    locus = row["assertion"]
    tree = ast.parse((ROOT / locus["path"]).read_text(encoding="utf-8"))
    names = {locus["function"]}
    # Unlike the historical reporter, explicitly include the called equality helper.
    if locus["path"].endswith("test_release_closure.py"):
        names.add("capture")
    result = []

    def applicable_nodes(node):
        yield node
        if locus["path"].endswith("test_release_closure.py") and isinstance(node, ast.If):
            expression = ast.unparse(node.test)
            choice = None
            if expression == "valid":
                choice = row["case_id"].endswith("FIRST_REASON")
            elif expression in ("mode == 'BUDGET'", "mode == 'CANCEL'"):
                choice = row["case_id"].endswith(expression.split("'")[1])
            if choice is not None:
                for child in node.body if choice else node.orelse:
                    yield from applicable_nodes(child)
                return
        for child in ast.iter_child_nodes(node):
            yield from applicable_nodes(child)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            for child in applicable_nodes(node):
                if isinstance(child, ast.Assert):
                    result.append(
                        dict(
                            path=locus["path"],
                            function=node.name,
                            line=child.lineno,
                            predicate=ast.unparse(child.test),
                        )
                    )
                elif (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "raises"
                ):
                    result.append(
                        dict(
                            path=locus["path"],
                            function=node.name,
                            line=child.lineno,
                            predicate=ast.unparse(child),
                        )
                    )
    return result


def main():
    model_path = BASE / "canonical-review-v2/CANONICAL_REQUIREMENTS.jsonl"
    model = {
        r["requirement_id"]: r
        for r in rows(model_path)
        if r.get("record_kind") in ("SEMANTIC_REQUIREMENT", "WHOLE_ROOT_STRUCTURAL_REQUIREMENT")
    }
    old_path = BASE / "verification-final/CANONICAL_ASSERTION_COVERAGE.jsonl.gz"
    previous = {r["requirement_id"]: r for r in rows(old_path)}
    assert set(previous) == set(model) and len(model) == 615
    regressions = rows(OUT / "REGRESSION_RESULTS.jsonl")
    by_requirement = collections.defaultdict(list)
    for r in regressions:
        for identity in r["canonical_ids"]:
            assert identity in model, identity
            by_requirement[identity].append(r)

    dispositions = []
    # Only this narrowly defined quotient has been discharged here. Other
    # records retain their residuals, even if the newly added examples pass.
    gate_id = "CM.RELAY.STANDARD.GATE"
    for identity, r in model.items():
        old = previous[identity]
        actual = by_requirement[identity]
        linked = bool(old["witnesses"] or actual)
        disposition = "PARTIALLY VERIFIED" if linked else "RELEASE BLOCKER"
        if identity == gate_id:
            disposition = "VERIFIED"
        domain = r.get("semantic_domain", r.get("predicate_domain"))
        historical = dict(
            case_ids=sorted({w["case_id"] for w in old["witnesses"]}),
            scopes=sorted({w["scope"] for w in old["witnesses"]}),
            passed=old["passing_witnesses"],
            failed=old["failing_witnesses"],
            assertion_and_repro_reference=f"../verification-final/CANONICAL_ASSERTION_COVERAGE.jsonl.gz#{identity}",
        )
        witnesses = [
            dict(
                case_id=w["case_id"],
                status=w["status"],
                repro=w["repro"],
                expected=w["expected"],
                actual=w["actual"],
                assertions=assertions(w),
                assertion_selection=(
                    "Authored parameter selects the applicable branch; capture equality included."
                    if w["assertion"]["path"].endswith("test_release_closure.py")
                    else "Legacy static function predicates: untaken branches receive no sufficiency credit."
                ),
            )
            for w in actual
        ]
        residual = {
            "required_behavior": r["semantic_proposition"],
            "forbidden_behavior": r.get("forbidden_behavior"),
            "observable_outcome": r.get("observable_outcome"),
            "domain": domain,
            "discharge": "No reviewed domain-complete proof is attached. Historical witnesses are candidate links, not a proof that this entire proposition follows from their predicates."
            if linked
            else "No assertion-to-behavior link has been established. This does NOT establish test absence, nor a need for a new test. Existing tests must be inspected before choosing repair.",
        }
        if identity == gate_id:
            residual = {
                "excluded": "Invalid Result inputs belong to CM.RELAY.STANDARD.GATE.INVALID; JSON parsing and full Result validation have separate records.",
                "proof": "RG.GATE.QUOTIENT: for accepted valid Results the nine disjoint semantic classes exhaust categorical states. The documented gate relation and gate_decision predicate inspect only the five categorical fields, so payload/evidence/usage do not distinguish decisions. Nine independently authored expectations exercise every class. This proves this gate projection, not Result validator correctness or universal graph execution.",
            }
        dispositions.append(
            dict(
                requirement_id=identity,
                record_kind=r["record_kind"],
                hierarchy=r["hierarchy"],
                authority=r.get("authority_classification", r.get("authority")),
                sources=r["sources"],
                preconditions=r.get("preconditions", []),
                domain_refs=r.get("domain_refs", []),
                semantic_proposition=r["semantic_proposition"],
                applicable_domain=domain,
                disposition=disposition,
                historical_candidate_links=historical,
                historical_assertions_reference=f"../verification-final/CANONICAL_ASSERTION_COVERAGE.jsonl.gz#{identity}",
                reviewed_execution_evidence=witnesses,
                what_assertions_establish=(
                    "For each listed authored stimulus, the retained predicate(s) and expected/actual values establish only the exercised relation; they do not establish untaken branches, arbitrary values, or scheduling interleavings."
                    if actual
                    else "No additional assertion credit awarded in this closure pass."
                ),
                untested_boundaries=residual,
                release_action=(
                    "None for this isolated gate relation."
                    if identity == gate_id
                    else "Resolve sufficiency for this existing requirement, or seek an explicit release-scope decision. Do not count the link as complete coverage."
                ),
            )
        )
    with (OUT / "REQUIREMENT_COVERAGE.jsonl").open("w", encoding="utf-8") as stream:
        for row in dispositions:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = collections.Counter(r["disposition"] for r in dispositions)
    branches = {}
    for branch in sorted({tuple(r["hierarchy"][:2]) for r in dispositions}):
        selected = [r for r in dispositions if tuple(r["hierarchy"][:2]) == branch]
        branches[" / ".join(branch)] = dict(
            records=len(selected),
            counts=dict(collections.Counter(r["disposition"] for r in selected)),
            status="BLOCKED"
            if any(r["disposition"] != "VERIFIED" for r in selected)
            else "VERIFIED",
        )
    manifest = json.loads((BASE / "FROZEN_EXPECTATIONS/MANIFEST.json").read_text())
    freeze = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
        for p, h in manifest["files"].items()
    }
    assert all(freeze.values())
    profiles = {}
    for name in ("golden-final", "regression", "existing-final"):
        path = ROOT / f".pytest_cache/release-{name}.xml"
        if not path.exists():
            profiles[name] = {"status": "NOT RUN"}
            continue
        document = ET.parse(path).getroot()
        suites = [document] if document.tag == "testsuite" else list(document.iter("testsuite"))
        stats = {
            k: sum(int(s.attrib.get(k, 0)) for s in suites)
            for k in ("tests", "failures", "errors", "skipped")
        }
        stats["passed"] = stats["tests"] - stats["failures"] - stats["errors"] - stats["skipped"]
        stats["seconds"] = sum(float(s.attrib.get("time", 0)) for s in suites)
        profiles[name] = stats
        shutil.copyfile(path, OUT / path.name)
    latest = Path((ROOT / ".pytest_cache/golden-v4/LATEST").read_text().strip())
    for source, target in (
        (latest / "results.jsonl", "GOLDEN_RESULTS.jsonl.gz"),
        (latest / "execution.json", "GOLDEN_EXECUTION.json.gz"),
    ):
        with gzip.open(OUT / target, "wb") as stream:
            stream.write(source.read_bytes())
    source_paths = {s["path"] for r in model.values() for s in r["sources"] if "path" in s}
    source_hashes = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
        for p in sorted(source_paths)
        if (ROOT / p).is_file()
    }
    write("SOURCE_HASHES.json", source_hashes)
    summary = dict(
        verdict="BLOCKED",
        base_commit="4da463e489c9d9bdb26af9c47979269500ba141f",
        canonical_records=len(model),
        semantic_requirements=582,
        whole_schema_predicates=33,
        dispositions=dict(counts),
        branches=branches,
        profiles=profiles,
        records_with_current_revision_witnesses=sum(bool(by_requirement[i]) for i in model),
        records_without_any_reviewed_link=sum(
            not previous[i]["witnesses"] and not by_requirement[i] for i in model
        ),
        historical_links_are_complete_proofs=False,
        frozen_file_integrity=freeze,
    )
    write("RELEASE_EVIDENCE.json", summary)
    branch_table = "\n".join(
        f"| {b} | {v['records']} | {v['counts'].get('VERIFIED', 0)} | {v['counts'].get('PARTIALLY VERIFIED', 0)} | {v['counts'].get('RELEASE BLOCKER', 0)} | {v['status']} |"
        for b, v in branches.items()
    )
    (OUT / "RELEASE_VERDICT.md").write_text(
        f"""# OpenVerify v0.1 release closure — BLOCKED

Base: `4da463e489c9d9bdb26af9c47979269500ba141f`, branch `fix/golden-v4-verification`, worktree `.worktrees/vcp-final-semantics`.

All 615 canonical records receive a conservative release disposition: **{counts["VERIFIED"]} VERIFIED**, **{counts["PARTIALLY VERIFIED"]} PARTIALLY VERIFIED**, **{counts["RELEASE BLOCKER"]} RELEASE BLOCKER**, **0 UNSUPPORTED**. The 582 semantic requirements and 33 schema predicates are preserved. These are disposition counts, not a claim of completed assertion-sufficiency review. No normative requirement was silently removed from scope.

The release gate fails B: requirement-wide assertion sufficiency is not established. Gate A passes only as disposition accounting; its stronger requirement to finish review of every behavior is not met. Gate C has no newly known unresolved deterministic production defect, but the retained regex timeout is a reliability limitation. Gate D depends on the exact results in TEST_RESULTS.md. Gate E is disclosed in KNOWN_LIMITATIONS.md. Gate F is bounded to the recorded clean consumer checks, not all optional packages or platforms.

Two confirmed stdio defects were fixed: complete invalid JSON now gets -32700 with null id; malformed request envelopes get -32600. Initially both exact response assertions failed with EOF; INITIAL_RPC_RESULTS.jsonl retains this evidence. The new tests also exercise gate classes, storage snapshots, cancellation reasons, file byte boundaries, provider failure/usage and service admission concurrency. Original frozen artifacts remain byte-identical; nine prior expectation corrections remain a separate opt-in overlay.

One isolated projection is discharged: RG.GATE.QUOTIENT. This is not full Result validation, full schema conformance, arbitrary DAG correctness, or universal Golden certification.

| Branch | Records | Verified | Partial | Blocker | Status |
|---|---:|---:|---:|---:|---|
{branch_table}

See [REQUIREMENT_COVERAGE.jsonl](REQUIREMENT_COVERAGE.jsonl) for exact IDs, source references, applicability, actual assertion expressions and requirement-specific residuals. [RELEASE_BLOCKERS.md](RELEASE_BLOCKERS.md) contains the finite decision list. No READY or publication claim is made.
""",
        encoding="utf-8",
    )
    blocked = [r for r in dispositions if r["disposition"] != "VERIFIED"]
    listing = "\n".join(
        f"- `{r['requirement_id']}` — {r['disposition']}: {r['semantic_proposition']}"
        for r in blocked
    )
    (OUT / "RELEASE_BLOCKERS.md").write_text(
        f"""# Finite release blockers

**BLOCKED.** These are existing canonical requirements, not newly invented obligations or a proposed giant test batch.

1. Assertion sufficiency remains unresolved for {len(blocked)} records below. {summary["records_without_any_reviewed_link"]} have no reviewed link at all. A missing link is not proof a test is missing. The remainder have bounded examples, not complete scoped discharge. Review existing assertions before authorizing any additional tests.
2. The published finite-DAG/schema/API scope is broader than the proved/tested projections. No justified reduction closes every applicable residual. An explicit narrower release scope, or completion of these specific evidence links, is needed before READY. This report does not make that normative scope decision.
3. One full ordinary run observed a 2-second regex child startup TimeoutError under concurrent verification load. The isolated rerun passed; final sequential outcome is recorded separately. Raising/removing safety deadlines without a contract decision would hide the tradeoff. Decide whether this documented fail-closed resource limit is acceptable for v0.1.

No new normative decision is requested for the two corrected RPC cases. -32603 and other untested transport failure branches are not claimed discharged merely because -32700/-32600 now pass. No external implementation honesty, domain ownership or cryptographic attestation is inferred.

Exact unresolved record list (predicate/domain/source and linked cases are in REQUIREMENT_COVERAGE.jsonl):

{listing}
""",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                k: summary[k]
                for k in (
                    "verdict",
                    "canonical_records",
                    "dispositions",
                    "records_without_any_reviewed_link",
                    "profiles",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
