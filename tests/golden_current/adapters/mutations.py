"""Disposable negative observations measure independent assertion sensitivity.

No production code is edited. A missing detector is reported as a survivor.
"""

from tools.golden.compare import Difference, equal
from tools.golden.oracle import result, reduce_results, EXCEPTIONAL


def probe(payload):
    name = payload["mutant"]
    detectors = {
        "pass_as_fail": lambda: equal(result("PASS"), result("FAIL")),
        "unknown_as_pass": lambda: equal(result("UNKNOWN"), result("PASS")),
        "stale_output": lambda: equal(
            {"status": "PRODUCER_ERROR"}, {"status": "AVAILABLE", "value": "stale"}
        ),
        "ignored_guard": lambda: equal(
            {"reason": "GUARD_FALSE", "state": "NONEXECUTED"}, {"state": "SUCCESS"}
        ),
        "wrong_provider": lambda: equal("com.example.expected", "com.example.other"),
        "schema_bypass": lambda: equal(True, 1),
        "ignored_stop": lambda: equal("CONTROL_STOP", None),
        "fabricated_usage": lambda: equal(
            {"unit": "call", "kind": "EXACT", "value": 2},
            {"unit": "call", "kind": "EXACT", "value": 3},
        ),
        "missing_provenance": lambda: equal(
            {"source": {"kind": "CONSTANT", "value": 1}}, {"value": 1}
        ),
        "provider_substitution": lambda: equal(
            {"provider_id": "com.example.correct"}, {"provider_id": "com.example.wrong"}
        ),
        "cancel_as_success": lambda: equal(result("CANCELLED"), result("PASS")),
        "cross_run_leak": lambda: equal(
            {"run": "first", "value": True}, {"run": "second", "value": 1}
        ),
    }
    if name == "swapped_weights":
        config = {"handling": dict.fromkeys(EXCEPTIONAL, "IGNORE"), "weights": [1, 3]}
        proper = reduce_results(
            "WEIGHTED_AVERAGE", [result("KNOWN", score=0), result("KNOWN", score=1)], config
        )
        config["weights"] = [3, 1]
        wrong = reduce_results(
            "WEIGHTED_AVERAGE", [result("KNOWN", score=0), result("KNOWN", score=1)], config
        )
        detectors[name] = lambda: equal(proper, wrong)
    if name not in detectors:
        return {"detected": False, "mutant": name, "reason": "no detector"}
    try:
        detectors[name]()
    except Difference as exc:
        return {"detected": True, "mutant": name, "invariant": str(exc)}
    return {"detected": False, "mutant": name}
