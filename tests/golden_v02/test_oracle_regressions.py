"""Known mathematical counterexamples; no implementation imports."""

from fractions import Fraction
from decimal import localcontext
import pytest
from tools.golden_v02.provider_oracle import instant, valid_schema


@pytest.mark.parametrize("year", ["0001", "2026", "9999"])
@pytest.mark.parametrize("digits", [9, 20, 80])
def test_deadline_exact(year, digits):
    prefix = year + "-01-01T00:00:00"
    before = prefix + "." + "0" * digits + "1Z"
    deadline = prefix + "." + "0" * digits + "2Z"
    after = prefix + "." + "0" * digits + "3Z"
    with localcontext() as context:
        context.prec = 2
        assert instant(before) < instant(deadline) < instant(after)
        assert instant(deadline) == instant(deadline.replace("Z", "+00:00"))
        assert instant(after) - instant(before) == Fraction(2, 10 ** (digits + 1))


@pytest.mark.parametrize(
    "schema,valid",
    [
        (True, True),
        (False, True),
        ({"minLength": -1}, False),
        ({"$defs": {"x": {"$id": "nested", "type": "string"}}}, False),
        ({"$id": "urn:example:root", "type": "string"}, True),
        ({"default": {"$id": "ordinary-data"}}, True),
        ({"$ref": "#/$defs/x", "$defs": {"x": {"type": "string"}}}, True),
        ({"$ref": "#/default", "default": {"type": "string"}}, False),
        ({"$ref": "https://example.invalid/schema"}, False),
        ({"$dynamicRef": "#x"}, False),
        ({"properties": {"x": {"minLength": -1}}}, False),
    ],
)
def test_declared_schema_validity(schema, valid):
    assert valid_schema(schema) is valid


def test_independent_dag_count_and_scheduler_formula():
    from collections import Counter
    from itertools import product
    from math import comb
    from tools.golden_v02.enumerate_graphs import labeled_dags, explore

    # Inclusion-exclusion by nonempty source subsets, independent of the DAG
    # generator's cycle detection and of the scheduler's traversal.
    counts = [1]
    for n in range(1, 5):
        counts.append(
            sum(
                (-1) ** (k + 1) * comb(n, k) * 2 ** (k * (n - k)) * counts[n - k]
                for k in range(1, n + 1)
            )
        )
    actual = Counter(n for n, edges in labeled_dags(4))
    assert [actual[n] for n in range(5)] == counts
    states = transitions = 0
    for n, edges in labeled_dags(3):
        valid = {
            s for s in product("PRT", repeat=n) if all(s[b] == "P" or s[a] == "T" for a, b in edges)
        }
        expected_transitions = {
            (s, t)
            for s in valid
            for t in valid
            if sum(a != b for a, b in zip(s, t)) == 1
            and all(a == b or (a, b) in (("P", "R"), ("R", "T")) for a, b in zip(s, t))
        }
        model = explore(n, edges)
        assert valid == {tuple(s) for s in model["states"]}
        assert expected_transitions == {
            (tuple(s), tuple(t)) for s, action, node, t in model["transitions"]
        }
        states += len(valid)
        transitions += len(expected_transitions)
    assert (states, transitions) == (290, 364)
