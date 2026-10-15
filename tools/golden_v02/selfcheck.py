"""Self-tests of the suite only. Never imports OpenVerify or executes Relay."""

from tools.golden_v02.compare import Difference, equal
from tools.golden_v02.oracle import EXCEPTIONAL, result, reduce_results, result_axes, result_error
from tools.golden_v02.enumerate_graphs import labeled_dags, explore, generated, shrink, topological
from tools.golden_v02.provider_oracle import encode_frame, decode_frames, instant


def run():
    checks = []
    for a, b in [(True, 1), (False, 0), ({"x": None}, {}), ([1, 2], [2, 1])]:
        try:
            equal(a, b)
        except Difference:
            checks.append("JSON distinction")
        else:
            raise AssertionError("strict comparator missed JSON distinction")
    equal(1, 1.0)
    axes = list(result_axes())
    equal(1024, len(axes))
    equal(3 * 2**4 + 2**3 + 2**2 + 2 + 4, sum(result_error(r) is None for r in axes))
    checks.append("all categorical Result states")
    config = {"handling": dict.fromkeys(EXCEPTIONAL, "IGNORE"), "weights": [1, 3]}
    equal(
        0.75,
        reduce_results(
            "WEIGHTED_AVERAGE", [result("KNOWN", score=0), result("KNOWN", score=1)], config
        )["result"]["score"],
    )
    checks.append("independent weighted 0.75 regression")
    equal(
        {"error_code": "AGGREGATE_INPUT"},
        reduce_results(
            "MAJORITY",
            [result("PASS"), result("FAIL")],
            {"handling": dict.fromkeys(EXCEPTIONAL, "REJECT")},
        ),
    )
    checks.append("majority tie rejection")
    from collections import Counter

    equal(
        {0: 1, 1: 1, 2: 3, 3: 25, 4: 543}.__repr__(),
        dict(Counter(n for n, _ in labeled_dags(4))).__repr__(),
    )
    checks.append("complete bounded DAG count")
    for n, e in generated(71717):
        assert topological(n, e) is not None
        for sn, se in shrink(n, e):
            assert topological(sn, se) is not None
    checks.append("seeded graph generation and shrink validity")
    for n, e in labeled_dags(3):
        model = explore(n, e)
        for state, action, i, target in model["transitions"]:
            equal(1, sum(a != b for a, b in zip(state, target)))
            if action == "start":
                assert all(state[a] == "T" for a, b in e if b == i)
    checks.append("abstract transitions obey all prerequisites")
    value = {"unicode": "é😀", "typed": [True, 1, False, 0, None]}
    equal([value], decode_frames(encode_frame(value)))
    assert instant("2026-01-01T00:00:00.00000000009Z") < instant("2026-01-01T00:00:00.0000000001Z")
    checks.append("UTF-8 byte framing and decimal deadlines")
    mutants = []  # Actual observation mutation probes run only in the SUT stage.
    return {
        "passed": True,
        "checks": checks,
        "mutants": mutants,
        "surviving_assertion_probes": [],
        "sut_executed": False,
        "limitations": "These probes exercise assertions; they are not a production mutation-testing campaign.",
    }
