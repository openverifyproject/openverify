"""Typed SDK values implementing the draft; these do not define protocol meaning."""

from typing import Literal

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


class Guard(Value):
    node_id: str
    field: Literal[
        "disposition",
        "execution_outcome",
        "applicability",
        "determination",
        "verdict",
        "decision_kind",
        "decision_destination",
    ]
    value: str


class Edge(Value):
    from_node: str
    to_node: str
    guard: Guard | None = None


class Node(AnnotatedValue):
    id: str
    kind: Literal["DERIVE", "EVALUATE", "CONTROL", "AGGREGATE"]
    executor_ref: str
    config: Context = Field(default_factory=dict)
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


class Capability(Value):
    executor_ref: str
    config: Context = Field(default_factory=dict)


class AdmissionPolicy(Value):
    strategy: str
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
    judgment_schema: Context
    satisfaction_mapping: Context | None = None
    graph: Graph
    execution_policy: ExecutionPolicy


class Admission(Value):
    outcome: Literal["RUN", "SKIP", "DEFER"]
    reason: str


class NodeRecord(Value):
    node_id: str
    executor_ref: str
    executor_version: str | None = None
    upstream_node_ids: list[str]
    input_context: Context
    upstream_results: dict[str, Result]
    started_at: str
    finished_at: str
    usage: ResourceVector
    result: Result | None = None
    decision: Decision | None = None
    derived: Context | None = None


class RunRecord(AnnotatedValue):
    protocol: Literal["draft"] = "draft"
    run_id: str
    definition: VerificationDefinition
    definition_fingerprint: str
    subject: ArtifactRef
    initial_context: Context
    opportunity_id: str
    admission: Admission
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
