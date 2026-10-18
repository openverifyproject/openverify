"""Reconcile executed assertions without importing historical obligation inventories.

This is intentionally fail-closed: unreviewed assertions are labeled UNREVIEWED,
and a linked representative never means a whole canonical domain is complete.
"""
import collections
import gzip
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'conformance/golden-v4/reconciliation-v2'


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines() if s]


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, default=str) + '\n', encoding='utf-8')


def compressed_rows(name, values):
    with (OUT / name).open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as stream:
        for value in values:
            stream.write((json.dumps(value, default=str) + '\n').encode())


def line(path, text):
    return next(i for i, s in enumerate((ROOT / path).read_text(encoding='utf-8').splitlines(), 1) if text in s)


def main():
    canonical = {r['requirement_id']: r for r in rows(ROOT / 'conformance/golden-v4/canonical-review-v2/CANONICAL_REQUIREMENTS.jsonl')}
    primary = {i: r for i, r in canonical.items() if r['record_kind'] in ('SEMANTIC_REQUIREMENT', 'WHOLE_ROOT_STRUCTURAL_REQUIREMENT')}
    latest = Path((ROOT / '.pytest_cache/golden-v4/LATEST').read_text())
    original = rows(latest / 'results.jsonl')
    regressions = rows(OUT / 'REGRESSION_RESULTS.jsonl')
    cases = {r['case_id']: r for r in rows(ROOT / 'conformance/golden-v4/FROZEN_EXPECTATIONS/cases.jsonl')}
    assert len(original) == len(cases) == len({r['case_id'] for r in original})
    assert {r['case_id'] for r in original} == set(cases)
    # Exact generic assertion and SUT paths were read before attaching these links.
    compare_path = 'tests/golden_v4/reporters/runner.py'
    compare_line = line(compare_path, 'if not compare(case["expected"],actual)')
    root_by_type = {(r['hierarchy'][0], r['hierarchy'][-1]): i for i, r in primary.items() if r['record_kind'] == 'WHOLE_ROOT_STRUCTURAL_REQUIREMENT'}
    explicit = {
        'V4.VCP.DECISION.DEST': ['CM.VCP.DECISION.DESTINATION'],
        'V4.VCP.EVIDENCE.MEANING': ['CM.VCP.KNOWLEDGE.EVIDENCE'],
        'V4.VCP.RESOURCE.PRESENCE_BINARY': ['CM.VCP.RES.KINDS'],
        'V4.VCP.RESOURCE.PRESENCE_TRINARY': ['CM.VCP.RES.KINDS'],
        'V4.VCP.RESOURCE.RANGE_ORDER': ['CM.VCP.RES.ORDER'],
        'V4.VCP.PORT.HANDLING': ['CM.VCP.DATA.PORT_HANDLING'],
        'V4.VCP.PORT.DEFAULT': ['CM.VCP.DATA.DEFAULT.CONSTANT'],
        'V4.VCP.RESULT.PROJECTION': ['CM.VCP.RESULT.FLATTEN'],
        'V4.VCP.AGG.HANDLING_MAP': ['CM.VCP.AGG.CONFIG'],
        'V4.VCP.AGG.SCORE': ['CM.VCP.AGG.MIN', 'CM.VCP.AGG.MAX', 'CM.VCP.AGG.MEAN', 'CM.VCP.AGG.WEIGHTED.SCORE'],
        'V4.VCP.AGG.LOGICAL': ['CM.VCP.AGG.ALL', 'CM.VCP.AGG.ANY', 'CM.VCP.AGG.MAJORITY.PASS', 'CM.VCP.AGG.MAJORITY.FAIL', 'CM.VCP.AGG.MAJORITY.TIE'],
        'V4.VCP.RESOLVE.HANDLER': ['CM.VCP.DATA.RESOLVE_ALL'],
        'V4.VCP.RESOLVE.CONSUMER': ['CM.VCP.DATA.RESOLVE_ALL'],
    }
    reducer_id = {'ALL': 'CM.VCP.AGG.ALL', 'ANY': 'CM.VCP.AGG.ANY', 'MIN_SCORE': 'CM.VCP.AGG.MIN', 'MAX_SCORE': 'CM.VCP.AGG.MAX', 'AVERAGE': 'CM.VCP.AGG.MEAN', 'WEIGHTED_AVERAGE': 'CM.VCP.AGG.WEIGHTED.SCORE'}
    reconciled = []
    for observed in original:
        c = cases[observed['case_id']]
        family, action, s = c['family'], c['action'], c['stimulus']
        links = list(explicit.get(family, []))
        scope = 'Reviewed finite representative/projection only; no full unbounded requirement coverage claimed.'
        if family in ('V4.VCP.AGG.LOGICAL', 'V4.VCP.AGG.SCORE'):
            reducer = s['reducer']
            links = [reducer_id[reducer]] if reducer in reducer_id else [i for i in explicit[family] if '.MAJORITY.' in i]
        if action == 'wire':
            t = s.get('object_type')
            i = root_by_type.get(('VCP', t)) or root_by_type.get(('PROVIDER', t))
            links = [i] if i else []
            scope = 'Required-field presence/wire projection only; not whole-root semantic or arbitrary-value exhaustiveness.'
        if action == 'coordinate':
            links = []
            scope = 'SCAFFOLD_ONLY: membership check plus constant CONDITIONAL result; no source reachability or runtime behavior assertion.'
        for i in links:
            assert i in primary, i
        # Domain-specific predicates must not be attached to unrelated reducer cases.
        reconciled.append(dict(case_id=c['case_id'], family=family, canonical_ids=links,
            hierarchy_leaves=[primary[i]['hierarchy'] for i in links],
            source_refs={i: primary[i]['sources'] for i in links},
            assertion={'path': compare_path, 'line': compare_line, 'relation': 'type-aware exact expected/actual comparison',
                       'sut_path': 'tests/golden_v4/sut.py', 'action': action},
            expected=c['expected'], actual=observed['actual'], status=observed['status'],
            review='PARTIAL_ASSERTION_LINK_REVIEWED' if links else ('SCAFFOLD_NOT_BEHAVIORAL_COVERAGE' if action == 'coordinate' else 'UNREVIEWED_NO_COVERAGE_CREDIT'),
            scope=scope, duration=observed['duration'], repro=observed['rerun']))
    for r in regressions:
        links = r['canonical_ids']
        assert all(i in primary for i in links), links
        reconciled.append({**r, 'hierarchy_leaves': [primary[i]['hierarchy'] for i in links],
            'review': 'PARTIAL_ASSERTION_LINK_REVIEWED' if links else 'CONTROL_ASSERTION_NO_SEMANTIC_COVERAGE',
            'scope': 'Snapshot relation representative, separately authored correction, or attempted live witness; FAIL is not coverage discharge.'})
    compressed_rows('TEST_RECONCILIATION.jsonl.gz', reconciled)
    # Independent failure adjudication; these are exact executed case IDs.
    failures = []
    corrections = []
    for r in original:
        if r['status'] != 'FAIL':
            continue
        i = r['case_id']
        if i.startswith('V4.VCP.AGG.WEIGHT_SIGN_2.'):
            category = 'incorrect frozen expectation'
            rationale = 'Invalid original weight configuration is AGGREGATE_CONFIG; AGGREGATE_INPUT belongs to reduction/member/retained-total failure. Separate revised cases verify the six corrections.'
            corrected = {'error': 'AGGREGATE_CONFIG'}
            source = 'spec/draft/aggregation.md; spec/draft/conformance.md; original-weight configuration versus retained-total semantics'
        elif i == 'V4.VCP.SCHEMA.FULL.ANNOTATION':
            category = 'incorrect frozen expectation'
            rationale = 'description must be a string under the Draft metaschema. An object containing $ref there is invalid schema, independently of annotation traversal. The separate corrected default-payload case is valid.'
            corrected = {'accepted': False}
            source = 'Draft2020-12 validation section9.1; spec/draft/dataflow.md valid Draft requirement'
        elif i.startswith('V4.AUDIT.INVENTORY.'):
            category = 'incorrect frozen expectation'
            rationale = 'Frozen assertion demands certification/PROVED for an inventory with admitted missing/unproved obligations. A fail-closed audit must return false; test green cannot establish completeness.'
            corrected = {'accepted': False}
            source = 'tools/golden_v4/report.py:inventory; REDUCTION_LEDGER entries remain unproved; canonical full test mapping incomplete'
        elif 'UNKNOWN_METHOD' in i:
            category = 'production defect'
            rationale = 'Valid unknown JSON-RPC method requires -32601. Session validation closes before the server returns that error; observed EOF. Production not modified.'
            corrected = r['expected']
            source = 'provider-contract/spec/draft/transports.md unknown-method rule; src/openverify/relay/adapters/server.py session.runner_message before handler try'
        else:
            category = 'production defect'
            rationale = 'Valid custom empty membership is rejected by unchanged validate_graph nonempty check. Current approved semantics permit that declaration; historical expected acceptance is retained.'
            corrected = r['expected']
            source = 'spec/draft/dataflow.md custom empty membership; src/openverify/dataflow.py nonempty membership check'
        spec_path = 'provider-contract/spec/draft/transports.md' if 'UNKNOWN_METHOD' in i else 'spec/draft/aggregation.md' if 'WEIGHT_SIGN' in i else 'spec/draft/dataflow.md'
        anchor = 'Unknown methods receive' if 'UNKNOWN_METHOD' in i else 'nonnegative weight' if 'WEIGHT_SIGN' in i else 'For a custom Aggregate' if category == 'production defect' else 'All port/config/judgment'
        spec_line = next((n for n, text in enumerate((ROOT / spec_path).read_text(encoding='utf-8').splitlines(), 1) if anchor in text), 1)
        failures.append(dict(case_id=i, profile='existing-v4', category=category, rationale=rationale, source=source,
                             source_reference={'path': spec_path, 'line': spec_line},
                             expected=r['expected'], actual=r['actual'], current_expected=corrected, repro=r['rerun']))
        if category == 'incorrect frozen expectation':
            corrections.append(dict(case_id=i, historical_expected=r['expected'], revised_expected=corrected, source=source, rationale=rationale))
    for r in regressions:
        if r['status'] == 'FAIL':
            failures.append(dict(case_id=r['case_id'], profile='revision-v2', category='production defect',
                rationale='Custom empty graph rejected' if 'CUSTOM.EMPTY' in r['case_id'] else 'CANCELLED unavailable information/Decision classified PRODUCER_NOT_EXECUTED instead of snapshot-required OUTPUT_MISSING',
                source='spec/draft/dataflow.md snapshot classifier and custom membership; unchanged src/openverify/dataflow.py', expected=r['expected'], actual=r['actual'], repro=r['repro']))
    (OUT / 'FAILURES.jsonl').write_text('\n'.join(json.dumps(r) for r in failures) + '\n', encoding='utf-8')
    dump('EXPECTATION_CORRECTIONS.json', corrections)
    linked = {i for r in reconciled for i in r['canonical_ids']}
    passing = {i for r in reconciled if r['status'] == 'PASS' for i in r['canonical_ids']}
    failing = {i for r in reconciled if r['status'] == 'FAIL' for i in r['canonical_ids']}
    # Both directions retain every executed ID, including deliberately uncredited assertions.
    dump('REQUIREMENT_ASSERTION_LINKS.json', {
        i: {'hierarchy': r['hierarchy'], 'passing_case_ids': [c['case_id'] for c in reconciled if i in c['canonical_ids'] and c['status'] == 'PASS'],
            'failing_case_ids': [c['case_id'] for c in reconciled if i in c['canonical_ids'] and c['status'] == 'FAIL'],
            'closure': 'NOT_FULLY_RECONCILED' if i in linked else 'NO_REVIEWED_EXECUTABLE_LINK',
            'note': 'Passing representatives are not proof that all this requirement domain is covered.'} for i, r in primary.items()})
    meta = json.loads((latest / 'execution.json').read_text())
    profiles = {}
    for mode in ['cheap', 'runtime', 'integration']:
        selected = [r for r in original if r['execution_mode'] == mode]
        profiles[mode] = {'executed': len(selected), 'counts': dict(collections.Counter(r['status'] for r in selected)),
                          'case_duration_sum_seconds': sum(r['duration'] for r in selected),
                          'relay_api_calls': sum(r['relay_api_calls'] for r in selected),
                          'timing_scope': 'Partition of one full suite run, not three separately timed profile processes.'}
    summary = dict(canonical_semantic=582, schema_root_predicates=33, original_v4=meta,
        revision_execution=json.loads((OUT / 'REGRESSION_EXECUTION.json').read_text()),
        revision_counts=dict(collections.Counter(r['status'] for r in regressions)), revision_executed=len(regressions),
        revision_case_duration_sum_seconds=sum(r['duration'] for r in regressions),
        existing_profiles=profiles, failure_categories=dict(collections.Counter(r['category'] for r in failures)),
        canonical_primary_ids=len(primary), primary_ids_with_reviewed_partial_links=len(linked),
        primary_ids_with_some_passing_links=len(passing), primary_ids_with_failing_links=len(failing),
        primary_ids_without_reviewed_links=len(set(primary)-linked), fully_reconciled_requirements=0,
        case_link_review= dict(collections.Counter(r['review'] for r in reconciled)),
        unique_executed_ids=len(reconciled), certification='NOT CERTIFIED',
        limitation='This begins assertion reconciliation. Remaining assertions are explicitly UNREVIEWED, not implicitly coverage. Full canonical mathematical/source closure is distinct from complete Golden coverage.')
    dump('EXECUTION_REPORT.json', summary)
    compressed_rows('EXISTING_RESULTS.jsonl.gz', original)
    for src, dst in [(ROOT / '.pytest_cache/golden-v4-existing-junit.xml', OUT / 'EXISTING_JUNIT.xml.gz'), (ROOT / '.pytest_cache/golden-v4-revision-junit.xml', OUT / 'REGRESSION_JUNIT.xml.gz')]:
        with src.open('rb') as inp, dst.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as stream:
            shutil.copyfileobj(inp, stream)
    # Freeze verification remains strict without an explicit source revision.
    frozen = json.loads((ROOT / 'conformance/golden-v4/FROZEN_EXPECTATIONS/MANIFEST.json').read_text())
    integrity = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in frozen['files'].items()}
    assert all(integrity.values()), integrity
    dump('FROZEN_INTEGRITY.json', integrity)
    print(json.dumps({k: v for k, v in summary.items() if k not in ['original_v4']}, indent=2))


if __name__ == '__main__':
    main()
