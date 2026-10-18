"""Integrity, fail-closed inventory audit, exact replay, and release evidence."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import os
from collections import Counter
from pathlib import Path

from .discover import BLUEPRINT, OUT, PIN, ROOT, digest, write_json, write_lines


def read_rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def verify_freeze():
    issues=[]
    manifest=json.loads((OUT/"FROZEN_EXPECTATIONS/MANIFEST.json").read_text(encoding="utf-8"))
    for path,expected in manifest["files"].items():
        p=ROOT/path
        actual=digest(p.read_bytes()) if p.is_file() else None
        if actual!=expected:issues.append({"path":path,"expected":expected,"actual":actual})
    if digest((OUT/"BLUEPRINT.md").read_bytes())!=BLUEPRINT:issues.append({"error":"Blueprint changed"})
    sources=json.loads((OUT/"NORMATIVE_SOURCE_HASHES.json").read_text(encoding="utf-8"))
    for path,expected in sources["files"].items():
        actual=digest((ROOT/path).read_bytes())
        if actual!=expected:
            revision_path=os.environ.get("OPENVERIFY_GOLDEN_SOURCE_REVISION")
            approved=False
            if revision_path:
                revision=json.loads(Path(revision_path).read_text(encoding="utf-8"))
                entry=revision["source_changes"].get(path)
                # The monorepo handoff appends documentation links to README;
                # it still requires the exact old/new hashes and frozen seal.
                approved=bool(entry and path in {"README.md","spec/draft/dataflow.md","spec/draft/aggregation.md","spec/draft/open-questions.md",
                              "src/openverify/dataflow.py","src/openverify/provider/stdio.py","src/openverify/relay/adapters/server.py",
                              "src/openverify/provider/validation.py","src/openverify/standard/text.py",
                              "src/openverify/standard/common.py","src/openverify/relay/application/execution.py",
                              "src/openverify/relay/adapters/process.py"}
                              and entry["old_sha256"]==expected and entry["new_sha256"]==actual
                              and revision["frozen_manifest_sha256"]==digest((OUT/"FROZEN_EXPECTATIONS/MANIFEST.json").read_bytes()))
            if not approved:issues.append({"path":path,"error":"Production/source drift","actual":actual,"expected":expected})
    expectation_revision=os.environ.get("OPENVERIFY_GOLDEN_EXPECTATION_REVISION")
    if expectation_revision:
        revision_path=os.environ.get("OPENVERIFY_GOLDEN_SOURCE_REVISION")
        revision=json.loads(Path(revision_path).read_text(encoding="utf-8")) if revision_path else {}
        actual=digest(Path(expectation_revision).read_bytes())
        if actual!=revision.get("expectation_corrections_sha256"):
            issues.append({"error":"Unsealed expectation corrections","actual":actual})
    # Git ancestry verifies the baseline without importing or running historical files.
    result=subprocess.run(["git","merge-base","--is-ancestor",PIN,"HEAD"],cwd=ROOT,capture_output=True)
    if result.returncode:issues.append({"error":"Pinned production is not ancestor"})
    return issues


def inventory():
    cases=read_rows(OUT/"CASES.jsonl")
    clauses=read_rows(OUT/"NORMATIVE_CLAUSES.jsonl")
    obligations=read_rows(OUT/"OBLIGATIONS.jsonl")
    proofs=read_rows(OUT/"REDUCTION_LEDGER.jsonl")
    issues=[]
    ids=[c["case_id"] for c in cases]
    if len(ids)!=len(set(ids)):issues.append("Duplicate case IDs")
    known={c["clause_id"] for c in clauses}
    if any(set(c["normative_clauses"])-known for c in cases):issues.append("Case links nonexistent clause")
    uncovered=[o["obligation_id"] for o in obligations if o["status"]=="MISSING"]
    if uncovered:issues.append(f"{len(uncovered)} extracted clause obligations lack reviewed assertion/proof crosswalk")
    unproved=[p["proof_id"] for p in proofs if p["status"]!="PROVED"]
    if unproved:issues.append(f"{len(unproved)} unproved reduction/composition residuals")
    methods=[c for c in clauses if c["kind"]=="METHOD"]
    roots=json.loads((OUT/"NORMATIVE_SOURCE_HASHES.json").read_text(encoding="utf-8"))["schema_roots"]
    if len(methods)!=7:issues.append("Port method inventory differs from seven direct methods")
    for paths in roots.values():
        for path in paths:
            if not any(c["path"]==path for c in clauses):issues.append("Unindexed schema root: "+path)
    actual_roots={layer:sorted(p.relative_to(ROOT).as_posix() for p in (ROOT/directory).glob("*.schema.json")) for layer,directory in [("VCP","schemas/draft"),("PROVIDER","provider-contract/schemas/draft")]}
    if actual_roots!={k:sorted(v) for k,v in roots.items()}:issues.append("Added/removed schema roots outside frozen inventory")
    schema_ids={json.loads((ROOT/path).read_text(encoding="utf-8"))["$id"] for paths in roots.values() for path in paths}
    unresolved_refs=[]
    def check_refs(value,path):
        if isinstance(value,dict):
            for key,v in value.items():
                if key=="$ref" and not v.startswith("#") and v.split("#")[0] not in schema_ids:unresolved_refs.append({"path":path,"ref":v})
                check_refs(v,path)
        elif isinstance(value,list):
            for v in value:check_refs(v,path)
    for paths in roots.values():
        for path in paths:check_refs(json.loads((ROOT/path).read_text(encoding="utf-8")),path)
    if unresolved_refs:issues.append("Unresolved transitive schema references: "+str(unresolved_refs))
    # Check source ranges/digests rather than accepting a syntactically present ID.
    source_text={}
    broken_ranges=[]
    for c in clauses:
        path=c["path"]
        if path not in source_text:source_text[path]=(ROOT/path).read_text(encoding="utf-8").splitlines()
        segment="\n".join(source_text[path][c["line_start"]-1:c["line_end"]]).encode()
        if digest(segment)!=c["text_sha256"]:broken_ranges.append(c["clause_id"])
    if broken_ranges:issues.append("Clause text/range mismatch: "+str(broken_ranges[:10]))
    # Inventory of actual declared facade/host methods, beyond the seven ports.
    public=[]
    public_files=["src/openverify/__init__.py","src/openverify/relay/api.py","src/openverify/relay/entrypoints/service.py","src/openverify/relay/entrypoints/cli.py","src/openverify/relay/entrypoints/mcp.py","src/openverify/relay/entrypoints/http.py"]
    for path in public_files:
        tree=ast.parse((ROOT/path).read_text(encoding="utf-8"))
        for obj in tree.body:
            if isinstance(obj,(ast.FunctionDef,ast.AsyncFunctionDef)) and not obj.name.startswith("_"):
                public.append({"path":path,"method":obj.name,"line":obj.lineno})
            elif isinstance(obj,ast.ClassDef):
                for method in obj.body:
                    if isinstance(method,(ast.FunctionDef,ast.AsyncFunctionDef)) and not method.name.startswith("_"):
                        public.append({"path":path,"method":obj.name+"."+method.name,"line":method.lineno})
            elif isinstance(obj,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="__all__" for t in obj.targets):
                for name in ast.literal_eval(obj.value):public.append({"path":path,"method":name,"line":obj.lineno})
    unindexed_methods=[r for r in public if not any(c["kind"]=="METHOD" and c["path"]==r["path"] and c["line_start"]<=r["line"]<=c["line_end"] for c in clauses)]
    if unindexed_methods:issues.append(f"{len(unindexed_methods)} facade/host declarations lack clause-level method index entries")
    fs=json.loads((OUT/"FAMILY_INVENTORY.json").read_text(encoding="utf-8"))
    for family in fs:
        if not any(c["family"]==family["family"] for c in cases):issues.append("Missing family: "+family["family"])
    # Oracle import audit: AST, never execute its imports to establish independence.
    prohibited=[]
    for p in (ROOT/"tests/golden_v4/oracle").glob("*.py"):
        for n in ast.walk(ast.parse(p.read_text(encoding="utf-8"))):
            names=[n.module or ""] if isinstance(n,ast.ImportFrom) else ([a.name for a in n.names] if isinstance(n,ast.Import) else [])
            if any(name.startswith("openverify") for name in names):prohibited.append(str(p))
    if prohibited:issues.append("Oracle imports production: "+str(prohibited))
    candidates={f["family"]:[c for c in cases if c["family"]==f["family"]] for f in fs}
    for family,count in [("V4.VCP.DEF.PRESENCE",4096),("V4.VCP.RESULT.WIRE_AXIS",1024),("V4.VCP.RESULT.SEMANTIC_AXIS",324),("V4.VCP.RESULT.OBS_MASK",2304),("V4.VCP.GRAPH.DAG_0_4",4166),("V4.VCP.AGG.HANDLING_MAP",1024)]:
        if len(candidates[family])!=count:issues.append("Finite coordinate universe mismatch: "+family)
    errors=json.loads((OUT/"ERROR_INVENTORY.json").read_text(encoding="utf-8"))["declarations"]
    authorities=Counter(e["authority"] for e in errors)
    if authorities!={"NORMATIVE_VCP":33,"NORMATIVE_PROVIDER_CONTRACT":8,"SDK_SPECIFIC":2,"RELAY_SPECIFIC":10}:issues.append("Corrected error authority inventory mismatch")
    for p in proofs:
        if p["status"]=="PROVED" and (not p.get("checker") or not p.get("premise_case_families")):issues.append("Proof lacks checker/tested premise links: "+p["proof_id"])
    # Frozen phase row used its third partition for stutters; treating it as N
    # would be an invalid impossibility claim. Preserve the freeze and report it.
    issues.append("Frozen phase-count row labels four stutters in the N column; those are not impossibility proofs")
    return {"certified":not issues,"issues":issues,"indexed_clause_units":len(clauses),"direct_methods":len(methods),
            "schema_roots":{k:len(v) for k,v in roots.items()},"case_ids":len(ids),"missing_clause_obligations":uncovered,
            "unproved_proof_ids":unproved,"unindexed_supported_methods":unindexed_methods,"transitive_schema_reference_errors":unresolved_refs,
            "error_authority_counts":dict(authorities),"error_declarations":errors,
            "portable_unique_obligation_total":"NOT_ESTABLISHED: clause-level assertion review and canonical deduplication remain incomplete"}


def latest():
    pointer=ROOT/".pytest_cache/golden-v4/LATEST"
    return Path(pointer.read_text(encoding="utf-8")) if pointer.exists() else None


def summary(artifact=None):
    path=Path(artifact) if artifact else latest()
    results=read_rows(path/"results.jsonl") if path and (path/"results.jsonl").exists() else []
    cases=read_rows(OUT/"CASES.jsonl")
    projections={r["family"]:r for r in json.loads((OUT/"PROJECTIONS.json").read_text(encoding="utf-8"))}
    families=json.loads((OUT/"FAMILY_INVENTORY.json").read_text(encoding="utf-8"))
    table=[]
    for f in families:
        name=f["family"];cs=[c for c in cases if c["family"]==name];rs=[r for r in results if r["family"]==name]
        p=projections[name]
        if name=="V4.VCP.LIFECYCLE.PHASES":
            p={**p,"VALID":"conditional","INVALID":"conditional","IMPOSSIBLE":0,"UNRESOLVED":"phase pair versus explicit transition call; see 5/4/7 partition"}
        table.append({"family":name,"formula":p["formula"],"C":p["C"],"VALID":p["VALID"],"INVALID":p["INVALID"],"IMPOSSIBLE":p["IMPOSSIBLE"],"UNRESOLVED":p["UNRESOLVED"],
                      "supported_obligations":"not established","direct_passed":"not established","proved":str(sum(1 for r in read_rows(OUT/"REDUCTION_LEDGER.jsonl") if r["family"]==name and r["status"]=="PROVED"))+" proof(s); obligation count unreviewed",
                      "failed":"not established","missing_obligations":"unreconciled","pytest_passed":sum(r["status"]=="PASS" for r in rs),"pytest_failed":sum(r["status"]=="FAIL" for r in rs),"missing_cases":len(cs)-len(rs),"pytest_cases":len(cs),"relay_api_calls":sum(r.get("relay_api_calls",0) for r in rs),"duration":sum(r["duration"] for r in rs)})
    inv=inventory();integrity=verify_freeze()
    failures=[r for r in results if r["status"]=="FAIL"]
    verdict="CERTIFIED FOR DECLARED SUPPORTED PROFILE" if inv["certified"] and not integrity and not failures and len(results)==len(cases) else "NOT CERTIFIED"
    return {"verdict":verdict,"artifact_path":str(path),"families":table,"executed":len(results),"frozen_cases":len(cases),"failures":failures,"integrity_issues":integrity,"inventory":inv}


def publish(artifact):
    s=summary(artifact)
    write_json(OUT/"COVERAGE.json",s)
    write_lines(OUT/"GOLDEN_FAILURES.jsonl",s["failures"])
    execution=json.loads((Path(artifact)/"execution.json").read_text(encoding="utf-8"))
    write_json(OUT/"EXECUTION_REPORT.json",execution)
    mutation=[r for r in read_rows(Path(artifact)/"results.jsonl") if r["family"]=="V4.AUDIT.MUTATION"]
    write_json(OUT/"MUTATION_REPORT.json",{"probes":mutation,"all_detected":bool(mutation) and all(r["status"]=="PASS" for r in mutation)})
    text=["# Golden v4 coverage report\n",s["verdict"],"\nNo grand candidate total is reported. Obligation totals remain not established until canonical deduplication and reviewed assertion/proof links exist. Pytest passing/failing item counts are retained separately in COVERAGE.json and never substituted into the obligation columns. Clause-level crosswalk gaps fail certification.\n",
          "| FAMILY | FORMULA | C | VALID | INVALID | IMPOSSIBLE | UNRESOLVED | SUPPORTED OBLIGATIONS | DIRECT PASSED | PROVED | FAILED | MISSING | PYTEST CASES | RELAY API CALLS | DURATION |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in s["families"]:
        text.append("| "+" | ".join(str(r[k]) for k in ("family","formula","C","VALID","INVALID","IMPOSSIBLE","UNRESOLVED","supported_obligations","direct_passed","proved","failed","missing_obligations","pytest_cases","relay_api_calls","duration"))+" |")
    text += ["\n## Certification blockers\n",*s["inventory"]["issues"],"\nExact failures and single-case replay commands are in GOLDEN_FAILURES.jsonl. All source bytes and frozen digests are in NORMATIVE_SOURCE_HASHES.json and FROZEN_EXPECTATIONS/MANIFEST.json.\n"]
    (OUT/"COVERAGE_REPORT.md").write_text("\n".join(text),encoding="utf-8")
    return s


def main():
    p=argparse.ArgumentParser();p.add_argument("--verify-inventory",action="store_true");p.add_argument("--verify-freeze",action="store_true")
    p.add_argument("--case-id");p.add_argument("--summary",action="store_true");p.add_argument("--json",action="store_true");p.add_argument("--publish-evidence")
    args=p.parse_args()
    if args.case_id:
        ids={c["case_id"] for c in read_rows(OUT/"CASES.jsonl")}
        if args.case_id not in ids:p.error("Unknown exact case ID")
        return subprocess.call([sys.executable,"-m","pytest","-q","tests/golden_v4/","--v4-case-id",args.case_id],cwd=ROOT)
    if args.verify_freeze:
        issues=verify_freeze();print(json.dumps({"verified":not issues,"issues":issues},indent=2));return int(bool(issues))
    if args.verify_inventory:
        result=inventory();print(json.dumps({k:v for k,v in result.items() if k!="missing_clause_obligations"},indent=2));return int(not result["certified"])
    result=publish(args.publish_evidence) if args.publish_evidence else (json.loads((OUT/"COVERAGE.json").read_text(encoding="utf-8")) if args.summary and (OUT/"COVERAGE.json").exists() else summary())
    if args.json:print(json.dumps(result,indent=2))
    else:
        print(result["verdict"]);print(f'{result["executed"]}/{result["frozen_cases"]} cases executed; {len(result["failures"])} failing cases')
        for issue in result["inventory"]["issues"]:print(issue)
    return 0


if __name__=="__main__":raise SystemExit(main())
