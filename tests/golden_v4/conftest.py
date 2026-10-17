"""Strict case reconciliation, integrity verification and per-case persistence."""
from __future__ import annotations

import json
import importlib.metadata
import os
import sys
import time
from collections import Counter
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT))
from tools.golden_v4.report import verify_freeze
from .reporters import runner


def pytest_addoption(parser):
    parser.addoption("--v4-case-id",default=None)


def pytest_sessionstart(session):
    issues=verify_freeze()
    if issues: raise pytest.UsageError("Golden v4 integrity failure: "+json.dumps(issues))
    import openverify
    assert Path(openverify.__file__).resolve().is_relative_to(ROOT/"src"), "Wrong production import"
    runner.START=time.monotonic()
    runner.ARTIFACTS=Path(os.environ.get("GOLDEN_V4_ARTIFACTS",str(ROOT/".pytest_cache/golden-v4/"/Path(str(time.time_ns())))))
    runner.ARTIFACTS.mkdir(parents=True,exist_ok=True)
    runner.STREAM=(runner.ARTIFACTS/"results.jsonl").open("w",encoding="utf-8",newline="\n")
    runner.META={"python":sys.version,"executable":sys.executable,"import_path":openverify.__file__,"argv":sys.argv,"start_monotonic":runner.START,
                 "dependencies":{n:importlib.metadata.version(n) for n in ("pytest","pydantic","jsonschema","mcp","starlette","httpx")}}


def pytest_collection_modifyitems(config,items):
    selected=config.getoption("--v4-case-id")
    ids=[]
    keep=[];removed=[]
    for item in items:
        c=item.callspec.params.get("case") if hasattr(item,"callspec") else None
        if c is None: raise pytest.UsageError("Untagged v4 test: "+item.nodeid)
        ids.append(c["case_id"])
        effective_mode="runtime" if c["action"]=="mutation" or (c["action"]=="sdk_diagnostic" and c["stimulus"]["code"]=="POLICY_ERROR") else c["execution_mode"]
        if c["action"]=="policy_role" or (c["action"]=="invoked_result" and c["classification"]=="INVALID"):effective_mode="cheap"
        item.v4_execution_mode=effective_mode
        for mark in ("golden_v4",effective_mode,"direct"):
            item.add_marker(mark)
        layer=c["family"].split(".")[1].lower()
        if layer in {"vcp","provider","relay"}:item.add_marker(layer)
        for word in ("result","decision","aggregate","policy","graph","scheduler","port","guard","record","binding"):
            if word in c["family"].lower() or (word=="aggregate" and ".AGG." in c["family"]):item.add_marker(word)
        item.add_marker("invalid" if c["classification"]=="INVALID" else "valid")
        if c["action"] in {"coordinate","phase","weight_proof","audit"}:item.add_marker("proof_check")
        if c["action"] in {"motif","route","lineage","guard_pointer"}:item.add_marker("composition")
        if c["action"] in {"lineage","record_compatibility","policy_order","cancel_record"}:item.add_marker("provenance")
        if c["action"] in {"weight_proof","reduce"}:item.add_marker("property")
        if selected and c["case_id"] != selected:removed.append(item)
        else:keep.append(item)
    if len(ids)!=len(set(ids)):raise pytest.UsageError("Duplicate collected case IDs")
    frozen={c["case_id"] for c in runner.all_cases()}
    if set(ids)!=frozen:raise pytest.UsageError("Collection differs from freeze: "+str(sorted(frozen-set(ids))[:20]))
    if selected:
        if not keep:raise pytest.UsageError("Unknown case ID: "+selected)
        items[:]=keep;config.hook.pytest_deselected(items=removed)
    runner.COLLECTED=ids


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    if report.when == "call":
        c=item.callspec.params["case"]
        row={**c,"frozen_execution_mode":c["execution_mode"],"execution_mode":item.v4_execution_mode,"normative_sources":runner.source_refs(c),"actual":getattr(item,"v4_actual",{"exception":str(call.excinfo.value) if call.excinfo else None}),
             "status":"PASS" if report.passed else "FAIL","duration":report.duration,
             "relay_api_calls":getattr(item,"v4_relay_calls",0),"relay_awaited_seconds":getattr(item,"v4_relay_seconds",0),
             "rerun":f'python -m tools.golden_v4.report --case-id "{c["case_id"]}"',"pytest_selector":item.nodeid}
        if hasattr(item,"v4_rejection"):row["rejection_detail"]=item.v4_rejection
        if hasattr(item,"v4_mutation_evidence"):row["mutation_evidence"]=item.v4_mutation_evidence
        report.user_properties.extend([(key,str(row[key])) for key in ("case_id","family","classification","execution_mode","rerun")])
        if report.failed:
            sources=";".join(f'{r["path"]}:{r["line_start"]}-{r["line_end"]}' for r in row["normative_sources"])
            report.longrepr=str(report.longrepr)+f'\n{c["case_id"]} | {c["family"]} | {sources} | EXPECTED {json.dumps(c["expected"])} | OBSERVED {json.dumps(row["actual"],default=str)} | REPRO {row["rerun"]}'
        runner.STREAM.write(json.dumps(row,ensure_ascii=False,default=str)+"\n");runner.STREAM.flush()
        runner.RESULTS.append({k:v for k,v in row.items() if k not in {"stimulus","normative_clauses"}})


def pytest_sessionfinish(session,exitstatus):
    runner.STREAM.close()
    runner.META.update(exitstatus=int(exitstatus),duration_seconds=time.monotonic()-runner.START,
                       collected=len(runner.COLLECTED),executed=len(runner.RESULTS),counts=dict(Counter(r["status"] for r in runner.RESULTS)),
                       relay_api_calls=sum(r["relay_api_calls"] for r in runner.RESULTS),relay_awaited_seconds=sum(r["relay_awaited_seconds"] for r in runner.RESULTS))
    (runner.ARTIFACTS/"execution.json").write_text(json.dumps(runner.META,indent=2)+"\n",encoding="utf-8")
    (ROOT/".pytest_cache/golden-v4/LATEST").write_text(str(runner.ARTIFACTS),encoding="utf-8")
