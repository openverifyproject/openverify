"""Independently expected snapshot and custom-empty regression assertions.

Local snapshots test the resolver relation; these are not malicious Provider runs.
The live custom capability is compliant and receives only authored JSON inputs.
"""
import asyncio
import json
from pathlib import Path

import pytest

from openverify import ProtocolError, Relay, parse_definition
from openverify.dataflow import resolve_inputs
from openverify.model import Graph, Node, NodeRecord
from openverify.relay import provider
from openverify.relay.adapters.catalog import Catalog

ROOT = Path(__file__).resolve().parents[2]
CASES = [json.loads(s) for s in (ROOT / 'conformance/golden-v4/reconciliation-v2/EXPECTATIONS.jsonl').read_text(encoding='utf-8').splitlines()]
SUBJECT = {'id': 'revision-subject', 'type': 'application/json', 'locator': {'snapshot': 17}}
CRITERION = {'id': 'revision-criterion', 'description': 'The custom capability owns this judgment'}
OP = {'capability_id': 'com.example.revision.compute', 'capability_version': '1'}


def result(disposition='EXECUTED', error=False, verdict='PASS'):
    if disposition != 'EXECUTED':
        return {'protocol': 'draft', 'disposition': disposition, 'output': {'reason': 'CANCELLATION' if disposition == 'CANCELLED' else 'GUARD_FALSE'}, 'evidence': [], 'usage': {}}
    if error:
        return {'protocol': 'draft', 'disposition': disposition, 'execution_outcome': 'ERROR', 'evidence': [], 'usage': {}}
    return {'protocol': 'draft', 'disposition': disposition, 'execution_outcome': 'SUCCESS', 'applicability': 'APPLICABLE', 'determination': 'KNOWN', 'verdict': verdict, 'evidence': [], 'usage': {}}


def port(name, schema=True, required=True, handler='BLOCK'):
    p = {'name': name, 'schema': schema, 'required': required, 'on_unavailable': handler}
    if handler == 'DEFAULT':
        p['default'] = {'kind': 'CONSTANT', 'value': 29}
    return p


