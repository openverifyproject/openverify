"""One assertion failure and persisted identity per frozen candidate."""
from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
ARTIFACTS=None
STREAM=None
RESULTS=[]
COLLECTED=[]
START=0
META={}


@lru_cache
def all_cases():
    return [json.loads(line) for line in (ROOT/"conformance/golden-v4/FROZEN_EXPECTATIONS/cases.jsonl").read_text(encoding="utf-8").splitlines()]


def family_cases(family,module):
    return [c for c in all_cases() if c["family"]==family and c["module"]==module]


@lru_cache
def clause_map():
    return {c["clause_id"]:c for c in [json.loads(s) for s in (ROOT/"conformance/golden-v4/NORMATIVE_CLAUSES.jsonl").read_text(encoding="utf-8").splitlines()]}


def source_refs(case):
    grouped={}
    for cid in case["normative_clauses"]:
        c=clause_map()[cid]
        g=grouped.setdefault(c["path"],{"path":c["path"],"line_start":c["line_start"],"line_end":c["line_end"],"source_sha256":c["source_sha256"]})
        g["line_start"]=min(g["line_start"],c["line_start"]);g["line_end"]=max(g["line_end"],c["line_end"])
    if not grouped and case["action"]=="error_name":return case["stimulus"]["sources"]
    return list(grouped.values())


def compare(expected,actual):
    # Exact JSON type identity: True cannot accidentally match numeric 1.
    if isinstance(expected,(int,float)) and not isinstance(expected,bool) and isinstance(actual,(int,float)) and not isinstance(actual,bool):return expected==actual
    if type(expected) is not type(actual):return False
    if isinstance(expected,dict):return expected.keys()==actual.keys() and all(compare(v,actual[k]) for k,v in expected.items())
    if isinstance(expected,list):return len(expected)==len(actual) and all(compare(a,b) for a,b in zip(expected,actual))
    return expected==actual


def run_case(case,request):
    from ..sut import execute
    actual=json.loads(json.dumps(execute(copy.deepcopy(case),request.node),ensure_ascii=False,allow_nan=False))
    request.node.v4_actual=actual
    if not compare(case["expected"],actual):
        sources=";".join(f'{r["path"]}:{r["line_start"]}-{r["line_end"]}' for r in source_refs(case))
        raise AssertionError(f'{case["case_id"]} | {case["family"]} | {sources} | EXPECTED {json.dumps(case["expected"],ensure_ascii=False)} | OBSERVED {json.dumps(actual,ensure_ascii=False,default=str)} | REPRO python -m tools.golden_v4.report --case-id "{case["case_id"]}"')
