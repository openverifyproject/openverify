"""Assertion reconciliation against the existing 615 canonical records.

This is an execution audit, not a replacement contract inventory. Links are
explicit reviewed predicates, never inferred from names, fixture counts or
Python coverage. A representative is not a discharge of an unbounded domain.
"""

import ast
import collections
import gzip
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "conformance/golden-v4/verification-final"
MODEL = ROOT / "conformance/golden-v4/canonical-review-v2/CANONICAL_REQUIREMENTS.jsonl"


def rows(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def write(name, value):
    (OUT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


@lru_cache
def checks(path, function):
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    owner = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == function
    )
    found = []
    for n in ast.walk(owner):
        if isinstance(n, ast.Assert):
            found.append({"path": path, "line": n.lineno, "predicate": ast.unparse(n.test)})
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "raises"
        ):
            found.append({"path": path, "line": n.lineno, "predicate": ast.unparse(n)})
    return found


def main():
    primary = {
        r["requirement_id"]: r
        for r in rows(MODEL)
        if r["record_kind"] in ("SEMANTIC_REQUIREMENT", "WHOLE_ROOT_STRUCTURAL_REQUIREMENT")
    }
    assert len(primary) == 615
    latest = Path((ROOT / ".pytest_cache/golden-v4/LATEST").read_text())
    golden = rows(latest / "results.jsonl")
    regressions = rows(OUT / "REGRESSION_RESULTS.jsonl")
    links = collections.defaultdict(list)
    execution = {}

    def attach(ids, cases, assertion_checks, scope):
        assert assertion_checks, (ids, scope)
        for i in ids:
            assert i in primary, i
            for c in cases:
                stimulus = c.get("stimulus", {})
                value = stimulus.get("value", {})
                if i.startswith("CM.VCP.RESULT.") and stimulus.get("object_type") == "result":
                    d, e, a, k = (
                        value.get(f)
                        for f in (
                            "disposition",
                            "execution_outcome",
                            "applicability",
                            "determination",
                        )
                    )
                    if ".ERROR." in i and not (d == "EXECUTED" and e == "ERROR"):
                        continue
                    if ".NONEXECUTION." in i and d == "EXECUTED":
                        continue
                    if ".NOT_APPLICABLE." in i and not (
                        d == "EXECUTED" and e == "SUCCESS" and a == "NOT_APPLICABLE"
                    ):
                        continue
                    if ".UNKNOWN." in i and not (
                        d == "EXECUTED" and e == "SUCCESS" and a == "APPLICABLE" and k == "UNKNOWN"
                    ):
                        continue
                policy_path = stimulus.get("path")
                if policy_path and i.startswith("CM.VCP.POLICY."):
                    only = {
                        "CM.VCP.POLICY.INACTIVE": {"INACTIVE"},
                        "CM.VCP.POLICY.UNSELECTED": {"UNSELECTED"},
                        "CM.VCP.POLICY.ADMISSION": {"RUN", "SKIP", "DEFER"},
                        "CM.VCP.POLICY.SKIP": {"SKIP"},
                        "CM.VCP.POLICY.DEFER": {"DEFER"},
                    }
                    if i in only and policy_path not in only[i]:
                        continue
                key = c.get("case_id", c.get("selector"))
                execution[key] = c
                links[i].append(
                    {
                        "case_id": key,
                        "status": c["status"],
                        "assertions": assertion_checks,
                        "scope": scope,
                        "expected": c.get("expected"),
                        "actual": c.get("actual"),
                        "repro": c.get("repro", c.get("rerun")),
                    }
                )

    def family(suffix, ids, scope, function=None):
        selected = [r for r in golden if r["family"] == suffix]
        assert selected, suffix
        locus = checks("tests/golden_v4/reporters/runner.py", "run_case")
        if function:
            locus += checks("tests/golden_v4/runtime.py", function)
        attach(ids, selected, locus, scope)

    def action(action_name, ids, scope, function=None):
        selected = [r for r in golden if r["action"] == action_name]
        assert selected, action_name
        locus = checks("tests/golden_v4/reporters/runner.py", "run_case")
        if function:
            locus += checks("tests/golden_v4/runtime.py", function)
        attach(ids, selected, locus, scope)

    # Import the prior reviewed subset as links only; never inherit its coverage
    # claims, counts or status. Actual latest executions supply each result.
    with gzip.open(
        ROOT / "conformance/golden-v4/reconciliation-v2/TEST_RECONCILIATION.jsonl.gz",
        "rt",
        encoding="utf-8",
    ) as stream:
        prior = [json.loads(s) for s in stream]
    by_id = {r["case_id"]: r for r in golden}
    for c in prior:
        if c["case_id"] in by_id and c["canonical_ids"]:
            attach(
                c["canonical_ids"],
                [by_id[c["case_id"]]],
                checks("tests/golden_v4/reporters/runner.py", "run_case"),
                "Previously reviewed assertion, re-executed; stated finite representative only.",
            )
    result_ids = [
        i
        for i in primary
        if i.startswith("CM.VCP.RESULT.")
        and i
        not in {
            "CM.VCP.RESULT.FLATTEN",
            "CM.VCP.RESULT.INVOKED",
            "CM.VCP.RESULT.NONEXEC_EVIDENCE",
            "CM.VCP.RESULT.SEVERITY",
            "CM.VCP.RESULT.SCORE_MEANING",
            "CM.VCP.RESULT.INDEPENDENCE",
        }
    ]
    for f in ["WIRE_AXIS", "SEMANTIC_AXIS", "OBS_MASK"]:
        family(
            "V4.VCP.RESULT." + f,
            result_ids,
            "Joint Result predicate: complete declared categorical/valid-payload projection. Not arbitrary payload/schema coverage.",
        )
    family(
        "V4.VCP.RESULT.VALUES",
        ["CM.VCP.RESULT.SCORE_MEANING", "CM.VCP.RESULT.INDEPENDENCE"],
        "Authored numeric/null/type boundaries only.",
    )
    family(
        "V4.VCP.NODE.INVOKED_RESULT",
        ["CM.VCP.RESULT.INVOKED"],
        "Accepted EXECUTED success/error and rejected standalone nonexecution; kind-specific acceptance.",
    )
    family(
        "V4.VCP.GRAPH.DAG_0_4",
        ["CM.VCP.GRAPH.UNSUPPORTED"],
        "All labelled loop-free topologies at n<=4, not arbitrary graph correctness.",
    )
    family(
        "V4.VCP.GRAPH.DEFINITION",
        [
            "CM.VCP.GRAPH.IDENTITY.EDGE_ID",
            "CM.VCP.GRAPH.IDENTITY.ENDPOINT",
            "CM.VCP.GRAPH.IDENTITY.NODE_ID",
        ],
        "Distinct authored identity mutations; joint parser predicate.",
    )
    family(
        "V4.VCP.GRAPH.FEATURES",
        ["CM.VCP.GRAPH.UNSUPPORTED"],
        "Four supported/unsupported feature subsets.",
    )
    family(
        "V4.VCP.NODE.ROLE",
        [
            "CM.VCP.DATA.DERIVE_ROLE",
            "CM.VCP.DATA.PRIMARY_RESULT.ROLES",
            "CM.VCP.DATA.PRIMARY_DECISION.ROLES",
        ],
        "Twelve kind/role pairs; unrelated primary-output prerequisites fixed.",
    )
    family(
        "V4.VCP.NODE.PRIMARY",
        [
            "CM.VCP.DATA.PRIMARY_RESULT.NAME",
            "CM.VCP.DATA.PRIMARY_RESULT.CARDINALITY",
            "CM.VCP.DATA.PRIMARY_DECISION.NAME",
            "CM.VCP.DATA.PRIMARY_DECISION.CARDINALITY",
        ],
        "Primary name/cardinality mutation projection.",
    )
    family(
        "V4.VCP.SOURCE.POLICY",
        ["CM.VCP.POLICY.SOURCES"],
        "Twelve ValueSource/policy-role coordinates.",
    )
    family(
        "V4.VCP.SCHEMA.PRIMITIVE",
        ["CM.VCP.SCHEMA.STATIC", "CM.SDK.SCHEMA.INCOMPATIBLE"],
        "49 primitive overlap pairs only; no full schema implication claim.",
    )
    family(
        "V4.VCP.SCHEMA.FULL",
        ["CM.VCP.SCHEMA.SUBSET"],
        "Authored schema syntax/reference cases including corrected invalid description annotation.",
    )
    family(
        "V4.VCP.AGG.MEMBER_ROLE",
        ["CM.VCP.AGG.MEMBERS.SOURCE_ROLE"],
        "Twelve producer kind/output role pairs.",
    )
    family(
        "V4.VCP.AGG.SEMANTIC",
        [
            "CM.VCP.AGG.MEMBERS_INPUT.CONSTANT",
            "CM.VCP.DATA.SEMANTIC_SUBJECT.SUBJECT",
            "CM.VCP.DATA.SEMANTIC_SUBJECT.CRITERION",
        ],
        "Exact authored semantic snapshot mutations; not every membership invariant.",
    )
    family(
        "V4.VCP.AGG.EXCEPTION",
        ["CM.VCP.AGG.IGNORE", "CM.VCP.AGG.REJECT", "CM.VCP.AGG.MISSING"],
        "112 reducer/exception/handler laws with fixed retained inputs.",
    )
    family(
        "V4.VCP.AGG.SEVERITY",
        [
            "CM.VCP.AGG.SEVERITY_RESULT",
            "CM.VCP.AGG.SEVERITY_DOMAIN.MEMBER_DOMAIN",
            "CM.VCP.AGG.SEVERITY_DOMAIN.MEMBER_LABEL",
        ],
        "Authored severity-domain/member boundaries.",
    )
    family(
        "V4.VCP.AGG.WEIGHT_IDENTITY",
        ["CM.VCP.AGG.WEIGHT_KEYS.IDENTITY", "CM.VCP.AGG.WEIGHTED.SCORE"],
        "Two unequal original weights after filtering/reordering.",
    )
    family(
        "V4.VCP.AGG.WEIGHT_SIGN_2",
        ["CM.VCP.AGG.WEIGHTED.ORIGINAL_WEIGHTS"],
        "Nine original sign pairs; six corrected configuration errors.",
    )
    family(
        "V4.VCP.POLICY.ROLE_RESULT",
        [
            "CM.VCP.POLICY.OUTCOME_ACTIVATION",
            "CM.VCP.POLICY.OUTCOME_SELECTION",
            "CM.VCP.POLICY.OUTCOME_ADMISSION",
        ],
        "Nine role/outcome-object pairs.",
    )
    action(
        "policy_path",
        [
            "CM.VCP.POLICY.ORDER",
            "CM.VCP.POLICY.INACTIVE",
            "CM.VCP.POLICY.UNSELECTED",
            "CM.VCP.POLICY.ADMISSION",
            "CM.VCP.POLICY.SKIP",
            "CM.VCP.POLICY.DEFER",
        ],
        "Five reachable ordered policy paths; exact call list and record effects.",
        "policy_path",
    )
    action(
        "policy_order",
        ["CM.VCP.PROV.POLICY_ORDER.STAGES"],
        "All six policy-role permutations rejected/accepted by record parser.",
    )
    action(
        "resolve",
        [
            "CM.VCP.DATA.RESOLVE_ALL",
            "CM.VCP.DATA.RESOLVE_BLOCK.NONINVOCATION",
            "CM.VCP.DATA.RESOLVE_BLOCK.REASON",
            "CM.VCP.DATA.RESOLVE_BLOCK.PROVENANCE",
        ],
        "Actual consumed values, exact authored source, noninvocation/record assertions; statuses contextual.",
        "resolve",
    )
    for name in ["guard", "guard_source", "guard_pointer"]:
        action(
            name,
            ["CM.VCP.GUARD.EQUALITY", "CM.VCP.GUARD.ABSENT"],
            "Explicit equality/pointer/source reachability witnesses; guard false prevents invocation.",
            "guard_case",
        )
    action(
        "route",
        ["CM.VCP.LIFECYCLE.ROUTE_TARGET", "CM.VCP.LIFECYCLE.ROUTE_EXCLUSION.BRANCHES"],
        "Direct-successor versus non-successor; shared join and independent work.",
        "route",
    )
    action(
        "reason",
        [
            "CM.VCP.LIFECYCLE.NONEXEC_CAUSE",
            "CM.VCP.PROV.UNSTARTED.INFORMATION",
            "CM.VCP.PROV.UNSTARTED.OBSERVATION",
        ],
        "Nine declared nonexecution reasons, diagnostic Result and absent executor observation.",
        "reason_witness",
    )
    action(
        "cancel_record",
        [
            "CM.VCP.LIFECYCLE.CANCEL_ADMISSION",
            "CM.VCP.LIFECYCLE.CANCEL_RUNNING.STATE",
            "CM.VCP.LIFECYCLE.CANCEL_RUNNING.OBSERVATION",
            "CM.VCP.LIFECYCLE.CANCEL_RUNNING.LATER",
        ],
        "Six phase/admission coordinates, genuine token cancellation and retained usage.",
        "cancellation_witness",
    )
    action(
        "motif",
        [
            "CM.VCP.GRAPH.READINESS",
            "CM.VCP.GRAPH.NO_DATA",
            "CM.RELAY.SCHED.ORDER",
            "CM.RELAY.SCHED.ISOLATION",
            "CM.RELAY.SCHED.CONTROL",
        ],
        "Named small graph/independence/wave witnesses only; no universal scheduler induction.",
        "motif",
    )
    action(
        "lineage",
        [
            "CM.VCP.PROV.RECONSTRUCT.VALUES",
            "CM.VCP.PROV.RECONSTRUCT.RESOLUTIONS",
            "CM.VCP.PROV.UPSTREAM_SNAPSHOTS",
        ],
        "Seven targeted isolated record corruptions; not coherent-forgery authentication.",
        "lineage",
    )
    # Provider tests below are cheap local protocol validation, not malicious live
    # providers. Legal live_event cases are separately recorded in the run.
    action(
        "provider_init", ["CM.PROVIDER.INIT.SELECT"], "Three exact initialization version lists."
    )
    action(
        "provider_transition",
        [
            "CM.PROVIDER.LIFE.CORRELATION.UNKNOWN",
            "CM.PROVIDER.LIFE.CORRELATION.AFTER_TERMINAL",
            "CM.PROVIDER.LIFE.CORRELATION.DUPLICATE_OUTCOME",
        ],
        "Sixteen observed state/action correlation coordinates.",
    )
    action(
        "provider_cancel",
        ["CM.PROVIDER.CANCEL.UNKNOWN", "CM.PROVIDER.CANCEL.TERMINAL", "CM.PROVIDER.FEATURE.CANCEL"],
        "Eight correlation/support coordinates.",
    )
    action(
        "provider_terminal",
        ["CM.PROVIDER.CANCEL.CAUSE", "CM.PROVIDER.DEADLINE.ACTIVE.NO_LATE_COMPLETE"],
        "24 terminal/cancel/deadline coordinates with explicit provider clock.",
    )
    action(
        "provider_invocation",
        ["CM.PROVIDER.FEATURE.DEADLINE", "CM.PROVIDER.BUDGET.EXACT"],
        "Four deadline-feature/presence and four budget/VCP-presence pairs.",
    )
    action(
        "provider_outcome",
        ["CM.PROVIDER.FEATURE.RESOURCE"],
        "32 usage/terminal/resource/VCP feature coordinates.",
    )
    action(
        "provider_event",
        ["CM.PROVIDER.FEATURE.STREAM", "CM.PROVIDER.FEATURE.RESOURCE", "CM.PROVIDER.EVENT.PAYLOAD"],
        "48 event/feature coordinates; malformed objects remain local.",
    )
    family(
        "V4.PROVIDER.EVENT.SEQUENCE",
        ["CM.PROVIDER.LIFE.SEQUENCE.FIRST", "CM.PROVIDER.LIFE.SEQUENCE.INCREASE"],
        "Schema-level positive sequence boundaries; ordering requirements require lifecycle witnesses separately.",
    )
    family(
        "V4.PROVIDER.VCP_COMPAT",
        ["CM.PROVIDER.COMPAT.CAPABILITY_VCP.ADVERTISEMENT"],
        "Capability declaration x manifest support projection.",
    )
    for c in golden:
        if c["action"] == "port":
            methods = {
                "CATALOG.PROVIDERS": "ProviderCatalog.providers",
                "BINDER.BIND": "ProviderBinder.bind",
                "DRIVER.EXECUTE": "ExecutionDriver.execute",
                "TRANSPORT.INVOKE": "ProviderTransport.invoke",
                "SINK.EMIT": "EventSink.emit",
                "STORE.GET.NONE": "RecordStore.get",
                "STORE.GET": "RecordStore.get",
                "STORE.PUT": "RecordStore.put",
                "OBSERVER.OBSERVE": "EventObserver.observe",
            }
            key = c["stimulus"]["method"]
            assert key in methods, key
            attach(
                ["CM.RELAY.PORT." + methods[key]],
                [c],
                checks("tests/golden_v4/runtime.py", "port_witness"),
                "Direct compliant port return/event/snapshot witness; declared exception subspaces separate.",
            )
        if c["action"] == "schema_root":
            path = c["stimulus"]["path"]
            root = next(
                i
                for i, r in primary.items()
                if r["record_kind"] == "WHOLE_ROOT_STRUCTURAL_REQUIREMENT"
                and any(s.get("path") == path for s in r["sources"])
            )
            attach(
                [root],
                [c],
                checks("tests/golden_v4/sut.py", "execute"),
                "Package/source schema equality, offline root identity and Draft metaschema validity ONLY; does not discharge complete root acceptance.",
            )
    for r in regressions:
        if r["canonical_ids"]:
            attach(
                r["canonical_ids"],
                [r],
                [{"path": r["assertion"]["path"], **a} for a in r["assertion"]["assertions"]],
                "Exact revision witness assertion; see selector and explicit context. No blanket domain closure.",
            )
    # These predicates were inspected in the existing unit/integration sources.
    # Merely being collected, having a suggestive name or using a fixture earns
    # no link. Parameterized functions retain every actual JUnit execution ID.
    ordinary = []
    for t in ET.parse(ROOT / ".pytest_cache/verification-existing.xml").iter("testcase"):
        path = t.attrib["classname"].replace(".", "/") + ".py"
        name = t.attrib["name"]
        ordinary.append(
            {
                "selector": path + "::" + name,
                "case_id": path + "::" + name,
                "path": path,
                "function": name.split("[")[0],
                "status": "SKIP"
                if t.find("skipped") is not None
                else "FAIL"
                if t.find("failure") is not None or t.find("error") is not None
                else "PASS",
                "duration": float(t.attrib["time"]),
                "repro": 'python -m pytest -q "' + path + "::" + name + '"',
            }
        )

    def ordinary_witness(path, function, ids):
        selected = [
            c
            for c in ordinary
            if c["path"] == path and c["function"] == function and c["status"] != "SKIP"
        ]
        assert selected, (path, function)
        attach(
            ids,
            selected,
            checks(path, function),
            "Reviewed existing assertion expression and exception expectation. Exact parametrized JUnit execution; bounded witness, not domain-wide proof. Runtime values were not serialized by this existing suite.",
        )

    specs = [
        (
            "tests/unit/test_json_equality.py",
            "test_json_snapshot_types_and_array_order",
            ["CM.SHARED.JSON_EQUALITY", "CM.SDK.JSON.EQUALITY"],
        ),
        (
            "tests/unit/test_json_equality.py",
            "test_json_snapshot_equal_values",
            ["CM.SHARED.JSON_EQUALITY", "CM.SDK.JSON.EQUALITY"],
        ),
        (
            "tests/unit/test_values.py",
            "test_json_rejections",
            ["CM.VCP.WIRE.JSON.DUPLICATE_KEYS", "CM.VCP.WIRE.JSON.FINITE"],
        ),
        ("tests/unit/test_values.py", "test_non_json_values", ["CM.VCP.WIRE.JSON.JSON_TYPES"]),
        (
            "tests/unit/test_values.py",
            "test_frozen_outer_model_and_revalidation",
            ["CM.SDK.MODEL.CONSTRUCTION.FROZEN", "CM.SDK.MODEL.CONSTRUCTION.SEMANTIC_BOUNDARY"],
        ),
        (
            "tests/unit/test_values.py",
            "test_required_null_and_optional_extensions_roundtrip",
            ["CM.VCP.WIRE.NULL.PAYLOADS", "CM.SDK.SERIALIZE.DATA"],
        ),
        (
            "tests/unit/test_integral_ranks.py",
            "test_integral_json_rank_normalized",
            ["CM.SDK.MODEL.INTEGRAL_NORMALIZATION", "CM.VCP.AGG.SEVERITY_DOMAIN.RANK_UNIQUE"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_rejected_ids_cannot_be_retried",
            ["CM.VCP.BIND.INPUT", "CM.PROVIDER.WIRE.ATTEMPT_ID.SESSION_UNIQUENESS"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_work_before_init_and_second_init",
            ["CM.PROVIDER.INIT.ONCE.PREWORK", "CM.PROVIDER.INIT.ONCE.ONCE"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_initialization_failure_closes_lifecycle",
            ["CM.PROVIDER.INIT.ONCE.FAIL_CLOSE"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_fractional_deadline_precision_and_clock_adjustment",
            ["CM.PROVIDER.DEADLINE.PRECISION.FRACTION", "CM.PROVIDER.DEADLINE.IRREVERSIBLE"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_deadline_requires_clock_and_expired_invocation_has_no_events",
            ["CM.PROVIDER.DEADLINE.ACCEPT.ACCEPT", "CM.PROVIDER.DEADLINE.ACCEPT.TERMINAL"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_stdio_utf8_split_at_every_byte_and_coalescing",
            [
                "CM.PROVIDER.STDIO.RECEIVE.PARTIAL",
                "CM.PROVIDER.STDIO.RECEIVE.COALESCED",
                "CM.SDK.PROVIDER.FRAME.ENCODE",
                "CM.SDK.PROVIDER.FRAME.DECODE",
            ],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_stdio_invalid_frames_poison_decoder",
            ["CM.SDK.PROVIDER.FRAME.FAILURE", "CM.PROVIDER.STDIO.RECEIVE.CLOSE"],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_stdio_cancel_race_and_two_correlations",
            [
                "CM.PROVIDER.RPC.CANCEL_ACK.NULL",
                "CM.PROVIDER.RPC.CANCEL_ACK.RACE",
                "CM.PROVIDER.RPC.EVENT_BEFORE_RESULT.DUAL_CORRELATION",
            ],
        ),
        (
            "tests/unit/test_provider_contract.py",
            "test_stdio_rejection_before_work_vs_error_after_events",
            ["CM.PROVIDER.RPC.ERROR_CHANNEL", "CM.PROVIDER.RPC.RESERVED_ERRORS.CONTRACT_REJECTION"],
        ),
        (
            "tests/integration/test_provider_binding.py",
            "test_exact_bound_input_config_output_and_provenance",
            [
                "CM.VCP.BIND.PROVENANCE.OCCURRENCE_MAP",
                "CM.VCP.BIND.PROVENANCE.NODE_COPY",
                "CM.VCP.BIND.PROVENANCE.EXECUTOR",
                "CM.VCP.DATA.CONFIG.SEPARATE",
                "CM.VCP.DATA.CAPABILITY_SHAPE.INPUT",
                "CM.VCP.DATA.CAPABILITY_SHAPE.CONFIG",
            ],
        ),
        (
            "tests/integration/test_provider_binding.py",
            "test_provider_configuration_is_checked_before_invocation",
            ["CM.PROVIDER.INVOKE.VALIDATE.CONFIG", "CM.VCP.BIND.INPUT"],
        ),
        (
            "tests/integration/test_provider_binding.py",
            "test_provider_input_rejects_values_accepted_by_vcp",
            [
                "CM.PROVIDER.INVOKE.VALIDATE.INPUT",
                "CM.VCP.BIND.INPUT",
                "CM.VCP.BIND.PROVENANCE.ONLY_INVOKED",
            ],
        ),
        (
            "tests/integration/test_provider_binding.py",
            "test_invalid_provider_output_retains_usage_and_cannot_feed_downstream",
            [
                "CM.VCP.BIND.OUTPUT_REJECTION.RETAIN",
                "CM.VCP.BIND.OUTPUT_REJECTION.DIAGNOSIS",
                "CM.VCP.BIND.OUTPUT_REJECTION.ACCEPTANCE",
                "CM.VCP.OBS.RETENTION.USAGE",
                "CM.VCP.OBS.RETENTION.SNAPSHOT",
            ],
        ),
        (
            "tests/integration/test_provider_binding.py",
            "test_vcp_semantic_boundary_still_rejects_contract_valid_output",
            ["CM.VCP.DATA.ATOMIC_OUTPUT.MISSING", "CM.VCP.DATA.ATOMIC_OUTPUT.ATOMIC"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_failed_producer_cannot_read_stale_run_or_ambient_value",
            [
                "CM.VCP.DATA.RESOLVE_BLOCK.STATE",
                "CM.VCP.DATA.RESOLVE_BLOCK.RESULT",
                "CM.VCP.DATA.CONTEXT.AMBIENT",
            ],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_usage_survives_invalid_semantic_output_for_every_kind",
            ["CM.VCP.OBS.RETENTION.USAGE", "CM.VCP.DATA.ATOMIC_OUTPUT.ATOMIC"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_usage_disagreement_invalidates_output_without_erasing_observed_usage",
            ["CM.VCP.OBS.AUTHORITY.OVERLAP", "CM.VCP.OBS.RETENTION.USAGE"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_invalid_judgment_retains_result_reported_usage",
            ["CM.VCP.DATA.JUDGMENT", "CM.VCP.OBS.RETENTION.USAGE"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_explicit_null_judgment_is_validated",
            ["CM.VCP.DATA.JUDGMENT"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_error_bookkeeping_does_not_bypass_refined_result_output_schema",
            ["CM.VCP.DATA.BOOKKEEPING"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_external_reference_remains_exact_and_unfetched",
            ["CM.VCP.KNOWLEDGE.REFERENCE"],
        ),
        (
            "tests/integration/test_typed_dataflow.py",
            "test_subject_and_criterion_are_authoritative_explicit_inputs",
            ["CM.VCP.DATA.SEMANTIC_SUBJECT.CRITERION"],
        ),
        (
            "tests/integration/test_occurrence_lifecycle.py",
            "test_executed_semantic_states_never_become_nonexecution",
            ["CM.VCP.RESULT.OUTCOME", "CM.VCP.RESULT.SUCCESS"],
        ),
        (
            "tests/integration/test_occurrence_lifecycle.py",
            "test_standalone_nonexecution_still_accepts_diagnostic_evidence",
            ["CM.VCP.RESULT.NONEXEC_EVIDENCE"],
        ),
        (
            "tests/integration/test_occurrence_lifecycle.py",
            "test_cancellation_after_a_completed_node_does_not_rewrite_it",
            ["CM.VCP.LIFECYCLE.TERMINAL.IMMUTABILITY", "CM.VCP.LIFECYCLE.CANCEL_RUNNING.RESULT"],
        ),
        (
            "tests/integration/test_provenance_invariants.py",
            "test_admission_skip_complete_multinode_record",
            ["CM.VCP.PROV.NODE_SET.EXACT", "CM.VCP.LIFECYCLE.TERMINAL.CARDINALITY"],
        ),
        (
            "tests/relay/test_concurrency.py",
            "test_independent_nodes_overlap_dependencies_wait_and_snapshots_isolate",
            [
                "CM.VCP.PROV.TIMING.DEPENDENCY",
                "CM.RELAY.SCHED.WAVE.BARRIER",
                "CM.RELAY.SCHED.ORDER",
            ],
        ),
        (
            "tests/relay/test_concurrency.py",
            "test_concurrent_graphs_different_inputs_and_no_cancellation_leakage",
            ["CM.RELAY.SCHED.ISOLATION"],
        ),
        (
            "tests/relay/test_concurrency.py",
            "test_running_cancellation_and_timeout_are_distinct",
            ["CM.RELAY.CANCEL.TOKEN", "CM.RELAY.DRIVER.TIMEOUT"],
        ),
        (
            "tests/relay/test_architecture.py",
            "test_dependency_direction_and_no_hidden_globals",
            ["CM.RELAY.ARCH.DEPENDENCIES"],
        ),
        (
            "tests/relay/test_entrypoints.py",
            "test_cli_json_stdin_exit_codes_validate_inspect_and_discovery",
            [
                "CM.RELAY.CLI.JSON",
                "CM.RELAY.CLI.STDIN",
                "CM.RELAY.CLI.OPERATIONS",
                "CM.RELAY.CLI.EXIT.FAIL",
                "CM.RELAY.CLI.EXIT.PASS",
            ],
        ),
        (
            "tests/relay/test_entrypoints.py",
            "test_actual_mcp_server_discover_describe_invoke_and_inspect",
            ["CM.RELAY.MCP.TOOLS", "CM.RELAY.SERVICE.ALLOWLIST"],
        ),
        (
            "tests/relay/test_entrypoints.py",
            "test_optional_http_named_graphs_auth_and_bounds",
            [
                "CM.RELAY.HTTP.AUTH",
                "CM.RELAY.HTTP.BOUND",
                "CM.RELAY.HTTP.HEALTH",
                "CM.RELAY.HTTP.SHAPE.INVALID_INPUT",
            ],
        ),
        (
            "tests/relay/test_local_paths.py",
            "test_action_directory_prefixes",
            ["CM.RELAY.ACTION.PREFIX", "CM.RELAY.STANDARD.ACTION_POLICY"],
        ),
        (
            "tests/relay/test_local_paths.py",
            "test_invalid_action_prefix_fails_closed",
            ["CM.RELAY.STANDARD.ACTION_POLICY"],
        ),
        (
            "tests/relay/test_local_paths.py",
            "test_directory_membership",
            ["CM.RELAY.SCOPE.PATH", "CM.RELAY.STANDARD.SCOPE.ORDER"],
        ),
        (
            "tests/relay/test_local_paths.py",
            "test_half_open_ranges_and_empty_ranges",
            ["CM.RELAY.SCOPE.RANGES"],
        ),
        (
            "tests/relay/test_local_paths.py",
            "test_exact_files_relative_absolute_and_missing",
            ["CM.RELAY.STANDARD.SCOPE.EMPTY"],
        ),
        (
            "tests/relay/test_standard.py",
            "test_json_parse_schema_boolean_number_and_pattern",
            ["CM.RELAY.STANDARD.JSON_PARSE", "CM.RELAY.STANDARD.SCHEMA", "CM.RELAY.STANDARD.TEXT"],
        ),
        (
            "tests/relay/test_standard.py",
            "test_filesystem_selection_and_binary_observation",
            ["CM.RELAY.STANDARD.SELECT_FILES", "CM.RELAY.STANDARD.READ_FILE"],
        ),
        (
            "tests/relay/test_standard.py",
            "test_missing_tool_is_execution_error_with_installation_help",
            ["CM.RELAY.STANDARD.TOOLS_DISCOVERY"],
        ),
        (
            "tests/relay/test_tools.py",
            "test_real_code_fail_fix_pass_and_changed_span_scoping",
            ["CM.RELAY.STANDARD.RUFF", "CM.RELAY.STANDARD.ASTGREP", "CM.RELAY.TEMPLATES"],
        ),
        (
            "tests/relay/test_tools.py",
            "test_text_document_actual_files_missing_binary_large_and_path_scope",
            ["CM.RELAY.STANDARD.READ_TEXT", "CM.RELAY.SECURITY.FILES"],
        ),
        (
            "tests/relay/test_tools.py",
            "test_command_capture_host_observation_and_pytest",
            ["CM.RELAY.STANDARD.COMMAND_CHECK", "CM.RELAY.STANDARD.PYTEST"],
        ),
        (
            "tests/relay/test_git.py",
            "test_comparison_modes_are_distinct",
            ["CM.RELAY.GIT.MODES", "CM.RELAY.STANDARD.GIT_SCOPE"],
        ),
        (
            "tests/relay/test_git.py",
            "test_renamed_deleted_and_untracked",
            ["CM.RELAY.GIT.CHANGES", "CM.RELAY.STANDARD.GIT.DELETE"],
        ),
        (
            "tests/relay/test_git.py",
            "test_scope_changes_during_derivation_reject",
            ["CM.RELAY.STANDARD.GIT.FRESHNESS"],
        ),
        (
            "tests/unit/test_admission.py",
            "test_boundaries_and_skipped_provenance",
            ["CM.VCP.POLICY.PROBABILITY.BOUNDARIES"],
        ),
        (
            "tests/unit/test_admission.py",
            "test_invalid_probability",
            ["CM.VCP.POLICY.PROBABILITY.DOMAIN"],
        ),
        (
            "tests/unit/test_admission.py",
            "test_repeatable_sampling_and_always",
            ["CM.VCP.POLICY.ALWAYS", "CM.VCP.POLICY.PROBABILITY.INTERIOR"],
        ),
        ("tests/unit/test_aggregation.py", "test_empty_rejected", ["CM.VCP.AGG.NONEMPTY"]),
        (
            "tests/unit/test_aggregation.py",
            "test_tie_and_all_ignored_and_zero_retained_weight",
            ["CM.VCP.AGG.WEIGHTED.RETAINED_TOTAL"],
        ),
        (
            "tests/property/test_provider_contract.py",
            "test_provider_extension_roundtrip",
            ["CM.PROVIDER.EXT.ROUNDTRIP.PRESERVE"],
        ),
        (
            "tests/property/test_provider_contract.py",
            "test_provider_event_monotonicity",
            ["CM.PROVIDER.LIFE.SEQUENCE.DUPLICATE", "CM.PROVIDER.LIFE.SEQUENCE.REORDER"],
        ),
        (
            "tests/property/test_provider_contract.py",
            "test_provider_exactly_one_terminal",
            ["CM.PROVIDER.LIFE.TERMINAL.EXACTLY_ONCE"],
        ),
        (
            "tests/property/test_typed_dataflow.py",
            "test_arbitrary_json_survives_all_bound_snapshots",
            ["CM.VCP.DATA.CONTEXT.ISOLATION"],
        ),
        (
            "tests/property/test_typed_dataflow.py",
            "test_every_required_port_has_exactly_one_declared_binding",
            ["CM.VCP.DATA.BIND_TARGET"],
        ),
        (
            "tests/property/test_typed_dataflow.py",
            "test_topological_order_is_independent_of_node_array_order",
            ["CM.VCP.GRAPH.ORDER", "CM.VCP.PROV.NODE_SET.ORDER"],
        ),
        (
            "tests/property/test_typed_dataflow.py",
            "test_aggregate_membership_is_stable_across_result_states",
            ["CM.VCP.AGG.MEMBER_STATES"],
        ),
        (
            "tests/relay/test_execution.py",
            "test_raw_json_equivalence_and_input_snapshot",
            [
                "CM.RELAY.API.RUN",
                "CM.VCP.PROV.RECORD_ANCHOR.SNAPSHOTS",
                "CM.RELAY.TEXT.COORDINATES.OFFSETS",
                "CM.RELAY.TEXT.COORDINATES.LINECOL",
            ],
        ),
        (
            "tests/relay/test_execution.py",
            "test_inputs_rejected_before_invocation",
            [
                "CM.VCP.DATA.RUN_ACCEPT.MISSING_REQUIRED",
                "CM.VCP.DATA.RUN_ACCEPT.UNKNOWN_NAME",
                "CM.VCP.DATA.RUN_ACCEPT.VALUE_SCHEMA",
            ],
        ),
        (
            "tests/relay/test_execution.py",
            "test_catalog_binding_and_explicit_precedence",
            ["CM.RELAY.BIND.SELECT", "CM.RELAY.CATALOG.TRUST.DUPLICATE"],
        ),
        (
            "tests/relay/test_execution.py",
            "test_control_termination",
            ["CM.VCP.LIFECYCLE.STOP", "CM.VCP.LIFECYCLE.DEFER", "CM.VCP.LIFECYCLE.RETRY"],
        ),
        (
            "tests/relay/test_execution.py",
            "test_routes_shared_joins_and_guard_false_without_implicit_propagation",
            [
                "CM.VCP.DATA.RESOLVE_BLOCK.DOWNSTREAM",
                "CM.VCP.LIFECYCLE.ROUTE_EXCLUSION.DEPENDENCIES",
            ],
        ),
        (
            "tests/relay/test_execution.py",
            "test_observer_failure_store_snapshots_and_guardrail",
            [
                "CM.RELAY.OBSERVER.ERROR",
                "CM.RELAY.STORE.COPY",
                "CM.RELAY.STORE.SCOPE",
                "CM.RELAY.API.GATE.WAIT",
                "CM.RELAY.API.GATE.ACTION",
            ],
        ),
        (
            "tests/relay/test_process.py",
            "test_capture_bounds_and_environment",
            ["CM.RELAY.PROCESS.ARGV_ENV"],
        ),
        (
            "tests/relay/test_process.py",
            "test_timeout_kills_descendants_after_tool_parent_exits",
            ["CM.RELAY.PROCESS.CLEANUP.TEARDOWN", "CM.RELAY.PROCESS.WINDOWS_PRESTART"],
        ),
        (
            "tests/relay/test_core.py",
            "test_builder_portable_deterministic_and_invalid_graphs",
            [
                "CM.SDK.AUTHORING.GRAPH.BUILD",
                "CM.SDK.AUTHORING.GRAPH.TO_JSON",
                "CM.SDK.AUTHORING.GRAPH.INSPECT",
            ],
        ),
        (
            "tests/relay/test_core.py",
            "test_duplicate_and_expansion_reject",
            ["CM.VCP.DATA.RUN_NAMES"],
        ),
        (
            "tests/relay/test_reducers_graph.py",
            "test_real_bound_reducers",
            ["CM.RELAY.STANDARD.AGGREGATE"],
        ),
        (
            "tests/unit/test_error_code_compatibility.py",
            "test_nested_enum_normalization_copies_changed_containers_only",
            ["CM.SDK.JSON.NORMALIZE"],
        ),
        (
            "tests/test_error_contract_hardening.py",
            "test_provider_namespaced_errors_stay_extensible",
            ["CM.PROVIDER.ERROR.CLASSIFY"],
        ),
        (
            "tests/test_error_contract_hardening.py",
            "test_provider_code_wire_roundtrip",
            ["CM.SDK.PROVIDER.SERIALIZE", "CM.SDK.PROVIDER.WIRE_DATA"],
        ),
    ]
    for path, function, ids in specs:
        ordinary_witness(path, function, ids)
    # Every primary record is reconciled. No unreviewed record is called a missing
    # test: absence of a reviewed link is not proof the existing tests lack it.
    audit = []
    for i, r in primary.items():
        witnesses = list({(w["case_id"], w["scope"]): w for w in links[i]}.values())
        audit.append(
            {
                "requirement_id": i,
                "record_kind": r["record_kind"],
                "hierarchy": r["hierarchy"],
                "semantic_proposition": r["semantic_proposition"],
                "sources": r["sources"],
                "domain_refs": r.get("domain_refs", []),
                "status": "PARTIAL_ASSERTION_WITNESSES" if witnesses else "UNRECONCILED",
                "passing_witnesses": sum(w["status"] == "PASS" for w in witnesses),
                "failing_witnesses": sum(w["status"] != "PASS" for w in witnesses),
                "witnesses": witnesses,
                "proofs": [],
                "remaining": {
                    "required_relation": r["semantic_proposition"],
                    "domain": r.get("semantic_domain", r.get("predicate_domain")),
                    "reason": "Domain-wide proof/partition discharge not established by representative tests."
                    if witnesses
                    else "No reviewed assertion link. Existing test absence has NOT been established; independent review is required.",
                },
            }
        )
    with gzip.open(OUT / "CANONICAL_ASSERTION_COVERAGE.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in audit:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # Preserve every executed case identity, including uncredited cases.
    reverse = collections.defaultdict(set)
    for i, ws in links.items():
        for w in ws:
            reverse[w["case_id"]].add(i)
    with gzip.open(OUT / "TEST_ASSERTION_CROSSWALK.jsonl.gz", "wt", encoding="utf-8") as f:
        for c in [*golden, *regressions, *ordinary]:
            key = c["case_id"]
            f.write(
                json.dumps(
                    {
                        "case_id": key,
                        "canonical_ids": sorted(reverse[key]),
                        "status": c["status"],
                        "expected": c.get("expected"),
                        "actual": c.get("actual"),
                        "review": "PARTIAL_ASSERTION_LINKS"
                        if reverse[key]
                        else "NO_COVERAGE_CREDIT",
                        "repro": c.get("repro", c.get("rerun")),
                    }
                )
                + "\n"
            )
    branches = {}
    for branch in sorted({tuple(r["hierarchy"][:2]) for r in audit}):
        selected = [r for r in audit if tuple(r["hierarchy"][:2]) == branch]
        branches[" / ".join(branch)] = dict(
            records=len(selected),
            partial=sum(bool(r["witnesses"]) for r in selected),
            unreconciled=sum(not r["witnesses"] for r in selected),
            status="INCOMPLETE",
        )
    manifest = json.loads(
        (ROOT / "conformance/golden-v4/FROZEN_EXPECTATIONS/MANIFEST.json").read_text()
    )
    integrity = {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
        for p, h in manifest["files"].items()
    }
    assert all(integrity.values())
    failures = [r for r in [*golden, *regressions, *ordinary] if r["status"] == "FAIL"]
    complete = not failures and all(r["status"] == "DISCHARGED" for r in audit)
    result = {
        "verdict": "CERTIFIED FOR DECLARED SUPPORTED PROFILE" if complete else "NOT CERTIFIED",
        "canonical_records": len(audit),
        "semantic_requirements": sum(r["record_kind"] == "SEMANTIC_REQUIREMENT" for r in audit),
        "schema_predicates": sum(
            r["record_kind"] == "WHOLE_ROOT_STRUCTURAL_REQUIREMENT" for r in audit
        ),
        "partial_assertion_links": sum(bool(r["witnesses"]) for r in audit),
        "unreconciled": sum(not r["witnesses"] for r in audit),
        "fully_discharged": sum(r["status"] == "DISCHARGED" for r in audit),
        "frozen_files": integrity,
        "golden": json.loads((latest / "execution.json").read_text()),
        "revision": json.loads((OUT / "REGRESSION_EXECUTION.json").read_text()),
        "failing_case_ids": [r["case_id"] for r in failures],
        "branches": branches,
        "scaffold_cases_excluded": sum(r["action"] == "coordinate" for r in golden),
    }
    result["ordinary_execution"] = dict(
        executed=len(ordinary),
        counts=dict(collections.Counter(c["status"] for c in ordinary)),
        junit="verification-existing.xml",
        runtime_values="Existing suite did not serialize actual values; assertion expressions and JUnit outcomes retained.",
    )
    write("COVERAGE_REPORT.json", result)
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("branches", "golden", "revision", "frozen_files")
            },
            indent=2,
        )
    )
    return int(not complete)


if __name__ == "__main__":
    sys.exit(main())
