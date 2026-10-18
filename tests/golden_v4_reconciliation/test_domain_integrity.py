"""Independent finite-domain checks; passing executions cannot hide missing coordinates.

No production imports. These audit the existing stimuli against source-derived
products/predicates, rather than using a generator to validate itself.
"""

import itertools
import json
from collections import Counter

import pytest

from .test_snapshot import ROOT

CASES = [
    json.loads(s)
    for s in (ROOT / "conformance/golden-v4/FROZEN_EXPECTATIONS/cases.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
]
DISPOSITIONS = ("EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED")
FIELDS = ("execution_outcome", "applicability", "determination", "verdict")
VALUES = (
    ("SUCCESS", "ERROR"),
    ("APPLICABLE", "NOT_APPLICABLE"),
    ("KNOWN", "UNKNOWN"),
    ("PASS", "FAIL"),
)


def result_valid(d, e, a, k, v):
    if d != "EXECUTED":
        return all(x is None for x in (e, a, k, v))
    if e == "ERROR":
        return all(x is None for x in (a, k, v))
    if e != "SUCCESS":
        return False
    if a == "NOT_APPLICABLE":
        return k is None and v is None
    return a == "APPLICABLE" and (k == "KNOWN" or (k == "UNKNOWN" and v is None))


@pytest.mark.parametrize("projection", ["WIRE_AXIS", "SEMANTIC_AXIS"])
def test_result_complete_product_and_classification(projection):
    rows = [c for c in CASES if c["family"] == "V4.VCP.RESULT." + projection]
    absent = ("ABSENT", "NULL") if projection == "WIRE_AXIS" else ("ABSENT",)
    domain = set(itertools.product(DISPOSITIONS, *(absent + v for v in VALUES)))
    actual = []
    classified = Counter()
    for c in rows:
        p = c["stimulus"]["value"]
        coord = (p["disposition"],) + tuple(
            "ABSENT" if f not in p else "NULL" if p[f] is None else p[f] for f in FIELDS
        )
        actual.append(coord)
        valid = result_valid(p["disposition"], *(p.get(f) for f in FIELDS))
        assert c["expected"] == {"accepted": valid}, c["case_id"]
        assert c["classification"] == ("VALID" if valid else "INVALID"), c["case_id"]
        classified[valid] += 1
    assert len(actual) == len(set(actual))
    assert set(actual) == domain
    if projection == "WIRE_AXIS":
        # Three nonexecutions, ERROR, NOT_APPLICABLE, UNKNOWN and KNOWN are disjoint.
        assert classified[True] == 3 * 2**4 + 2**3 + 2**2 + 2 + 4 == 66
        assert len(domain) == 4 * 4**4 == classified[True] + classified[False]
    else:
        assert classified[True] == 3 + 1 + 1 + 1 + 3 == 9
        assert len(domain) == 4 * 3**4 == classified[True] + classified[False]


def test_observation_actual_names_and_complete_masks():
    names = {
        "judgment",
        "score",
        "severity",
        "evidence",
        "usage",
        "output",
        "metadata",
        "extensions",
    }
    forbidden = {"judgment", "score", "severity"}
    rows = [c for c in CASES if c["family"] == "V4.VCP.RESULT.OBS_MASK"]
    actual = set()
    states = set()
    valid_count = 0
    for c in rows:
        p = c["stimulus"]["value"]
        state = (p["disposition"],) + tuple(p.get(f) for f in FIELDS)
        mask = frozenset(set(p) & names)
        assert (state, mask) not in actual, c["case_id"]
        actual.add((state, mask))
        states.add(state)
        valid = p.get("determination") == "KNOWN" or not (mask & forbidden)
        assert c["expected"] == {"accepted": valid}, c["case_id"]
        assert set(p) <= names | set(FIELDS) | {"protocol", "disposition"}, c["case_id"]
        valid_count += valid
    expected_states = {
        x
        for x in itertools.product(DISPOSITIONS, *((None,) + v for v in VALUES))
        if result_valid(*x)
    }
    masks = {
        frozenset(n for n, bit in zip(sorted(names), bits) if bit)
        for bits in itertools.product((0, 1), repeat=8)
    }
    assert states == expected_states
    assert actual == set(itertools.product(expected_states, masks))
    assert len(actual) == 9 * 2**8 == 2304
    assert valid_count == 3 * 2**8 + 6 * 2**5 == 960


def test_small_graph_domain_and_cycles():
    rows = [c for c in CASES if c["family"] == "V4.VCP.GRAPH.DAG_0_4"]
    actual = set()
    dags = 0
    for c in rows:
        graph = c["stimulus"]["value"]["graph"]
        nodes = tuple(n["id"] for n in graph["nodes"])
        positions = {n: i for i, n in enumerate(nodes)}
        edges = {(positions[e["from_node"]], positions[e["to_node"]]) for e in graph["edges"]}
        n = len(nodes)
        arcs = tuple((i, j) for i in range(n) for j in range(n) if i != j)
        coord = (n, tuple(int(e in edges) for e in arcs))
        assert coord not in actual, c["case_id"]
        actual.add(coord)
        # Independent transitive closure: a diagonal reachability witness is a cycle.
        closure = set(edges)
        for k in range(n):
            closure |= {
                (i, j)
                for i in range(n)
                for j in range(n)
                if (i, k) in closure and (k, j) in closure
            }
        valid = not any((i, i) in closure for i in range(n))
        assert c["expected"] == {"accepted": valid}, c["case_id"]
        dags += valid
    expected = {
        (n, bits) for n in range(5) for bits in itertools.product((0, 1), repeat=n * (n - 1))
    }
    assert actual == expected
    assert len(actual) == sum(2 ** (n * (n - 1)) for n in range(5)) == 4166
    assert dags == 573


def test_reducer_configuration_product():
    reducers = {
        "ALL",
        "ANY",
        "MAJORITY",
        "MIN_SCORE",
        "MAX_SCORE",
        "AVERAGE",
        "WEIGHTED_AVERAGE",
        "WORST_SEVERITY",
    }
    exceptions = ("UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING")
    rows = [c for c in CASES if c["family"] == "V4.VCP.AGG.HANDLING_MAP"]
    actual = [
        (c["stimulus"]["reducer"], tuple(c["stimulus"]["handling"][k] for k in exceptions))
        for c in rows
    ]
    expected = set(itertools.product(reducers, itertools.product(("REJECT", "IGNORE"), repeat=7)))
    assert len(actual) == len(set(actual)) == 8 * 2**7
    assert set(actual) == expected
    assert all(set(c["stimulus"]["handling"]) == set(exceptions) for c in rows)
    # Configuration eligibility is tested here; exceptional-member behavior is a
    # different projection and is not proved by these all-retained examples.


@pytest.mark.parametrize("kind", ["RUN_RECORD", "NODE_RECORD"])
def test_record_presence_reduction_premises(kind):
    source = json.loads((ROOT / "schemas/draft/run-record.schema.json").read_text(encoding="utf-8"))
    schema = source if kind == "RUN_RECORD" else source["properties"]["nodes"]["items"]
    assert set(schema) <= {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "properties",
        "required",
        "additionalProperties",
    }
    assert schema["type"] == "object" and schema["additionalProperties"] is False
    fields, required = set(schema["properties"]), set(schema["required"])
    optional = sorted(fields - required)
    expected = {
        frozenset(required | {n for n, bit in zip(optional, bits) if bit})
        for bits in itertools.product((0, 1), repeat=len(optional))
    }
    expected |= {frozenset(fields - {r}) for r in required}
    rows = [c for c in CASES if c["family"] == "V4.VCP." + kind + ".PRESENCE"]
    observed = [frozenset(c["stimulus"]["value"]) for c in rows]
    assert len(observed) == len(set(observed))
    assert set(observed) == expected
    assert sum(c["expected"]["accepted"] for c in rows) == 2 ** len(optional)
    for c in rows:
        assert c["expected"] == {"accepted": required <= set(c["stimulus"]["value"])}
    # Fix all present field values to their independently valid presence stimuli.
    # With no cross-key root keyword, deleting any required key invalidates every
    # optional mask. The omitted invalid product is exact, not a sampling claim.
    all_masks = 2 ** len(fields)
    valid_masks = 2 ** len(optional)
    invalid_masks = (2 ** len(required) - 1) * valid_masks
    assert all_masks == valid_masks + invalid_masks
    assert len(rows) == valid_masks + len(required)
