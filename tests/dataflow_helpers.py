"""Explicit typed graphs reused by correctness and property regressions."""

from openverify.adapters import Registry
from openverify.adapters.demo import known
from openverify.model import (
    Context,
    Edge,
    ExecutionError,
    ExecutionObservation,
    Graph,
    InputPort,
    JsonSchema,
    Node,
    OperationRequirement,
    OutputPort,
    RunInput,
    UpstreamOutput,
    VerificationDefinition,
)
from tests.helpers import definition, node


def input_port(name: str, schema: JsonSchema = True, *, required: bool = True) -> InputPort:
    return InputPort(
        name=name, schema=schema, required=required, on_unavailable="BLOCK" if required else "OMIT"
    )


def derive(id: str, *, source: str = "x", schema: JsonSchema = True) -> Node:
    return Node(
        id=id,
        kind="DERIVE",
        operation=OperationRequirement(capability_id="com.example.echo", capability_version="1"),
        inputs=[input_port("x", schema)],
        outputs=[OutputPort(name="x", schema=schema, role="INFORMATION")],
        bindings={"x": RunInput(name=source)},
    )


def flow(schema: JsonSchema = True) -> VerificationDefinition:
    consumer = node(id="consumer", kind="EVALUATE", executor_ref="echo.judge")
    consumer.inputs.append(input_port("x", schema))
    consumer.bindings["x"] = UpstreamOutput(node_id="producer", output="x")
    return definition("generic").model_copy(
        update={
            "run_inputs": [input_port("x", schema)],
            "graph": Graph(
                nodes=[derive("producer", schema=schema), consumer],
                edges=[Edge(from_node="producer", to_node="consumer")],
            ),
        }
    )


class Echo:
    def execute(self, inputs: Context, config: Context) -> Context:
        return {"x": inputs["x"]}


class Judge:
    def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
        return ExecutionObservation(
            outputs={
                "result": known("PASS")
                .model_copy(update={"output": {"observed": inputs["x"]}})
                .model_dump(mode="json", exclude_none=True)
            }
        )


class Failure:
    def execute(self, inputs: Context, config: Context) -> ExecutionObservation:
        return ExecutionObservation(
            error=ExecutionError(code="com.example.failed", message="Unavailable")
        )


def registry() -> Registry:
    result = Registry()
    result.register("com.example.echo", "1", Echo())
    result.register("com.example.echo.judge", "1", Judge())
    return result
