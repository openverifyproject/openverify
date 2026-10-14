"""Typed SDK values implementing the draft; these do not define protocol meaning."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator


class Value(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", allow_inf_nan=False)


class Extension(Value):
    namespace: str
    version: str
    required: bool
    data: JsonValue


class AnnotatedValue(Value):
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    extensions: list[Extension] = Field(default_factory=lambda: list[Extension]())


class ArtifactRef(AnnotatedValue):
    id: str
    type: str
    locator: JsonValue
    schema_id: str | None = None


class Evidence(AnnotatedValue):
    id: str | None = None
    message: str | None = None
    artifact_ref: ArtifactRef | None = None
    locator: JsonValue = None
    structured_data: JsonValue = None


class Measurement(Value):
    unit: str
    kind: Literal["EXACT", "ESTIMATED", "RANGE", "UNKNOWN"]
    value: float | None = None
    minimum: float | None = None
    maximum: float | None = None


type ResourceVector = dict[str, Measurement]
type Context = dict[str, JsonValue]


class ResourceDimension(AnnotatedValue):
    id: str
    unit: str
    description: str


class Severity(Value):
    domain: str
    label: str


class SeverityLevel(Value):
    label: str
    rank: int

    @field_validator("rank", mode="before")
    @classmethod
    def integral_rank(cls, value: object) -> object:
        """Admit JSON Schema integers without loosening bool/string validation."""
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value


class SeverityDomain(Value):
    id: str
    levels: list[SeverityLevel]


class Result(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    disposition: Literal["EXECUTED", "SKIPPED", "DEFERRED", "CANCELLED"]
    execution_outcome: Literal["SUCCESS", "ERROR"] | None = None
    applicability: Literal["APPLICABLE", "NOT_APPLICABLE"] | None = None
    determination: Literal["KNOWN", "UNKNOWN"] | None = None
    judgment: JsonValue = None
    verdict: Literal["PASS", "FAIL"] | None = None
    score: float | None = None
    severity: Severity | None = None
    evidence: list[Evidence] = Field(default_factory=lambda: list[Evidence]())
    output: JsonValue = None
    usage: ResourceVector = Field(default_factory=dict)


class Decision(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    kind: Literal["CONTINUE", "STOP_SUCCESS", "STOP_FAILURE", "ROUTE", "RETRY", "DEFER"]
    destination: str | None = None
    reason: str | None = None


type JsonSchema = dict[str, JsonValue] | bool


class Constant(Value):
    kind: Literal["CONSTANT"] = "CONSTANT"
    value: JsonValue


class RunInput(Value):
    kind: Literal["RUN_INPUT"] = "RUN_INPUT"
    name: str


class ExternalReference(Value):
    kind: Literal["EXTERNAL_REFERENCE"] = "EXTERNAL_REFERENCE"
    reference: ArtifactRef


class UpstreamOutput(Value):
    kind: Literal["UPSTREAM_OUTPUT"] = "UPSTREAM_OUTPUT"
    node_id: str
    output: str


type ValueSource = Annotated[
    Constant | RunInput | ExternalReference | UpstreamOutput, Field(discriminator="kind")
]


class InputPort(Value):
    name: str
    value_schema: JsonSchema = Field(alias="schema")
    required: bool
    on_unavailable: Literal["BLOCK", "OMIT", "DEFAULT"]
    default: Constant | None = None


class OutputPort(Value):
    name: str
    value_schema: JsonSchema = Field(alias="schema")
    role: Literal["INFORMATION", "RESULT", "DECISION"]


class OperationRequirement(Value):
    capability_id: str
    capability_version: str


class Guard(Value):
    source: ValueSource
    pointer: str
    value: JsonValue


class Edge(Value):
    from_node: str
    to_node: str
    guard: Guard | None = None


class Node(AnnotatedValue):
    id: str
    kind: Literal["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"]
    operation: OperationRequirement
    inputs: list[InputPort] = Field(default_factory=lambda: list[InputPort]())
    outputs: list[OutputPort] = Field(default_factory=lambda: list[OutputPort]())
    bindings: dict[str, ValueSource] = Field(default_factory=dict)
    aggregate_inputs: list[str] = Field(default_factory=list)
    config: Context = Field(default_factory=dict)
    config_schema: JsonSchema | None = None
    resource_estimate: ResourceVector = Field(default_factory=dict)


class Graph(Value):
    nodes: list[Node]
    edges: list[Edge] = Field(default_factory=lambda: list[Edge]())
    features: list[Literal["CYCLES", "DYNAMIC_EXPANSION"]] = Field(
        default_factory=lambda: list[Literal["CYCLES", "DYNAMIC_EXPANSION"]]()
    )


class Criterion(AnnotatedValue):
    id: str
    description: str


class PolicyOperation(Value):
    operation: OperationRequirement | None = None
    config: Context = Field(default_factory=dict)
    config_schema: JsonSchema | None = None
    inputs: list[InputPort] = Field(default_factory=lambda: list[InputPort]())
    bindings: dict[str, ValueSource] = Field(default_factory=dict)


class Capability(PolicyOperation):
    executor_ref: str | None = None


class AdmissionPolicy(PolicyOperation):
    strategy: str | None = None
    probability: float | None = None


class ExecutionPolicy(Value):
    activation: Capability
    selection: Capability
    admission: AdmissionPolicy


class VerificationDefinition(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    id: str
    version: str
    subject: ArtifactRef
    criterion: Criterion
    judgment_schema: JsonSchema
    run_inputs: list[InputPort] = Field(default_factory=lambda: list[InputPort]())
    satisfaction_mapping: Context | None = None
    graph: Graph
    execution_policy: ExecutionPolicy


class Admission(Value):
    outcome: Literal["RUN", "SKIP", "DEFER"]
    reason: str


class Activation(Value):
    outcome: Literal["ACTIVATE", "DO_NOT_ACTIVATE"]
    reason: str


class Selection(Value):
    subjects: list[ArtifactRef]
    reason: str


class ExecutionError(Value):
    code: str
    message: str


class ExecutionObservation(Value):
    outputs: Context = Field(default_factory=dict)
    usage: ResourceVector = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=lambda: list[Evidence]())
    error: ExecutionError | None = None


class InputResolution(Value):
    source: ValueSource | None = None
    status: Literal[
        "AVAILABLE",
        "ABSENT",
        "PRODUCER_NOT_EXECUTED",
        "PRODUCER_ERROR",
        "OUTPUT_MISSING",
        "INVALID",
    ]
    used_default: bool = False
    value: JsonValue = None


class PolicyEvaluation(Value):
    role: Literal["ACTIVATION", "SELECTION", "ADMISSION"]
    input_values: Context
    input_resolutions: dict[str, InputResolution]
    outcome: Activation | Selection | Admission
    executor_ref: str | None = None
    executor_version: str | None = None


class CancellationEvent(Value):
    node_id: str
    phase: Literal["BEFORE_START", "RUNNING"]
    reason: str


class NodeRecord(Value):
    node_id: str
    kind: Literal["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"]
    operation: OperationRequirement
    executor_ref: str | None = None
    executor_version: str | None = None
    upstream_node_ids: list[str]
    input_values: Context
    input_resolutions: dict[str, InputResolution]
    upstream_results: dict[str, Result]
    started_at: str
    finished_at: str
    usage: ResourceVector
    state: Literal["SUCCESS", "ERROR", "NONEXECUTED", "CANCELLED"]
    reason: str | None = None
    observation: ExecutionObservation | None = None
    information: Context = Field(default_factory=dict)
    result: Result | None = None
    decision: Decision | None = None


class RunRecord(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    run_id: str
    definition: VerificationDefinition
    definition_fingerprint: str
    subject: ArtifactRef
    initial_context: Context
    run_inputs: Context
    opportunity_id: str
    admission: Admission
    policy_evaluations: list[PolicyEvaluation]
    cancellation: CancellationEvent | None = None
    started_at: str
    finished_at: str
    nodes: list[NodeRecord]
    final_results: dict[str, Result]


class Profile(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    id: str
    version: str
    flattened_statuses: list[str]
    severity_domain: SeverityDomain
    aggregators: list[str]
    admission_policies: list[str]
    decisions: list[str]
    resource_dimensions: list[ResourceDimension]
