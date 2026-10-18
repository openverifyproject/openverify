"""Versioned corrections; the historical frozen stimuli/expectations are unchanged."""
import pytest

from openverify import ProtocolError, parse_definition
from openverify.relay.core.aggregation import reduce_results
from .test_snapshot import ROOT, custom_definition, result


@pytest.mark.parametrize('weights', [(-1, -1), (-1, 0), (-1, 2), (0, -1), (0, 0), (2, -1)], ids=lambda w: 'V4.REVISION.WEIGHTS.CONFIG.' + str(w))
def test_invalid_original_weights_are_configuration_errors(weights, request):
    request.node.canonical_ids = ['CM.VCP.AGG.WEIGHTED.ORIGINAL_WEIGHTS']
    request.node.expected = {'error': 'AGGREGATE_CONFIG'}
    values = {'members': ['a', 'b'], 'a': {**result(), 'score': 0.25}, 'b': {**result(), 'score': 0.75}}
    config = {'reducer': 'WEIGHTED_AVERAGE', 'handling': {k: 'REJECT' for k in ['UNKNOWN', 'ERROR', 'SKIP', 'DEFERRED', 'CANCELLED', 'NOT_APPLICABLE', 'MISSING']}, 'weights': dict(zip(['a', 'b'], weights))}
    with pytest.raises(ProtocolError) as caught:
        reduce_results(values, config)
    request.node.actual = {'error': caught.value.code}
    assert request.node.actual == request.node.expected


def test_annotation_payload_is_not_a_schema(request):
    request.node.canonical_ids = ['CM.VCP.SCHEMA.SUBSET']
    request.node.expected = {'accepted': True}
    d = custom_definition()
    d['graph'] = {'nodes': [], 'edges': []}
    # description has a string metaschema type; default legitimately accepts JSON.
    d['judgment_schema'] = {'default': {'$ref': 'https://example.invalid/annotation-only'}}
    parse_definition(d)
    request.node.actual = {'accepted': True}
    assert request.node.actual == request.node.expected


@pytest.mark.parametrize('check', ['INVENTORY', 'PROOFS'], ids=lambda c: 'V4.REVISION.AUDIT.FAIL_CLOSED.' + c)
def test_incomplete_coverage_is_not_certified(check, request):
    from tools.golden_v4 import report
    request.node.canonical_ids = []
    request.node.expected = {'accepted': False}
    if check == 'INVENTORY':
        accepted = report.inventory()['certified']
    else:
        accepted = all(p['status'] == 'PROVED' for p in report.read_rows(ROOT / 'conformance/golden-v4/REDUCTION_LEDGER.jsonl'))
    request.node.actual = {'accepted': accepted}
    assert request.node.actual == request.node.expected
