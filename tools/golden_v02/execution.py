"""Execute frozen cases and assert observed public-boundary behavior.

Never writes expected files. All missing adapter work is an explicit ERROR.
"""

from __future__ import annotations

from copy import deepcopy

from tools.golden_v02.compare import Difference, equal
from tools.golden_v02.oracle import check_record, normalized_result
from tools.golden_v02.verify_manifest import resolve
from tools.golden_v02.environment import configure

configure()


class EnvironmentUnavailable(Exception):
    pass


class AdapterGap(Exception):
    pass


def assess(case, observed, expected):
    if expected.get("error_code") or expected.get("reject"):
        if not observed.get("error_code"):
            raise Difference("expected rejection; operation accepted")
        if expected.get("allowed_error_codes"):
            assert observed["error_code"] in expected["allowed_error_codes"], observed
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
    elif case["operation"] == "provider_object":
        equal(expected["preserve"], observed["value"])
    elif case["operation"] == "stdio_experiment":
        equal(expected["state"], observed["record"]["nodes"][0]["state"])
        equal(expected["information"], observed["record"]["nodes"][0]["information"])
    elif case["operation"] == "reducer_graph":
        outcome = observed["outcome"]
        equal("COMPLETED", outcome["state"], "/outcome/state")
        equal(
            normalized_result(expected["result"]),
            normalized_result(outcome["output"]["result"]),
            "/aggregate",
        )


async def dispatch(case, payload):
    from tests.golden_v02.adapters import public

    op = case["operation"]
    if op.startswith("parse_"):
        return public.parse(op, payload)
    if op == "provider_trace":
        return public.provider_trace(payload)
    if op == "provider_frame":
        return public.provider_frame(payload)
    if op == "provider_object":
        from openverify.provider import parse_provider_object, wire_data

        return {"value": wire_data(parse_provider_object(payload["object_type"], payload["value"]))}
    if op == "stdio_experiment":
        from tests.golden_v02.adapters.runtime import external

        return await external(payload["mode"])
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
        from tools.golden_v02.enumerate_graphs import explore

        return explore(payload["n"], tuple(tuple(e) for e in payload["edges"]))
    if op == "runtime_experiment":
        from tests.golden_v02.adapters.runtime import experiment

        return await experiment(payload)
    if op == "port_experiment":
        from tests.golden_v02.adapters.ports import experiment

        return await experiment(payload)
    if op == "provenance_experiment":
        from tests.golden_v02.adapters.provenance import experiment

        return await experiment(payload)
    if op == "mutation_probe":
        from tests.golden_v02.adapters.mutations import probe

        return await probe(payload)
    if op == "standard_experiment":
        from tests.golden_v02.adapters.standard import experiment

        return await experiment(payload)
    if op == "integration_experiment":
        from tests.golden_v02.adapters.integrations import experiment

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
        "spec_ambiguity": expected.get("spec_ambiguity"),
        "reproduce": f"python tools/golden_v02/run_suite.py --profile {case['profile']} --case {case['id']}",
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
        row["sut_executed"] = case["operation"] != "abstract_scheduler"
        try:
            observed = await dispatch(case, payload)
        except (EnvironmentUnavailable, AdapterGap, AssertionError):
            raise
        except Exception as exc:
            from openverify.errors import ProtocolError
            from openverify.provider import ProviderContractError

            if not isinstance(exc, (ProtocolError, ProviderContractError)):
                raise
            code = getattr(exc, "code", None)
            if code is None:
                raise
            observed = {
                "error_code": code,
                "message": exc.message,
                "structured_error": exc.as_dict(),
            }
        if case["operation"] in ("run", "policy_run", "metamorphic_run") and not (
            expected.get("error_code") or expected.get("reject")
        ):
            scenario = deepcopy(payload)
            check_record(observed["record"], scenario)
            import re

            for identity, facts in scenario["nodes"].items():
                if identity not in scenario.get("behaviors", {}):
                    continue
                provider = "com.example.golden.p_" + re.sub("[^a-z0-9_]", "_", identity.lower())
                calls = [c for c in observed["calls"] if c["provider_id"] == provider]
                if facts["state"] == "SUCCESS":
                    equal(1, len(calls), f"/{identity}/provider_calls")
                    actual_node = next(
                        n for n in observed["record"]["nodes"] if n["node_id"] == identity
                    )
                    equal(
                        actual_node["input_values"],
                        calls[0]["input"],
                        f"/{identity}/provider_consumed_values",
                    )
                elif facts["state"] == "NONEXECUTED":
                    equal([], calls, f"/{identity}/nonexecution_calls")
            for sc, variant in observed.get("variants", []):
                sc = deepcopy(sc)
                check_record(variant["record"], sc)
        elif case["operation"] == "abstract_scheduler":
            equal(expected, observed)
            row["scope"] = "MODEL_ONLY_NOT_SUT_CONFORMANCE"
        elif case["operation"] == "mutation_probe":
            if not observed.get("detected"):
                raise Difference("mutant survived: " + payload["mutant"])
            row["scope"] = "ACTUAL_EXECUTION_OBSERVATION_MUTATION"
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
        if observed.get("error_code"):
            row["observed_error"] = (
                observed["structured_error"]
                if "structured_error" in observed
                else observed["error_code"]
            )
        if "record" in observed and case["operation"] in ("run", "policy_run", "metamorphic_run"):
            row["observed_node_states"] = {
                n["node_id"]: {
                    "state": n["state"],
                    "resolutions": n["input_resolutions"],
                    "observation_error": (n.get("observation") or {}).get("error"),
                }
                for n in observed["record"]["nodes"]
            }
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
