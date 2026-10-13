"""Standard reducers with no implicit exceptional-input conversion."""

from fractions import Fraction
from typing import cast

from openverify.adapters.demo import known
from openverify.errors import ProtocolError
from openverify.model import Context, Result, Severity, SeverityDomain
from openverify.serialization import decode
from openverify.validation import aggregate_config, parse_object, validate_result


def aggregate(inputs: list[Result], config: Context) -> Result:
    decode(config)
    aggregate_config(config, len(inputs))
    reducer = cast(str, config["reducer"])
    handling = cast(dict[str, str], config["handling"])
    retained: list[tuple[int, Result]] = []
    domain: SeverityDomain | None = None
    ranks: dict[str, int] = {}
    if reducer == "WORST_SEVERITY":
        domain = cast(SeverityDomain, parse_object("severity-domain", config["severity_domain"]))
        ranks = {v.label: v.rank for v in domain.levels}
    for index, result in enumerate(inputs):
        validate_result(result)
        category: str | None = None
        if result.disposition != "EXECUTED":
            category = "SKIP" if result.disposition == "SKIPPED" else result.disposition
        elif result.execution_outcome == "ERROR":
            category = "ERROR"
        elif result.applicability == "NOT_APPLICABLE":
            category = "NOT_APPLICABLE"
        elif result.determination == "UNKNOWN":
            category = "UNKNOWN"
        elif reducer in ("ALL", "ANY", "MAJORITY") and result.verdict is None:
            category = "MISSING"
        elif (
            reducer in ("MIN_SCORE", "MAX_SCORE", "AVERAGE", "WEIGHTED_AVERAGE")
            and result.score is None
        ):
            category = "MISSING"
        elif reducer == "WORST_SEVERITY":
            if result.severity is None:
                category = "MISSING"
            elif (
                domain is None
                or result.severity.domain != domain.id
                or result.severity.label not in ranks
            ):
                raise ProtocolError(
                    "AGGREGATE_INPUT", "Severity does not belong to the configured domain"
                )
        if category:
            if handling[category] == "REJECT":
                raise ProtocolError("AGGREGATE_INPUT", f"Rejected {category} input", f"/{index}")
        else:
            retained.append((index, result))
    if not retained:
        raise ProtocolError("AGGREGATE_INPUT", "Empty retained input is undefined")
    results = [r for _, r in retained]
    output = known()
    if reducer in ("ALL", "ANY", "MAJORITY"):
        passed = sum(r.verdict == "PASS" for r in results)
        if reducer == "ALL":
            satisfied = passed == len(results)
        elif reducer == "ANY":
            satisfied = passed > 0
        else:
            if passed * 2 == len(results):
                raise ProtocolError("AGGREGATE_INPUT", "Majority tie is undefined")
            satisfied = passed * 2 > len(results)
        output = known("PASS" if satisfied else "FAIL")
    elif reducer == "WORST_SEVERITY":
        worst = max((cast(Severity, r.severity) for r in results), key=lambda s: ranks[s.label])
        output = output.model_copy(update={"severity": worst})
    else:
        scores = [cast(float, r.score) for r in results]
        if reducer == "MIN_SCORE":
            score = min(scores)
        elif reducer == "MAX_SCORE":
            score = max(scores)
        elif reducer == "AVERAGE":
            score = float(sum((Fraction(s) for s in scores), Fraction()) / len(scores))
        else:
            weights = cast(list[float], config["weights"])
            selected = [weights[i] for i, _ in retained]
            total = sum((Fraction(w) for w in selected), Fraction())
            if total == 0:
                raise ProtocolError("AGGREGATE_INPUT", "Retained weight total must be positive")
            score = float(
                sum(
                    (Fraction(s) * Fraction(w) for s, w in zip(scores, selected, strict=True)),
                    Fraction(),
                )
                / total
            )
        output = known(score=score)
    return output.model_copy(update={"evidence": [e for r in results for e in r.evidence]})
