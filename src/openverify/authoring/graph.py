"""An explicit, small VCP builder. build() always returns a validated SDK definition."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Literal, TypedDict, Unpack, cast

from pydantic import JsonValue

from openverify.authoring.references import Ref, constant
from openverify.inspection import inspect_definition
from openverify.model import (
    AdmissionPolicy,
    ArtifactRef,
    Capability,
    Constant,
    Context,
    Criterion,
    Edge,
    ExecutionPolicy,
    Guard,
    InputPort,
    JsonSchema,
    Node,
    OperationRequirement,
    OutputPort,
    ResourceVector,
    RunInput,
    UpstreamOutput,
    VerificationDefinition,
)
from openverify.model import (
    Graph as VCPGraph,
)
from openverify.serialization import serialize, to_data
from openverify.validation import HANDLING, parse_definition

type NodeKind = Literal["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"]


@dataclass(frozen=True)
class NodeRef:
    id: str
    outputs: dict[str, Ref]

    def __getitem__(self, name: str) -> Ref:
        return self.outputs[name]

    @property
    def result(self) -> Ref:
        return self["result"]

    @property
    def decision(self) -> Ref:
        return self["decision"]


class NodeOptions(TypedDict, total=False):
    version: str
    inputs: dict[str, Ref] | None
    outputs: dict[str, JsonSchema] | None
    config: Context | None
    config_schema: JsonSchema | None
    dependencies: list[NodeRef] | None
    input_ports: list[InputPort] | None
    aggregate_inputs: list[str] | None
    resource_estimate: ResourceVector | None


class Graph:
    def __init__(
        self,
        id: str,
        *,
        version: str = "1",
        subject: ArtifactRef | None = None,
        criterion: Criterion | None = None,
        judgment_schema: JsonSchema = True,
        execution_policy: ExecutionPolicy | None = None,
    ) -> None:
        self.id = id
        self.version = version
        self.subject = subject or ArtifactRef(id=id, type="declared-input", locator={"graph": id})
        self.criterion = criterion or Criterion(id=id, description=f"Verification defined by {id}")
        self.judgment_schema = judgment_schema
        self.execution_policy = execution_policy or ExecutionPolicy(
            activation=Capability(executor_ref="MANUAL"),
            selection=Capability(executor_ref="EXPLICIT"),
            admission=AdmissionPolicy(strategy="ALWAYS"),
        )
        self._inputs: list[InputPort] = []
        self._nodes: list[Node] = []
        self._edges: list[Edge] = []

    def input(
        self,
        name: str,
        schema: JsonSchema,
        *,
        required: bool = True,
        default: Constant | None = None,
    ) -> Ref:
        self._inputs.append(
            InputPort(
                name=name,
                schema=deepcopy(schema),
                required=required,
                on_unavailable="BLOCK" if required else "DEFAULT" if default else "OMIT",
                default=default,
            )
        )
        return Ref(RunInput(name=name), deepcopy(schema))

    def node(
        self,
        id: str,
        kind: NodeKind,
        capability: str,
        *,
        version: str = "1",
        inputs: dict[str, Ref] | None = None,
        outputs: dict[str, JsonSchema] | None = None,
        config: Context | None = None,
        config_schema: JsonSchema | None = None,
        dependencies: list[NodeRef] | None = None,
        input_ports: list[InputPort] | None = None,
        aggregate_inputs: list[str] | None = None,
        resource_estimate: ResourceVector | None = None,
    ) -> NodeRef:
        bindings = dict(inputs or {})
        if kind in ("EVALUATE", "AGGREGATE"):
            if "subject" in bindings or "criterion" in bindings:
                raise ValueError(
                    "Builder binds definition subject and criterion; "
                    "use raw VCP for explicit declarations"
                )
            bindings.update(
                subject=constant(to_data(self.subject), {"type": "object"}),
                criterion=constant(to_data(self.criterion), {"type": "object"}),
            )
        ports = {p.name: p for p in input_ports or []}
        for name, ref in bindings.items():
            if name not in ports:
                ports[name] = InputPort(
                    name=name, schema=deepcopy(ref.schema), required=True, on_unavailable="BLOCK"
                )
        declared = [
            OutputPort(name=name, schema=deepcopy(schema), role="INFORMATION")
            for name, schema in (outputs or {}).items()
        ]
        if kind in ("EVALUATE", "AGGREGATE", "CONTROL"):
            role = "DECISION" if kind == "CONTROL" else "RESULT"
            declared.append(OutputPort(name=role.lower(), schema={"type": "object"}, role=role))
        self._nodes.append(
            Node(
                id=id,
                kind=kind,
                operation=OperationRequirement(
                    capability_id=capability, capability_version=version
                ),
                inputs=list(ports.values()),
                outputs=declared,
                bindings={n: deepcopy(r.source) for n, r in bindings.items()},
                aggregate_inputs=aggregate_inputs or [],
                config=deepcopy(config or {}),
                config_schema=deepcopy(config_schema),
                resource_estimate=deepcopy(resource_estimate or {}),
            )
        )
        predecessors = [
            r.source.node_id for r in bindings.values() if isinstance(r.source, UpstreamOutput)
        ]
        predecessors.extend(n.id for n in dependencies or [])
        for predecessor in dict.fromkeys(predecessors):
            self._edges.append(Edge(from_node=predecessor, to_node=id))
        return NodeRef(
            id,
            {
                p.name: Ref(UpstreamOutput(node_id=id, output=p.name), p.value_schema)
                for p in declared
            },
        )

    def derive(self, id: str, capability: str, **kwargs: Unpack[NodeOptions]) -> NodeRef:
        return self.node(id, "DERIVE", capability, **kwargs)

    def evaluate(self, id: str, capability: str, **kwargs: Unpack[NodeOptions]) -> NodeRef:
        return self.node(id, "EVALUATE", capability, **kwargs)

    def control(self, id: str, capability: str, **kwargs: Unpack[NodeOptions]) -> NodeRef:
        return self.node(id, "CONTROL", capability, **kwargs)

    def aggregate(
        self,
        id: str,
        members: dict[str, Ref],
        *,
        reducer: str = "ALL",
        handling: dict[str, str] | None = None,
        config: Context | None = None,
        capability: str = "openverify.aggregate",
        version: str = "1",
    ) -> NodeRef:
        names = list(members)
        if set(names) & {"subject", "criterion", "members"}:
            raise ValueError("Reserved aggregate member name")
        settings: Context = dict(config or {})
        if capability == "openverify.aggregate":
            settings.update(
                reducer=reducer, handling=dict(handling or {k: "REJECT" for k in sorted(HANDLING)})
            )
        return self.node(
            id,
            "AGGREGATE",
            capability,
            version=version,
            inputs={
                **members,
                "members": constant(
                    cast(JsonValue, names), {"type": "array", "items": {"type": "string"}}
                ),
            },
            aggregate_inputs=names,
            config=settings,
        )

    def edge(self, predecessor: NodeRef, successor: NodeRef, *, guard: Guard | None = None) -> None:
        self._edges = [
            e for e in self._edges if (e.from_node, e.to_node) != (predecessor.id, successor.id)
        ]
        self._edges.append(Edge(from_node=predecessor.id, to_node=successor.id, guard=guard))

    def add_node(self, node: Node) -> NodeRef:
        self._nodes.append(deepcopy(node))
        return NodeRef(
            node.id,
            {
                p.name: Ref(UpstreamOutput(node_id=node.id, output=p.name), p.value_schema)
                for p in node.outputs
            },
        )

    def build(self) -> VerificationDefinition:
        definition = VerificationDefinition(
            id=self.id,
            version=self.version,
            subject=self.subject,
            criterion=self.criterion,
            judgment_schema=self.judgment_schema,
            run_inputs=self._inputs,
            graph=VCPGraph(nodes=self._nodes, edges=self._edges),
            execution_policy=self.execution_policy,
        )
        return parse_definition(serialize(definition))

    def validate(self) -> None:
        self.build()

    def inspect(self) -> Context:
        return inspect_definition(self.build())

    def to_json(self) -> str:
        return serialize(self.build())
