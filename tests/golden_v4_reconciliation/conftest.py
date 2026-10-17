"""Versioned reconciliation evidence; original Golden files remain immutable."""
import json
import sys
import time
import ast
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'conformance/golden-v4/reconciliation-v2'


@lru_cache
def assertion_locus(path, function):
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    owner = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == function)
    return {'path': Path(path).relative_to(ROOT).as_posix(), 'function': function,
            'assertions': [{'line': n.lineno, 'predicate': ast.unparse(n.test)} for n in ast.walk(owner) if isinstance(n, ast.Assert)]}


def pytest_sessionstart(session):
    session.config._reconciliation_start = time.monotonic()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    if report.when != 'call':
        return
    case = item.callspec.params.get('case') if hasattr(item, 'callspec') else None
    case_id = case['case_id'] if case else (item.callspec.id if hasattr(item, 'callspec') else 'V4.REVISION.' + item.name.upper())
    links = list(getattr(item, 'canonical_ids', []))
    if case and 'status' in case['expected']:
        e = case['expected']
        if e['status'] != 'AVAILABLE':
            links += {'BLOCK': ['CM.VCP.DATA.RESOLVE_BLOCK.RESOLUTION'], 'OMIT': ['CM.VCP.DATA.RESOLVE_OMIT.INPUT', 'CM.VCP.DATA.RESOLVE_OMIT.PROVENANCE'], 'DEFAULT': ['CM.VCP.DATA.RESOLVE_DEFAULT.SUBSTITUTE', 'CM.VCP.DATA.RESOLVE_DEFAULT.PROVENANCE']}[e['handler']]
        else:
            links += ['CM.VCP.DATA.RESOLVE_AVAILABLE.PROVENANCE']
    row = dict(case_id=case_id, selector=item.nodeid, status='PASS' if report.passed else 'FAIL',
               duration=report.duration, expected=getattr(item, 'expected', None),
               actual=getattr(item, 'actual', None), canonical_ids=sorted(set(links)),
               source='spec/draft/dataflow.md', assertion=assertion_locus(str(item.path), item.function.__name__),
               repro='python -m pytest -q ' + item.nodeid,
               failure=str(report.longrepr) if report.failed else None)
    item.config._reconciliation_rows = getattr(item.config, '_reconciliation_rows', []) + [row]


def pytest_sessionfinish(session, exitstatus):
    rows = getattr(session.config, '_reconciliation_rows', [])
    (OUT / 'REGRESSION_RESULTS.jsonl').write_text('\n'.join(json.dumps(r, default=str) for r in rows) + '\n', encoding='utf-8')
    (OUT / 'REGRESSION_EXECUTION.json').write_text(json.dumps({'exitstatus': int(exitstatus), 'executed': len(rows), 'wall_seconds': time.monotonic() - session.config._reconciliation_start, 'argv': sys.argv, 'python': sys.version}, indent=2) + '\n', encoding='utf-8')
