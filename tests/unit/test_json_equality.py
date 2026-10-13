import pytest
from pydantic import JsonValue

from openverify.serialization import json_equal

UNEQUAL_VALUES: list[tuple[JsonValue, JsonValue]] = [
    (1, True),
    (0, False),
    ({"v": 1}, {"v": True}),
    ({"v": 0}, {"v": False}),
    ([1], [True]),
    ([0], [False]),
    ({"x": [1]}, {"x": [True]}),
    ({"x": [0]}, {"x": [False]}),
    ([1, 2], [2, 1]),
    ([], [None]),
    ({"a": None}, {}),
    ("1", 1),
]


@pytest.mark.parametrize("left,right", UNEQUAL_VALUES)
def test_json_snapshot_types_and_array_order(left: JsonValue, right: JsonValue) -> None:
    assert not json_equal(left, right)
    assert not json_equal(right, left)


EQUAL_VALUES: list[tuple[JsonValue, JsonValue]] = [
    (None, None),
    (1, 1),
    (True, True),
    (False, False),
    ("same", "same"),
    ({"a": [None, True, 1, {}], "b": []}, {"b": [], "a": [None, True, 1, {}]}),
    (1, 1.0),  # Parsed reference values share the JSON number type.
]


@pytest.mark.parametrize("left,right", EQUAL_VALUES)
def test_json_snapshot_equal_values(left: JsonValue, right: JsonValue) -> None:
    assert json_equal(left, right)
    assert json_equal(right, left)
