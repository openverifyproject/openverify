"""Execute frozen cases and assert observed public-boundary behavior.

Never writes expected files. All missing adapter work is an explicit ERROR.
"""

from __future__ import annotations

from copy import deepcopy

from tools.golden.compare import Difference, equal
from tools.golden.oracle import check_record, normalized_result
from tools.golden.verify_manifest import resolve


class EnvironmentUnavailable(Exception):
    pass


class AdapterGap(Exception):
    pass


def assess(case, observed, expected):
    if expected.get("error_code") or expected.get("reject"):
        if not observed.get("error_code"):
            raise Difference("expected rejection; operation accepted")
        if expected.get("error_code"):
            equal(expected["error_code"], observed["error_code"], "/error_code")
        return
    if observed.get("error_code"):
        raise Difference(
            "unexpected rejection: " + observed["error_code"] + ": " + observed.get("message", "")
        )
    if case["operation"] == "parse_result":
        equal(
            normalized_result(expected["preserve"]), normalized_result(observed["value"]), "/result"
        )
        equal(expected["projection"], observed["projection"], "/projection")
        if expected["projection"] is None:
            equal("RESULT_PROJECTION", observed.get("projection_error"), "/projection_error")
    elif case["operation"] == "provider_frame":
        equal(expected, observed)
    elif case["operation"] == "reducer_graph":
        outcome = observed["outcome"]
        equal("COMPLETED", outcome["state"], "/outcome/state")
        equal(
            normalized_result(expected["result"]),
            normalized_result(outcome["output"]["result"]),
            "/aggregate",
        )


async def dispatch(case, payload):
    from tests.golden_current.adapters import public

    op = case["operation"]
    if op.startswith("parse_"):
        return public.parse(op, payload)
    if op == "provider_trace":
        return public.provider_trace(payload)
    if op == "provider_frame":
        return public.provider_frame(payload)
    if op == "reducer_graph":
        answer = await public.reducer(payload)
        if answer["outcome"]["state"] == "ERROR":
            # Provider error codes are observed verbatim; never infer a stable
            # semantic category by parsing the diagnostic message.
            return {**answer, "error_code": answer["outcome"]["error"]["code"]}
        return answer
    if op in ("run", "policy_run", "metamorphic_run"):
        observed = await public.run_scenario(payload)
        if op == "metamorphic_run":
            variants = []
            for variant in ("reverse_nodes", "reverse_edges", "irrelevant_node"):
                s = deepcopy(payload)
                if variant == "reverse_nodes":
                    s["definition"]["graph"]["nodes"].reverse()
                elif variant == "reverse_edges":
                    s["definition"]["graph"]["edges"].reverse()
                else:
                    # A separate independent node with explicit information output.
                    template = deepcopy(s["definition"]["graph"]["nodes"][0])
                    template["id"] = "irrelevant"
                    s["definition"]["graph"]["nodes"].append(template)
                    s["behaviors"]["irrelevant"] = {"outputs": {"value": "irrelevant"}}
                    s["nodes"]["irrelevant"] = {
                        "state": "SUCCESS",
                        "information": {"value": "irrelevant"},
                    }
                variants.append((s, await public.run_scenario(s)))
            observed["variants"] = variants
        return observed
    if op == "abstract_scheduler":
        from tools.golden.enumerate_graphs import explore

        return explore(payload["n"], tuple(tuple(e) for e in payload["edges"]))
    if op == "runtime_experiment":
        from tests.golden_current.adapters.runtime import experiment

        return await experiment(payload)
    if op == "port_experiment":
        from tests.golden_current.adapters.ports import experiment

        return await experiment(payload)
    if op == "provenance_experiment":
        from tests.golden_current.adapters.provenance import experiment

        return await experiment(payload)
    if op == "mutation_probe":
        from tests.golden_current.adapters.mutations import probe

        return probe(payload)
    if op == "standard_experiment":
        from tests.golden_current.adapters.standard import experiment

        return await experiment(payload)
    if op == "integration_experiment":
        from tests.golden_current.adapters.integrations import experiment

        return await experiment(payload)
    raise AdapterGap("no invocation adapter for " + op)


async def execute_case(case):
    payload, expected = (
        deepcopy(resolve(case["input_ref"])),
        deepcopy(resolve(case["expected_ref"])),
    )
    row = {
        "id": case["id"],
        "profile": case["profile"],
        "category": case["category"],
        "feature_ids": case["feature_ids"],
        "expected": expected,
        "reproduce": f"python tools/golden/run_suite.py --profile {case['profile']} --case {case['id']}",
        "sut_executed": False,
    }
    if expected.get("blocked_by_spec") or expected.get("blocked_error_category"):
        row.update(
            status="BLOCKED_BY_SPEC",
            detail=expected.get("blocked_by_spec", expected.get("blocked_error_category")),
        )
        return row
    observed = {}
    try:
        row["sut_executed"] = case["operation"] not in ("abstract_scheduler", "mutation_probe")
        try:
            observed = await dispatch(case, payload)
        except (EnvironmentUnavailable, AdapterGap, AssertionError):
            raise
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code is None:
                raise
            observed = {"error_code": code, "message": str(exc)}
        if case["operation"] in ("run", "policy_run", "metamorphic_run") and not expected.get(
            "error_code"
        ):
            scenario = deepcopy(payload)
            scenario["definition"] = observed["definition"]
            check_record(observed["record"], scenario)
            for sc, variant in observed.get("variants", []):
                sc = deepcopy(sc)
                sc["definition"] = variant["definition"]
                check_record(variant["record"], sc)
        elif case["operation"] == "abstract_scheduler":
            equal(expected, observed)
            row["scope"] = "MODEL_ONLY_NOT_SUT_CONFORMANCE"
        elif case["operation"] == "mutation_probe":
            if not observed.get("detected"):
                raise Difference("mutant survived: " + payload["mutant"])
            row["scope"] = "INDEPENDENT_ASSERTION_SENSITIVITY"
        else:
            assess(case, observed, expected)
            if case["operation"] in (
                "runtime_experiment",
                "port_experiment",
                "standard_experiment",
                "integration_experiment",
            ):
                equal(True, observed.get("verified"), "/experiment_verified")
        row.update(status="PASS")
    except EnvironmentUnavailable as exc:
        row.update(status="ENVIRONMENT_UNAVAILABLE", detail=str(exc), sut_executed=False)
    except AdapterGap as exc:
        row.update(
            status="ERROR",
            classification="ADAPTER_UNIMPLEMENTED",
            detail=str(exc),
            sut_executed=False,
        )
    except AssertionError as exc:
        row.update(status="FAIL", detail=str(exc))
    except Exception as exc:
        row.update(status="ERROR", detail=f"{type(exc).__name__}: {exc}")
    # Observations are report data only. They are never written into fixtures.
    if row["status"] in ("FAIL", "ERROR"):
        row["observed"] = observed
    return row
