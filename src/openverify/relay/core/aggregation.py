"""Standard reducers, independently implemented from the normative aggregation spec."""

from fractions import Fraction
from typing import cast

from pydantic import JsonValue

from openverify.errors import ProtocolError
from openverify.model import Context, Evidence, Result, Severity, SeverityDomain
from openverify.serialization import to_data
from openverify.validation import aggregate_config, parse_object, parse_result


def reduce_results(inputs: Context, config: Context) -> Result:
    names = cast(list[str], inputs["members"])
    checked = dict(config)
    weights = cast(dict[str, float], config.get("weights", {}))
    if config["reducer"] == "WEIGHTED_AVERAGE":
        checked["weights"] = [weights[n] for n in names]
    aggregate_config(checked, len(names))
    reducer = config["reducer"]
    handling = cast(dict[str, str], config["handling"])
    retained: list[tuple[str, Result]] = []
    for name in names:
        result = parse_result(inputs[name])
        exceptional = (
            "SKIP"
            if result.disposition == "SKIPPED"
            else result.disposition
            if result.disposition != "EXECUTED"
            else "ERROR"
            if result.execution_outcome == "ERROR"
            else "NOT_APPLICABLE"
            if result.applicability == "NOT_APPLICABLE"
            else "UNKNOWN"
            if result.determination == "UNKNOWN"
            else None
        )
        field = (
            "verdict"
            if reducer in ("ALL", "ANY", "MAJORITY")
            else ("severity" if reducer == "WORST_SEVERITY" else "score")
        )
        if exceptional is None and getattr(result, field) is None:
            exceptional = "MISSING"
        if exceptional is not None:
            if handling[exceptional] == "REJECT":
                raise ProtocolError("AGGREGATE_INPUT", f"Rejected {name}: {exceptional}")
        else:
            retained.append((name, result))
    if not retained:
        raise ProtocolError("AGGREGATE_INPUT", "No retained aggregate inputs")
    evidence: list[Evidence] = [e for _, r in retained for e in r.evidence]
    fields: dict[str, JsonValue] = {}
    if reducer in ("ALL", "ANY", "MAJORITY"):
        passes = sum(r.verdict == "PASS" for _, r in retained)
        if reducer == "MAJORITY" and passes * 2 == len(retained):
            raise ProtocolError("AGGREGATE_INPUT", "Majority tie has no defined verdict")
        passed = (
            passes == len(retained)
            if reducer == "ALL"
            else passes > 0
            if reducer == "ANY"
            else passes * 2 > len(retained)
        )
        fields["verdict"] = "PASS" if passed else "FAIL"
    elif reducer == "WORST_SEVERITY":
        domain = cast(SeverityDomain, parse_object("severity-domain", config["severity_domain"]))
        ranks = {level.label: level.rank for level in domain.levels}
        severities = [cast(Severity, r.severity) for _, r in retained]
        if any(s.domain != domain.id or s.label not in ranks for s in severities):
            raise ProtocolError("AGGREGATE_INPUT", "Severity is outside the configured domain")
        fields["severity"] = to_data(max(severities, key=lambda s: ranks[s.label]))
    else:
        scores = [cast(float, r.score) for _, r in retained]
        if reducer in ("MIN_SCORE", "MAX_SCORE"):
            fields["score"] = min(scores) if reducer == "MIN_SCORE" else max(scores)
        else:
            ws = [
                Fraction(weights[n]) if reducer == "WEIGHTED_AVERAGE" else Fraction(1)
                for n, _ in retained
            ]
            if sum(ws) <= 0:
                raise ProtocolError("AGGREGATE_INPUT", "Retained weight total must be positive")
            fields["score"] = float(
                sum((Fraction(s) * w for s, w in zip(scores, ws, strict=True)), Fraction())
                / sum(ws)
            )
    return parse_result(
        {
            "protocol": "draft",
            "disposition": "EXECUTED",
            "execution_outcome": "SUCCESS",
            "applicability": "APPLICABLE",
            "determination": "KNOWN",
            **fields,
            "evidence": [to_data(e) for e in evidence],
        }
    )
