import math
from typing import cast

import pytest
from pydantic import JsonValue, ValidationError

from openverify import ProtocolError, serialize
from openverify.adapters.demo import known
from openverify.engine.aggregation import aggregate
from openverify.model import Severity, SeverityDomain, SeverityLevel
from openverify.validation import parse_object, validate_wire
from tests.helpers import handling


@pytest.mark.parametrize("rank", [0, 1, -2, 0.0, 1.0, -2.0])
def test_integral_json_rank_normalized(rank: int | float) -> None:
    data: dict[str, JsonValue] = {"id": "custom", "levels": [{"label": "one", "rank": rank}]}
    validate_wire("severity-domain", data)
    domain = cast(SeverityDomain, parse_object("severity-domain", data))
    assert type(domain.levels[0].rank) is int
    assert domain.levels[0].rank == int(rank)
    assert parse_object("severity-domain", serialize(domain)) == domain
    constructed = SeverityLevel.model_validate({"label": "one", "rank": rank})
    assert type(constructed.rank) is int
    assert constructed.rank == domain.levels[0].rank


@pytest.mark.parametrize("rank", [True, False, "1", 1.5, float("nan"), float("inf")])
def test_invalid_rank_stays_rejected(rank: JsonValue) -> None:
    data: dict[str, JsonValue] = {"id": "custom", "levels": [{"label": "one", "rank": rank}]}
    with pytest.raises(ProtocolError) as error:
        parse_object("severity-domain", data)
    expected = (
        "PROTOCOL_JSON"
        if isinstance(rank, float) and not math.isfinite(rank)
        else "PROTOCOL_STRUCTURE"
    )
    assert error.value.code == expected
    with pytest.raises(ValidationError):
        SeverityLevel.model_validate({"label": "one", "rank": rank})


def test_integral_rank_in_aggregate_domain() -> None:
    result = known().model_copy(update={"severity": Severity(domain="custom", label="one")})
    output = aggregate(
        [result],
        {
            "reducer": "WORST_SEVERITY",
            "handling": handling(),
            "severity_domain": {"id": "custom", "levels": [{"label": "one", "rank": 1.0}]},
        },
    )
    assert output.severity == result.severity