def node(name, kind='DERIVE'):
    return {'id': name, 'kind': kind, 'operation': OP, 'inputs': [], 'outputs': [], 'bindings': {}, 'config': {}}


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['case_id'])
def test_snapshot_relation(case, request):
    c, expected = case['context'], case['expected']
    request.node.expected = expected
    request.node.canonical_ids = case['canonical_ids']
    if 'preflight_error' in expected:
        target = node('consumer')
        target['inputs'] = [port('input')]
        d = custom_definition()
        d['graph'] = {'nodes': [target], 'edges': []}
        with pytest.raises(ProtocolError) as caught:
            parse_definition(d)
        request.node.actual = {'required': True, 'handler': 'BLOCK', 'preflight_error': caught.value.code}
        assert request.node.actual == expected
        return
    target = node('consumer')
    schema = {'type': 'integer'}
    value = 17
    records, run_values = {}, {}
    producer = node('producer', c['kind'] or 'DERIVE')
    if producer['kind'] in ('EVALUATE', 'AGGREGATE'):
        for name, authored in [('subject', SUBJECT), ('criterion', CRITERION)]:
            producer['inputs'].append(port(name))
            producer['bindings'][name] = {'kind': 'CONSTANT', 'value': authored}
    if producer['kind'] == 'AGGREGATE':
        producer['inputs'].append(port('members'))
        producer['bindings']['members'] = {'kind': 'CONSTANT', 'value': []}
        producer['aggregate_inputs'] = []
    source = None
    if c['source'] == 'CONSTANT':
        source = {'kind': 'CONSTANT', 'value': value}
    elif c['source'] == 'EXTERNAL_REFERENCE':
        source = {'kind': 'EXTERNAL_REFERENCE', 'reference': SUBJECT}
        schema = True
        value = SUBJECT
    elif c['source'] == 'RUN_INPUT':
        source = {'kind': 'RUN_INPUT', 'name': 'authored'}
        if c['candidate'] != 'ABSENT':
            run_values['authored'] = 17
        if c['validation'] == 'FAIL':
            schema = {'type': 'integer', 'minimum': 20}
    elif c['source'] == 'UPSTREAM_OUTPUT':
        role = c['role']
        output = 'result' if role == 'RESULT' else ('decision' if role == 'DECISION' else 'x')
        source = {'kind': 'UPSTREAM_OUTPUT', 'node_id': 'producer', 'output': output}
        state = c['state']
        r = result('SKIPPED' if state == 'NONEXECUTED' else 'CANCELLED' if state == 'CANCELLED' else 'EXECUTED', error=state == 'ERROR')
        if role == 'RESULT':
            value = r
            schema = True
        elif role == 'DECISION':
            value = {'protocol': 'draft', 'kind': 'CONTINUE'}
            schema = True
        if c['validation'] == 'CONSUMER_FAIL':
            schema = {'type': 'object', 'required': ['not_present']} if role != 'INFORMATION' else {'type': 'integer', 'minimum': 20}
        producer_schema = {'type': 'object', 'required': ['not_present']} if c['validation'] == 'PRODUCER_FAIL' else True
        if c['cause'] == 'REJECTED_PRESENT':
            producer_schema = {'type': 'object'} if role == 'DECISION' else {'type': 'integer'}
        producer['outputs'] = [{'name': output, 'role': role, 'schema': producer_schema}]
        if producer['kind'] in ('EVALUATE', 'AGGREGATE') and role != 'RESULT':
            producer['outputs'].append({'name': 'result', 'role': 'RESULT', 'schema': True})
        rec = {'node_id': 'producer', 'kind': producer['kind'], 'operation': OP,
               'upstream_node_ids': [], 'upstream_results': {}, 'input_values': {}, 'input_resolutions': {},
               'started_at': '2026-01-01T00:00:00Z', 'finished_at': '2026-01-01T00:00:01Z',
               'state': state, 'usage': {}, 'information': {}}
        rec['input_values'] = {name: binding['value'] for name, binding in producer['bindings'].items()}
        rec['input_resolutions'] = {name: {'source': binding, 'status': 'AVAILABLE', 'used_default': False, 'value': binding['value']} for name, binding in producer['bindings'].items()}
        if state != 'NONEXECUTED':
            rec.update(executor_ref='authored-local-revision', executor_version='1')
        if producer['kind'] in ('EVALUATE', 'AGGREGATE') or state in ('ERROR', 'NONEXECUTED', 'CANCELLED'):
            rec['result'] = r
        if state == 'SUCCESS':
            if role == 'INFORMATION':
                rec['information'] = {output: value}
            if role == 'DECISION':
                rec['decision'] = value
        if state == 'ERROR':
            cause = c['cause']
            if cause == 'REJECTED_PRESENT':
                rec.update(reason='OUTPUT_INVALID', observation={'outputs': {output: 'rejected'}, 'usage': {}, 'evidence': []})
            elif cause == 'EXPLICIT_MISSING':
                rec.update(reason='OUTPUT_MISSING', observation={'outputs': {}, 'usage': {}, 'evidence': []})
            elif cause == 'EXECUTION_ERROR':
                rec.update(reason='com.example.failure', observation={'outputs': {}, 'usage': {}, 'evidence': [], 'error': {'code': 'com.example.failure', 'message': 'authored'}})
            elif cause == 'RAISED':
                rec['reason'] = 'EXECUTOR_ERROR'
            elif cause == 'VALID_ERROR_RESULT':
                rec['observation'] = {'outputs': {output: value, 'result': r}, 'usage': {}, 'evidence': []}
        if state == 'NONEXECUTED':
            rec['reason'] = 'GUARD_FALSE'
        if state == 'CANCELLED':
            rec['reason'] = 'CANCELLATION'
            raw = c['cause']
            if raw:
                raw_outputs = {} if raw == 'RAW_ABSENT' else {output: 17 if raw == 'RAW_VALID' else 'bad'}
                rec['observation'] = {'outputs': raw_outputs, 'usage': {}, 'evidence': []}
        records['producer'] = NodeRecord.model_validate(rec)
    p = port('input', schema, expected['required'], expected['handler'])
    default_value = {'not_present': 29} if isinstance(schema, dict) and schema.get('required') == ['not_present'] else 29
    if expected['handler'] == 'DEFAULT':
        p['default']['value'] = default_value
    target['inputs'] = [p]
    if source is not None:
        target['bindings']['input'] = source
    graph = Graph.model_validate({'nodes': [producer, target], 'edges': [{'from_node': 'producer', 'to_node': 'consumer'}] if c['source'] == 'UPSTREAM_OUTPUT' else []})
    values, resolutions, blocked = resolve_inputs(graph.nodes[-1], run_values, records, graph)
    resolution = resolutions['input']
    actual = {'status': resolution.status, 'required': p['required'], 'handler': p['on_unavailable'],
              'used_default': resolution.used_default, 'value_present': 'input' in values,
              'invocation_permitted_by_input': not blocked}
    request.node.actual = actual
    assert actual == expected, (case['case_id'], expected, actual)
    if expected['value_present']:
        assert values == {'input': default_value if expected['used_default'] else value}
        assert resolution.value == values['input']
    else:
        assert values == {} and 'value' not in resolution.model_fields_set
    if source is not None:
        from openverify.serialization import to_data
        assert to_data(resolution.source) == source


