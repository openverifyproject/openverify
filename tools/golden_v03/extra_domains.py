"""Additional pure Relay laws and immutable tiny graph factory."""
from dataclasses import dataclass
import json
from itertools import product
from tools.golden_v02.build_baseline import definition, node, edge
from tools.golden_v02.enumerate_graphs import labeled_dags
from tools.golden_v03.domains import row
from tools.golden_v03.expectations import POLICIES, SUBJECT


@dataclass(frozen=True)
class TinyGraph:
    """Canonical JSON prevents mutation of nested graph containers."""
    wire: str

    @classmethod
    def build(cls, nodes, edges=(), policies=None):
        d = definition(nodes, edges)
        if policies is not None:
            d["execution_policy"] = policies
        return cls(json.dumps(d, sort_keys=True, separators=(",", ":")))

    def value(self):
        return json.loads(self.wire)


def cases():
    phases = ("PENDING", "READY", "RUNNING", "TERMINAL")
    legal = {("PENDING", "READY"), ("PENDING", "TERMINAL"), ("READY", "RUNNING"),
             ("READY", "TERMINAL"), ("RUNNING", "TERMINAL")}
    for initial, target in product(phases, repeat=2):
        yield row(f"phase.{initial}.{target}", "phase", {"initial": initial, "target": target},
            {"allowed": (initial, target) in legal}, "docs/relay/architecture.md", "node-transitions")
    for i, (n, pairs) in enumerate(labeled_dags(3)):
        for mask in range(1 << n):
            terminal = {str(k) for k in range(n) if mask & (1 << k)}
            expected = [str(k) for k in range(n) if str(k) not in terminal and
                        all(str(a) in terminal for a, b in pairs if b == k)]
            graph = TinyGraph.build([node(str(k)) for k in range(n)],
                                    [edge(str(a), str(b)) for a, b in pairs])
            yield row(f"ready.dependencies.{i}.{mask}", "dependency_readiness", {
                "graph": graph.value()["graph"], "terminal": sorted(terminal)}, {"ready": expected},
                "spec/draft/composition.md", "dependency-readiness")
    for name, changes, expected in (
        ("exact", {}, True), ("wrong_id", {"capability_id": "com.example.other"}, False),
        ("wrong_version", {"capability_version": "2"}, False),
        ("no_vcp", {"supported_vcp_versions": []}, False),
        ("no_contract", {"supported_contract_versions": ["future"]}, False),
    ):
        yield row("capability." + name, "compatibility", changes, {"compatible": expected},
            "spec/draft/provider-binding.md", "capability-matching")
    for role, object_role in product(POLICIES, repeat=2):
        yield row(f"policy.typed_role.{role}.{object_role}", "policy_outcome", {
            "role": role, "object_type": object_role.lower(), "value": POLICIES[object_role]},
            {"accept": True} if role == object_role else {"error_code": "POLICY_OUTPUT"},
            "spec/draft/execution-policy.md", "policy-role-laws")
    yield row("policy.selection.other_subject", "policy_outcome", {"role": "SELECTION",
        "object_type": "selection", "value": {"subjects": [{**SUBJECT, "id": "other"}], "reason": "known"}},
        {"error_code": "POLICY_OUTPUT"}, "spec/draft/execution-policy.md", "policy-role-laws")
    for profile in ("CONSTANT", "RUN_INPUT", "EXTERNAL_REFERENCE", "UPSTREAM_INFORMATION",
                    "UPSTREAM_RESULT", "UPSTREAM_DECISION"):
        for enabled in (True, False):
            yield row(f"guard.source.{profile}.{enabled}", "guard_source", {"profile": profile,
                "matches": enabled, "unavailable": False}, {"enabled": enabled},
                "spec/draft/dataflow.md", "guard-source-laws")
        if profile in ("RUN_INPUT", "UPSTREAM_INFORMATION", "UPSTREAM_RESULT", "UPSTREAM_DECISION"):
            yield row(f"guard.source.{profile}.unavailable", "guard_source", {"profile": profile,
                "matches": True, "unavailable": True}, {"enabled": False},
                "spec/draft/dataflow.md", "guard-source-laws")
