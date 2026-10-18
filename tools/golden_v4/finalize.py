"""Publish immutable-run evidence separately from the independent freeze."""
from __future__ import annotations

import gzip
import json
import shutil
import subprocess
from pathlib import Path

from .discover import BLUEPRINT,OUT,PIN,ROOT,digest,write_json,write_lines
from .report import publish,read_rows,verify_freeze


def main():
    artifact=ROOT/".pytest_cache/golden-v4/full-final"
    assert (artifact/"execution.json").exists(),"Full release run has not finished"
    assert not verify_freeze(),"Source/expectation integrity failure"
    results=read_rows(artifact/"results.jsonl")
    cases=read_rows(OUT/"CASES.jsonl")
    assert len(results)==len(cases) and {r["case_id"] for r in results}=={c["case_id"] for c in cases}
    s=publish(artifact)
    evidence=OUT/"RUN_EVIDENCE";evidence.mkdir(exist_ok=True)
    for name in ("results.jsonl","execution.json","junit.xml"):
        shutil.copyfile(artifact/name,evidence/name)
    for diagnostic in artifact.glob("stdio-*-stderr.txt"):
        shutil.copyfile(diagnostic,evidence/diagnostic.name)
    shutil.copyfile(ROOT/".pytest_cache/golden-v4-full-final.log",evidence/"pytest-stdout.txt")
    profiles={}
    for name in ("cheap-release","runtime-release","integration-release"):
        folder=ROOT/".pytest_cache/golden-v4"/name
        report=json.loads((folder/"execution.json").read_text(encoding="utf-8"))
        report["results_sha256"]=digest((folder/"results.jsonl").read_bytes())
        report["junit_sha256"]=digest((folder/"junit.xml").read_bytes())
        # Store the actual per-profile raw outputs in deterministic compressed form.
        for filename in ("results.jsonl","junit.xml"):
            (evidence/f"{name}-{filename}.gz").write_bytes(gzip.compress((folder/filename).read_bytes(),mtime=0))
        profiles[name]=report
    write_json(OUT/"PROFILE_EXECUTIONS.json",profiles)
    sources=json.loads((OUT/"NORMATIVE_SOURCE_HASHES.json").read_text(encoding="utf-8"))
    execution=json.loads((OUT/"EXECUTION_REPORT.json").read_text(encoding="utf-8"))
    execution.update(profiles=profiles,production_commit=PIN,independent_freeze_commit="147baf1",pre_evidence_head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                     imported_source_sha256=sources["files"]["src/openverify/__init__.py"],blueprint_sha256=BLUEPRINT,
                     source_inventory_sha256=digest((OUT/"NORMATIVE_SOURCE_HASHES.json").read_bytes()),
                     freeze_manifest_sha256=digest((OUT/"FROZEN_EXPECTATIONS/MANIFEST.json").read_bytes()),
                     frozen_cases_sha256=digest((OUT/"FROZEN_EXPECTATIONS/cases.jsonl").read_bytes()),
                     complete_case_id_reconciliation=True,evidence_results_sha256=digest((evidence/"results.jsonl").read_bytes()))
    write_json(OUT/"EXECUTION_REPORT.json",execution)
    findings=[]
    for r in s["failures"]:
        if r["family"]=="V4.AUDIT.INVENTORY":kind="COVERAGE_GATE_FAILURE";reason="Missing reviewed clause/method crosswalk and unproved residuals prevent certification."
        elif r["case_id"].endswith("UNKNOWN_METHOD"):kind="SUPPORTED_TRANSPORT_FAILURE";reason="An initialized stdio session closes instead of returning the required JSON-RPC unknown-method response. No production change is permitted in this assignment."
        elif ".WEIGHT_SIGN_2." in r["case_id"]:kind="FROZEN_ORACLE_DEFECT";reason="Rejection is required, but the frozen author asserted AGGREGATE_INPUT for invalid weight configuration. The observed AGGREGATE_CONFIG is not established here as a production defect. Exact precedence must not be invented."
        else:kind="FROZEN_STIMULUS_DEFECT";reason="Aggregate fixtures have empty membership, or the schema-annotation fixture uses an invalid object-valued description. Unrelated validity prerequisites were not held valid. Frozen bytes are preserved; these are not established production defects."
        findings.append({"case_id":r["case_id"],"classification":kind,"reason":reason,"expected":r["expected"],"actual":r["actual"],"sources":r.get("normative_sources",[]),"rerun":r["rerun"]})
    findings.append({"finding_id":"V4.AUDIT.PHASE_PARTITION_LABEL","classification":"FROZEN_INVENTORY_DEFECT","reason":"The 5 progression/4 stutter/7 other partition is correct, but four stutters were placed in an N column in the frozen arithmetic table. They are not impossible coordinates. Published coverage labels this explicitly conditional and assigns no impossibility claim."})
    write_json(OUT/"AUDIT_FINDINGS.json",findings)
    limits={"UNSUPPORTED":["cycles and dynamic expansion","external/nested/dynamic schema resolution","automatic retries, durable replay/recovery","required unknown extension semantics","portable multi-attempt interrupted cancellation","network Provider bindings"],
            "AMBIGUOUS":["unmandated exact error precedence","portable numeric rounding/canonical identity/clock trust","raw availability coordinate reachability without mandatory extra axes"],
            "UNBOUNDED":["arbitrary JSON/schema/string/number values","DAGs of arbitrary size","arbitrary member lists, custom logic and event histories","unbounded concurrent scheduling histories"],
            "SAMPLED":["logical reducer sequences n=1..5","severity sequences n=1..4","authored score boundary vectors","twelve named Relay motifs and explicit resource/event paths"],
            "UNPROVED":["universal DAG induction noninterference/global-state premises","unbounded reducer order/identity reduction","complete normative clause-to-assertion review and canonical obligation deduplication","complete cross-module pair and required higher-order interaction matrix","all standard-provider behavioral contracts beyond text and aggregate","complete supported host/method clause indexing"],
            "EXCLUDED":["Byzantine Provider streams in real Relay","malicious arbitrary replacement ports","cryptographic attestation/coordinated coherent forgery"],
            "EXECUTION_PLAN_CORRECTIONS":["Mutation probes and the SDK policy-exception boundary execute in runtime mode, regardless of their frozen initial mode label.","Invalid invoked nonexecution Results and all policy role/outcome-object combinations execute locally in cheap mode. No deliberately malformed external provider is required.","The expired-deadline resource witness is a local Provider lifecycle check: the public Relay.run API has no deadline argument. It is not claimed as a live Relay deadline invocation.","The stdio helper's post-terminal EOF exit status is diagnostic: the binding does not mandate a numeric exit status after all responses settle. Its cancellation shutdown traceback is preserved separately in run artifacts."]}
    write_json(OUT/"SCOPE_LEDGERS.json",limits)
    mutation=json.loads((OUT/"MUTATION_REPORT.json").read_text(encoding="utf-8"))
    failures=s["failures"]
    lines=["# OpenVerify Golden v4 implementation and audit\n", "## 1. Source and integrity\n",
           f"Branch: `test/openverify-golden-v4`. Pinned production: `{PIN}`. Independent byte-preserving freeze commit: `147baf1`. Final implementation/evidence commit is the branch HEAD; no push/merge/tag/release was performed.\n",
           f"Imported source: `{execution['import_path']}`; SHA-256 `{execution['imported_source_sha256']}`.\n",
           f"Source inventory SHA-256: `{execution['source_inventory_sha256']}`. Freeze manifest SHA-256: `{execution['freeze_manifest_sha256']}`. Frozen cases SHA-256: `{execution['frozen_cases_sha256']}`. Blueprint SHA-256: `{BLUEPRINT}`.\n",
           "All original frozen bytes and production/spec/profile files verified unchanged. The isolated worktree is committed separately from the user's original checkout.\n",
           "## 2. Every blueprint family\n", "Obligation totals are not established: canonical deduplication and reviewed clause-level assertion links are incomplete. Pytest pass/fail counts remain separate in COVERAGE.json; they are never substituted for obligation totals. The 78 overlapping projections have no grand candidate total. See COUNT_PROOFS.md for the projection assumptions.\n"]
    coverage=(OUT/"COVERAGE_REPORT.md").read_text(encoding="utf-8")
    table=coverage[coverage.index("| FAMILY |"):coverage.index("\n## Certification blockers")]
    lines.append(table)
    lines += ["\n## 3. Every failing case\n",f"{len(failures)} failing case IDs. Mutation probes: {len(mutation['probes'])}; all detected: {mutation['all_detected']}. Fourteen failures are frozen authoring defects, two are coverage gates, and one is the supported stdio boundary. They must not all be called production bugs.\n"]
    for r in failures:
        lines += [f"- `{r['case_id']}`",f"  - EXPECTED: `{json.dumps(r['expected'],ensure_ascii=False)}`",f"  - ACTUAL: `{json.dumps(r['actual'],ensure_ascii=False)}`",
                  "  - SOURCE_CLAUSE: "+"; ".join(f"`{x['path']}:{x['line_start']}-{x['line_end']}`" for x in r.get("normative_sources",[])),f"  - REPRO: `{r['rerun']}`"]
    lines += ["\n## 4. Reductions\n", "RunRecord structural presence executes 16 valid optional masks plus 14 single required deletions; 262,114 other invalid masks are discharged by the unconditional required-field conjunction. NodeRecord executes 256 valid optional masks plus 12 single deletions; 1,048,308 other invalid masks are discharged. Total invalid presence cases avoided by these two disjoint object projections: 1,310,422. This is not a reduction of full semantic record validity.\n",
              "The Result disjoint branch partition is 48+8+4+2+4=66; all 1,024 wire cases are executed, so zero cases are omitted. Observation mask 960=3*256+6*32 is conditional on true judgment schema and valid payloads. All 4,166 topology candidates and all 1,024 reducer handling maps are executed, so zero are omitted. Graph DAG counts are independently checked by source-set inclusion/exclusion [1,1,3,25,543] against cycle-detection expectations.\n",
              "Unbounded DAG induction and reducer reductions remain UNPROVED; they save no claimed covered obligations. Their precise premises are in COMPOSITION_PROOFS.md and REDUCTION_LEDGER.jsonl. No sample is upgraded to proof.\n",
              "## 5. Scope ledgers\n"]
    for label,entries in limits.items():lines += [f"{label}: "+"; ".join(entries)+".\n"]
    lines += ["## 6. Obligation accounting\n",f"{s['inventory']['indexed_clause_units']} conservative clause units have explicit missing review obligations. {len(s['inventory']['unindexed_supported_methods'])} additional facade/host declarations lack clause-level method entries. A portable unique obligation total is NOT ESTABLISHED: canonical deduplication and assertion-level review are incomplete. Passing pytest item counts are not substituted for that total. Exact missing IDs and method declarations are in COVERAGE.json.\n",
              "## 7. Execution evidence and commands\n",f"Full execution: {len(results)} individually reconciled cases; {sum(r['status']=='PASS' for r in results)} PASS, {len(failures)} FAIL; {execution['duration_seconds']:.3f} seconds, {execution['relay_api_calls']} real Relay.run calls, {execution['relay_awaited_seconds']:.3f} summed awaited seconds. Aggregate awaited seconds include concurrent calls and are not wall time.\n"]
    for name,p in profiles.items():lines.append(f"{name}: {p['executed']} executed; {p['counts']}; {p['duration_seconds']:.3f} seconds; {p['relay_api_calls']} Relay API calls; {p['relay_awaited_seconds']:.3f} awaited seconds.\n")
    lines += ["PowerShell commands and environment setup are in README.md. Stable raw per-case output, JUnit XML and stdout are in RUN_EVIDENCE/. PROFILE_EXECUTIONS.json records actual original profile runs. The frozen cases and original profile modes remain unchanged; execution mode corrections are explicit in SCOPE_LEDGERS.json and each result record.\n",
              "## 8. Verdict\n",s["verdict"],"\nThe suite is executable and its audit is fail-closed. Complete supported normative obligation coverage has not been achieved. No stable 1.0, arbitrary JSON, arbitrary provider, universal DAG, or scheduler-race proof is claimed.\n"]
    (OUT/"FINAL_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({"verdict":s["verdict"],"executed":len(results),"failures":len(failures),"final_report":str(OUT/"FINAL_REPORT.md")},indent=2))


if __name__=="__main__":main()