def custom_definition():
    n = node('custom', 'AGGREGATE')
    for name, value in [('subject', SUBJECT), ('criterion', CRITERION), ('members', [])]:
        n['inputs'].append(port(name))
        n['bindings'][name] = {'kind': 'CONSTANT', 'value': value}
    n['aggregate_inputs'] = []
    n['outputs'] = [{'name': 'result', 'role': 'RESULT', 'schema': True}]
    return {'protocol': 'draft', 'id': 'revision.custom.empty', 'version': '1',
            'subject': SUBJECT, 'criterion': CRITERION, 'judgment_schema': True, 'run_inputs': [],
            'graph': {'nodes': [n], 'edges': []}, 'execution_policy': {'activation': {'executor_ref': 'MANUAL'}, 'selection': {'executor_ref': 'EXPLICIT'}, 'admission': {'strategy': 'ALWAYS'}}}


@pytest.mark.parametrize('verdict', ['PASS', 'FAIL', 'ERROR'], ids=lambda v: 'V4.REVISION.CUSTOM.EMPTY.' + v)
def test_custom_empty_invocation(verdict, request):
    calls = []
    emitted = result(error=verdict == 'ERROR', verdict=verdict)
    request.node.canonical_ids = ['CM.VCP.AGG.MEMBERS.COMPLETE', 'CM.VCP.AGG.MEMBERS.ORDER', 'CM.VCP.DATA.SEMANTIC_SUBJECT.SUBJECT', 'CM.VCP.DATA.SEMANTIC_SUBJECT.CRITERION']
    request.node.expected = {'calls': [{'subject': SUBJECT, 'criterion': CRITERION, 'members': []}], 'result': emitted}

    @provider(provider_id='com.example.revision.provider', capability_id=OP['capability_id'], kind='AGGREGATE', input_schema=True, output_schema=True, config_schema=True)
    async def custom(inputs, config):
        calls.append(inputs)
        return {'result': emitted}

    catalog = Catalog()
    catalog.register(custom)
    try:
        run = asyncio.run(Relay(catalog=catalog).run(parse_definition(custom_definition()), inputs={}, opportunity_id='revision-explicit'))
    except ProtocolError as exc:
        request.node.actual = {'rejection': exc.code, 'calls': calls}
        raise
    request.node.actual = {'calls': calls, 'result': run.results['custom'].model_dump(exclude_none=True)}
    assert calls == request.node.expected['calls']
    from openverify.serialization import to_data
    observed = to_data(run.results['custom'])
    assert all(observed[k] == v for k, v in emitted.items())
    rec = run.record.nodes[0]
    assert rec.input_values == calls[0]
    assert rec.input_resolutions['members'].status == 'AVAILABLE'
    assert rec.input_resolutions['members'].value == []
    assert not rec.input_resolutions['members'].used_default
    assert rec.provider_binding == run.record.provider_bindings['custom']


def test_live_cancellation_snapshot(request):
    from openverify.lifecycle import Cancellation
    token = Cancellation()
    calls = []
    request.node.canonical_ids = ['CM.VCP.DATA.RESOLVE_ALL', 'CM.VCP.DATA.RESOLVE_BLOCK.RESOLUTION']
    request.node.expected = {'producer_state': 'CANCELLED', 'consumer_reason': 'CANCELLATION', 'status': 'OUTPUT_MISSING', 'calls': ['producer']}

    @provider(provider_id='com.example.revision.provider', capability_id=OP['capability_id'], kind='DERIVE', input_schema=True, output_schema=True, config_schema=True)
    async def execute(inputs, config):
        calls.append(config['node'])
        token.cancel('authored cancellation before output acceptance')
        return {'x': 17}

    producer = node('producer')
    producer.update(outputs=[{'name': 'x', 'schema': True, 'role': 'INFORMATION'}], config={'node': 'producer'})
    consumer = node('consumer')
    consumer.update(inputs=[port('x')], bindings={'x': {'kind': 'UPSTREAM_OUTPUT', 'node_id': 'producer', 'output': 'x'}}, config={'node': 'consumer'})
    d = custom_definition()
    d['graph'] = {'nodes': [producer, consumer], 'edges': [{'from_node': 'producer', 'to_node': 'consumer'}]}
    catalog = Catalog()
    catalog.register(execute)
    run = asyncio.run(Relay(catalog=catalog).run(parse_definition(d), inputs={}, cancellation=token, opportunity_id='revision-live-cancel'))
    p, c = run.record.nodes
    actual = {'producer_state': p.state, 'consumer_reason': c.reason, 'status': c.input_resolutions['x'].status, 'calls': calls}
    request.node.actual = actual
    assert p.reason == 'CANCELLATION' and p.information == {}
    assert c.input_values == {} and not c.input_resolutions['x'].used_default
    assert actual == request.node.expected
