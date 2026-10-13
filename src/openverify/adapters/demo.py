"""Small local examples, not protocol primitives or an untrusted code runner."""

import re
from typing import cast

from openverify.adapters import Registry
from openverify.errors import ProtocolError
from openverify.model import Context, Decision, Evidence, Result
from openverify.validation import parse_result


def known(verdict: str | None = None, score: float | None = None) -> Result:
    return parse_result(
        {
            "protocol": "draft",
            "disposition": "EXECUTED",
            "execution_outcome": "SUCCESS",
            "applicability": "APPLICABLE",
            "determination": "KNOWN",
            "verdict": verdict,
            "score": score,
        }
    )


class ConstantEvaluator:
    version = "1"

    def execute(
        self, context: Context, prior_results: dict[str, Result], config: Context
    ) -> Result:
        return parse_result(config["result"])


class RegexEvaluator:
    version = "1"

    def execute(
        self, context: Context, prior_results: dict[str, Result], config: Context
    ) -> Result:
        text = context[cast(str, config["key"])]
        pattern = config["pattern"]
        must_match = config["must_match"]
        if (
            not isinstance(text, str)
            or not isinstance(pattern, str)
            or type(must_match) is not bool
        ):
            raise ProtocolError(
                "EXECUTOR_ERROR", "Regex demo needs text, pattern, and boolean must_match"
            )
        matched = re.search(pattern, text) is not None
        result = known("PASS" if matched == must_match else "FAIL")
        return result.model_copy(
            update={"evidence": [Evidence(message=f"Pattern matched: {matched}")]}
        )


class RangeEvaluator:
    version = "1"

    def execute(
        self, context: Context, prior_results: dict[str, Result], config: Context
    ) -> Result:
        value = context[cast(str, config["key"])]
        low, high = config["minimum"], config["maximum"]
        if any(type(v) not in (int, float) for v in (value, low, high)):
            raise ProtocolError("EXECUTOR_ERROR", "Range demo requires numeric values")
        if cast(float, low) > cast(float, high):
            raise ProtocolError("EXECUTOR_ERROR", "Inverted range")
        return known(
            "PASS" if cast(float, low) <= cast(float, value) <= cast(float, high) else "FAIL"
        )


class LengthDeriver:
    version = "1"

    def execute(self, context: Context, config: Context) -> Context:
        value = context[cast(str, config["key"])]
        if not isinstance(value, str):
            raise ProtocolError("EXECUTOR_ERROR", "Length demo requires text")
        return {cast(str, config["output_key"]): len(value)}


class UnknownRouter:
    version = "1"

    def execute(self, context: Context, results: dict[str, Result], config: Context) -> Decision:
        if any(r.determination == "UNKNOWN" for r in results.values()):
            return Decision(
                kind="ROUTE",
                destination=cast(str, config["destination"]),
                reason="Uncertain evaluation",
            )
        return Decision(kind="CONTINUE")


def demo_registry() -> Registry:
    registry = Registry()
    registry.register_evaluate("demo.constant", ConstantEvaluator())
    registry.register_evaluate("demo.regex", RegexEvaluator())
    registry.register_evaluate("demo.range", RangeEvaluator())
    registry.register_derive("demo.length", LengthDeriver())
    registry.register_control("demo.unknown-route", UnknownRouter())
    return registry
