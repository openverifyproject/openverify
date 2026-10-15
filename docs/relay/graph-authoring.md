# Author portable graphs

The builder compiles to the existing VerificationDefinition model. Raw VCP JSON
uses exactly the same validation/execution path. Run:

```sh
python examples/custom-graph/run.py
python tools/build_relay_examples.py
openverify validate examples/first-run/definition.json
```

`Graph(id, version=..., subject=ArtifactRef(...), criterion=Criterion(...),
judgment_schema=..., execution_policy=...)` defines meaning and policy. Defaults
materialize a declared-input subject and a criterion tied to that graph ID. For
shared/deployed graphs, supply domain-appropriate subject and criterion metadata.
Evaluate/Aggregate nodes explicitly receive constant-bound subject and criterion
snapshots in the exported VCP. They never receive hidden semantic inputs.

`graph.input(name, schema)` returns a typed Ref. Optional inputs use
`required=False`; an explicit SDK `Constant(value=...)` enables DEFAULT (including
null). Otherwise optional inputs OMIT. Schema `default` annotations insert nothing.
`constant(value, schema)` and `external(ArtifactRef(...))` create other source refs.
External refs pass their exact reference object; Relay does not fetch content.

`derive`, `evaluate`, and `control` accept a node ID, capability ID and keyword
arguments matching `node`: `version`, `inputs` mapping names to Refs, information
`outputs` mapping names to schemas, `config`, `config_schema`, `dependencies`,
`input_ports`, and `resource_estimate`. Capability versions are exact opaque
strings. Estimates do not silently become enforceable budgets. `input_ports`
exposes required/OMIT/DEFAULT behavior for advanced node declarations.

NodeRef supports `node["information_port"]`, `.result`, and `.decision`.
Upstream bindings automatically add prerequisite edges; the builder materializes
them in VCP. `dependencies=[node]` adds execution-only ordering. Neither kind of
edge carries implicit data. Unrelated branch outputs are never injected.

`graph.edge(a, b, guard=Guard(source=ref.source, pointer="/verdict", value="PASS"))`
sets an equality guard on that edge. All incoming prerequisites/guards apply.
Routes are Decisions naming a direct successor, with shared joins retained.
`add_node(SDKNode(...))` supports complete explicit VCP ports/metadata; `edge`
connects those nodes. Invalid source identities, duplicate nodes/ports, cycles,
expansion, unsupported required extensions, and external schema references reject.

`aggregate(id, {"stable_name": upstream.result, ...}, reducer="ALL", handling=...,
config=...)` materializes ordered aggregate_inputs and the constant members input.
The builder's simple default is an **explicit serialized** REJECT for every
exceptional category. Override each category with REJECT or IGNORE in `handling`:
UNKNOWN, ERROR, SKIP, DEFERRED, CANCELLED, NOT_APPLICABLE, MISSING. Ignoring all
members and majority ties are errors, never automatic PASS.

All standard reducers are supported: ALL, ANY, MAJORITY, MIN_SCORE, MAX_SCORE,
AVERAGE, WEIGHTED_AVERAGE and WORST_SEVERITY. Weighted config uses
`{"weights":{"stable_name":2.0,...}}`, exactly matching member identities.
Severity config supplies an explicit domain with distinct label/rank levels.
Numeric/severity reducers do not invent binary verdicts. Evidence concatenates in
membership order. `capability="com.example.custom_aggregate"` selects a custom
provider and passes the same explicit members and semantic inputs.

`graph.build()` snapshots and validates. `validate()`, `inspect()`, and
deterministically sorted `to_json()` are available. Save JSON with
`Path("graph.json").write_text(graph.to_json(), encoding="utf-8")` and load through
`parse_definition(Path("graph.json").read_bytes())`. There is no mandatory YAML
dependency or separate graph language.

Custom execution policies are SDK Capability/AdmissionPolicy values with an
OperationRequirement, explicit ports/bindings/config, passed in ExecutionPolicy.
Only constants, run inputs and external refs are legal before graph execution.
Their providers return Activation, Selection or Admission objects directly.
Selection is empty or the exact definition subject. No hidden history, clock,
budget, environment or current graph outputs are passed to a policy.

To replace a deterministic text evaluator with a semantic checker, change that
node's capability requirement and explicitly register/bind a provider with the
same declared ports or update the ports accordingly. Relay source does not change.
For factual verification, author these actual dependencies and bindings:

```text
text -> configured claim extractor -> claims
reference identities -> configured retrieval provider -> evidence
claims + evidence -> configured support/contradiction evaluator -> Results
Results -> explicit aggregation/control
```

The extractor, retriever and evaluator must actually be installed/configured.
No factual checker ships in v0.1. Insufficient evidence must produce an executed,
successful, applicable UNKNOWN Result without a verdict/judgment. Regex/literal
providers establish deterministic text properties only.
