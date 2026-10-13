from typing import cast

import pytest
from pydantic import JsonValue

from openverify.adapters.demo import known
from openverify.engine.aggregation import aggregate
from openverify.errors import ProtocolError
from openverify.model import Context, Result, Severity
from openverify.validation import parse_result
from tests.helpers import handling


def config(reducer: str, action: str = "REJECT") -> Context:
    return {"reducer": reducer, "handling": handling(action)}


@pytest.mark.parametrize(
    "reducer,verdicts,expected",
    [
        ("ALL", ["PASS", "PASS"], "PASS"),
        ("ALL", ["PASS", "FAIL"], "FAIL"),
        ("ANY", ["FAIL", "PASS"], "PASS"),
        ("ANY", ["FAIL", "FAIL"], "FAIL"),
        ("MAJORITY", ["PASS", "PASS", "FAIL"], "PASS"),
        ("MAJORITY", ["FAIL", "PASS", "FAIL"], "FAIL"),
    ],
)
def test_logical(reducer: str, verdicts: list[str], expected: str) -> None:
    assert aggregate([known(v) for v in verdicts], config(reducer)).verdict == expected


@pytest.mark.parametrize(
    "reducer,expected", [("MIN_SCORE", 0.2), ("MAX_SCORE", 0.8), ("AVERAGE", 0.5)]
)
def test_numeric(reducer: str, expected: float) -> None:
    result = aggregate([known(score=0.2), known(score=0.8)], config(reducer))
    assert result.score == pytest.approx(expected)
    assert result.verdict is None


def test_weighted_and_filter_position_and_large_weights() -> None:
    unknown = parse_result(
        {
            "protocol": "draft",
            "disposition": "EXECUTED",
            "execution_outcome": "SUCCESS",
            "applicability": "APPLICABLE",
            "determination": "UNKNOWN",
        }
    )
    c = {**config("WEIGHTED_AVERAGE", "IGNORE"), "weights": [1.0, 100.0, 3.0]}
    result = aggregate([known(score=0.2), unknown, known(score=0.8)], cast(Context, c))
    assert result.score == pytest.approx(0.65)
    large: Context = {**config("WEIGHTED_AVERAGE"), "weights": [1e308, 1e308]}
    assert aggregate([known(score=0.2), known(score=0.8)], large).score == pytest.approx(0.5)


def test_identical_scores_remain_identical_after_mean_rounding() -> None:
    score = 0.028837896834126305
    inputs = [known(score=score) for _ in range(3)]
    assert aggregate(inputs, config("AVERAGE")).score == score
    assert aggregate(inputs, {**config("WEIGHTED_AVERAGE"), "weights": [1, 1, 1]}).score == score


@pytest.mark.parametrize(
    "state", ["UNKNOWN", "ERROR", "SKIP", "DEFERRED", "CANCELLED", "NOT_APPLICABLE", "MISSING"]
)
def test_explicit_exception_policies(state: str) -> None:
    result = known()
    if state == "UNKNOWN":
        result = result.model_copy(update={"determination": "UNKNOWN"})
    elif state == "ERROR":
        result = Result(disposition="EXECUTED", execution_outcome="ERROR")
    elif state in ("SKIP", "DEFERRED", "CANCELLED"):
        result = parse_result(
            {"protocol": "draft", "disposition": "SKIPPED" if state == "SKIP" else state}
        )
    elif state == "NOT_APPLICABLE":
        result = Result(
            disposition="EXECUTED", execution_outcome="SUCCESS", applicability="NOT_APPLICABLE"
        )
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate([known("PASS"), result], config("ALL"))
    assert aggregate([known("PASS"), result], config("ALL", "IGNORE")).verdict == "PASS"


@pytest.mark.parametrize(
    "reducer", ["ALL", "ANY", "MAJORITY", "MIN_SCORE", "MAX_SCORE", "AVERAGE", "WORST_SEVERITY"]
)
def test_empty_rejected(reducer: str) -> None:
    c = config(reducer)
    if reducer == "WORST_SEVERITY":
        c["severity_domain"] = {"id": "s", "levels": [{"label": "A", "rank": 1}]}
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate([], c)


def test_tie_and_all_ignored_and_zero_retained_weight() -> None:
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate([known("PASS"), known("FAIL")], config("MAJORITY"))
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate([Result(disposition="SKIPPED")], config("ALL", "IGNORE"))
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate(
            [known(score=1), Result(disposition="SKIPPED")],
            {**config("WEIGHTED_AVERAGE", "IGNORE"), "weights": [0, 1]},
        )


def test_severity() -> None:
    c: Context = {
        **config("WORST_SEVERITY"),
        "severity_domain": {
            "id": "custom",
            "levels": [{"label": "mild", "rank": 1}, {"label": "severe", "rank": 100}],
        },
    }
    results = [
        known().model_copy(update={"severity": Severity(domain="custom", label=label)})
        for label in ("mild", "severe")
    ]
    assert aggregate(results, c).severity == Severity(domain="custom", label="severe")
    with pytest.raises(ProtocolError, match="AGGREGATE_INPUT"):
        aggregate(
            [known().model_copy(update={"severity": Severity(domain="other", label="mild")})], c
        )


@pytest.mark.parametrize("weights", [[-1, 2], [0, 0], [True, 1], [1], ["1", 2]])
def test_invalid_weights(weights: list[JsonValue]) -> None:
    with pytest.raises(ProtocolError, match="AGGREGATE_CONFIG"):
        aggregate(
            [known(score=0.2), known(score=0.8)], {**config("WEIGHTED_AVERAGE"), "weights": weights}
        )
