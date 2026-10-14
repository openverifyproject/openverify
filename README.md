# Openverify

A domain-neutral protocol for defining verification, composing arbitrary verification
mechanisms, normalizing results and evidence, deciding when verification runs, and
preserving provenance across runs.

**Protocol status: DRAFT. Implementation: 0.1.0.** JSON is the only implemented
normative wire format. The package name is not part of protocol meaning.

## Why it exists

Different domains already have excellent specialized mechanisms: regex, scripts,
policy engines, test frameworks, theorem provers, model judges, humans, APIs, and
sensors. Their inputs, judgments, exceptional states, policies, and histories often
have incompatible representations. This project gives them a common verification
model. It does not replace them.

```text
                 SUBJECT / WORLD
                       |
                       v
              verification definition
                       |
                       v
        +--------------+--------------+
        |              |              |
        v              v              v
      tool           model          human
        |              |              |
        +--------------+--------------+
                       |
                       v
                normalized result
                       |
                       v
             aggregate / control
                       |
                       v
             provenance / history
```

Implementation mechanisms are replaceable; verification meaning stays stable
across those mechanisms when they implement the same specification. This draft's
meaning remains under review; it has no stable 1.0 compatibility promise.

## Project boundary

The protocol covers meaning, information/evidence, verification computation,
composition, execution policy, resource accounting, results/decisions, and provenance.
It observes, derives, judges, and controls **verification execution**.

Arbitrary external business actions, distributed workers, durable orchestration,
cloud scheduling, databases, dashboards, and model providers are outside it.
The protocol can express `ROUTE("human-review")`, `STOP_FAILURE`, or `CONTINUE`.
These do not themselves refund money, deploy software, stop a factory, or publish
a document. The host owns those actions and the underlying mechanisms.

## The complete mental model

```text
    +----------------------------------------------------------+
    | MEANING                                                  |
    | Subject + Criterion                                      |
    +-----------------------------+----------------------------+
                                  |
                                  v
    +----------------------------------------------------------+
    | KNOWLEDGE                                                |
    | Context + Artifacts + Evidence                           |
    +-----------------------------+----------------------------+
                                  |
                                  v
    +----------------------------------------------------------+
    | COMPUTATION                                              |
    |                                                          |
    |   DERIVE             EVALUATE             CONTROL        |
    | information          judgment             decision       |
    |                         |                                |
    |                     Aggregate                            |
    |                 (special Evaluate)                       |
    +-----------------------------+----------------------------+
                                  |
                                  v
    +----------------------------------------------------------+
    | COMPOSITION                                              |
    | nodes + edges + guards + cycles + dynamic expansion       |
    +-----------------------------+----------------------------+
                                  |
              +-------------------+-------------------+
              |                   |                   |
              v                   v                   v
         ACTIVATION           SELECTION           ADMISSION
          Trigger              Scope              Run Policy
              \                   |                   /
               +------------------+------------------+
                                  |
                                  v
                         RESOURCE MODEL
                       Estimate + Actual
                                  |
                                  v
                        RESULT / DECISION
                                  |
                                  v
                      HISTORY / PROVENANCE
```

**Meaning:** Subject identifies what is examined; Criterion identifies the property
to establish. A definition includes id/version, subject reference, criterion metadata,
judgment schema, graph, and execution policy. Every evaluator explicitly binds the definition subject and criterion; trusted implementations must honor these semantic inputs. There is no criterion expression language.

**Knowledge:** Typed run inputs, constants, explicit external references and upstream outputs supply semantic information. Context is optional ambient nonsemantic metadata. ArtifactRef identifies
content without requiring its bytes or automatically fetching it. Evidence records
messages, references, opaque locators, or structured observations. A locator can
address prose, image regions, sensor events, or database rows; fundamental Evidence
fields do not encode file paths or line numbers.

**Computation:** Derive produces information, Evaluate produces judgment, and Control
produces a verification decision. Regex, model, human, API, and theorem prover are
adapter implementation choices. Aggregate combines Results into a Result and is a
specialized Evaluate.

**Composition:** A general directed graph relates operations. Dependency gives sequence;
independent nodes permit parallelism; guards give conditions; convergence gives joins;
cycles give iteration; expansion gives ForEach. The implemented subset is acyclic
graphs with equality guards and all incoming prerequisites. Cycles and expansion
are recognized as unsupported draft features. Independent nodes execute sequentially
in definition order when ready in the reference engine.

**Activation:** Trigger asks whether an event makes verification eligible. Trigger
capabilities are extensible. The engine implements MANUAL host invocation and
registered custom policy operations with explicit typed inputs. It has no periodic
scheduler.

**Selection:** Scope asks which subjects from a candidate universe are included.
This remains distinct from criterion. EXPLICIT selects the definition's single
subject; custom policies select that exact subject or an empty set using explicit
typed inputs. General subject-universe execution is not implemented.

**Admission:** Run policy asks whether an eligible selected opportunity should spend
resources now: RUN, SKIP, or DEFER. Percentage sampling belongs here. Custom typed
policies and ALWAYS/PROBABILITY are implemented. Probability requires `0 <= p <= 1` and a host-supplied
opportunity id. Reference sampling is deterministic for the same definition
fingerprint, subject, and opportunity; its bucket identity is not portable.
Maximum staleness and its interaction with sampling/history remain OPEN.

**Resources:** An open dimension-to-measurement mapping records unit, kind, and value
or range. Estimate precedes execution; actual usage follows it. Dimensions include
wall time, currency, tokens, reviewer time, bytes, energy, or custom quantities.
The engine preserves adapter usage and separately measures node wall time.
Scheduler labels such as FAST or DEEP are not the resource model.

**Result / Decision:** Result separates disposition, execution outcome, applicability,
determination, judgment, verdict, score, severity, evidence, output, and usage.
An API error, uncertainty, and a skipped check mean different things.
PASS/FAIL/UNKNOWN/ERROR/SKIP is a **partial convenience projection**, not the full
state model. Deferred, cancelled, not-applicable, and known nonbinary judgments
have no invented flattened mapping. Severity belongs to an ordered profile/domain.
Decision controls execution and is distinct from judgment. A human is an evaluator,
not a special Result type.

**History / Provenance:** RunRecord retains the definition snapshot and identity,
subject, initial run inputs, exact per-port resolutions and source identities,
executor references and versions when known, upstream Results, observed/accepted
outputs, evidence, usage, ordered policy evaluations, lifecycle reason codes,
cancellation events, and timing. Validation detects inconsistent snapshots along
declared dataflow edges without rerunning implementations. Lineage
does not prescribe a backend. The engine returns JSON-serializable records; memory
and local JSONL stores are supplied. Cache equivalence, coverage/backfill scheduling,
clock trust, and full replay are not implemented.

## Logical exhaustiveness within the boundary

The claim is a boundary argument with an explicit way to disprove it:

| Every verification concern asks | Category |
| --- | --- |
| What are we trying to establish? | Meaning |
| What information is available? | Knowledge |
| What operation is performed? | Computation |
| How are operations related in time? | Composition |
| What event makes this eligible? | Activation |
| Which subjects are included? | Selection |
| Should an eligible check run now? | Admission |
| What resources are required or consumed? | Resource model |
| What happened? | Result / Decision |
| How does it relate across time? | Provenance |

**If a legitimate concern inside the declared verification boundary cannot be
represented by one of these questions, the model is incomplete.** Category coverage
does not prove complete wire syntax or execution support. The
[conceptual audit](spec/draft/conceptual-audit.md) challenges it with writing, AI,
physical measurements, human review, and external services.

Every operation inside the boundary produces INFORMATION, JUDGMENT, or a CONTROL
DECISION, so the three fundamental computation types are exhaustive by output type:

```text
DERIVE     information          -> information
EVALUATE   information/results  -> judgment
CONTROL    explicit bound inputs -> workflow decision

Aggregate: Results[] -> Result
Aggregate is a specialized Evaluate.
```

An operation with multiple output kinds can be decomposed. Enumerating executor
technologies or reducers would not establish exhaustiveness.

## Protocol, SDK, and reference engine

```text
OpenVerify
  +-- VCP                 verification semantics
  +-- Provider Contract   runner/provider interoperability (DRAFT "0.1")
  +-- Python SDK          types + parsing + validation
  +-- Reference Engine    current small reference VCP executor
```

The [Provider Contract](provider-contract/README.md) sits below VCP and lets any
compatible runner invoke independently implemented capabilities. OpenVerify Relay
is the planned minimal provider-driven harness/runtime built on that contract;
Relay does not exist yet. The Engine uses a small local registry of exact capability ID/version implementations, with no discovery or provider transport runtime.

```text
PROTOCOL: prose semantics + normative JSON schemas + conformance fixtures
    |
    v
PYTHON SDK: typed construction, parsing, validation, serialization, inspection
    |
    v
REFERENCE ENGINE: small local demonstration of executable definitions
```

They share one repository, Python package, release, dependency graph, and root
`.venv` today for simplicity. They are distinct conceptual components. Python and
Pydantic implement meaning; they do not define it. Another SDK or replaceable engine
can implement the same subset.

This project is not Temporal, Dagger, or Airflow. Future adapters could execute
definitions over a local process or those runtimes, but no integrations exist here.
The reference engine has no durable recovery, distributed workers, leases, queues,
replay, sandboxing, or exactly-once execution.

OPA or another policy engine could supply an Evaluate, Control, or admission adapter.
The protocol does not replace general-purpose policy languages. Neither an OPA
integration nor a new policy language is implemented.

Continual learning requires no LEARN node: a discovered mistake yields reusable
knowledge; a changed definition gets a new version/fingerprint; history identifies
subjects without that version; selection/admission can choose backfill. The protocol
supplies identity and lineage primitives. Automatically inventing checks or scheduling
backfill belongs to a host and is not implemented.

## What is implemented today

Shipped Draft 2020-12 schemas strictly validate core wire fields; semantic validation
then enforces prose invariants with stable error codes. Unknown optional extension
data is preserved; unsupported required extensions fail clearly. Duplicate JSON keys,
numeric-string coercion, boolean scores, nonfinite values, and unknown core fields
are rejected. Models are frozen at the attribute level; nested containers remain
mutable, so validation and engine snapshots guard interchange boundaries.

Public functions: `parse_definition`, `parse_result`, `parse_run_record`,
`validate_definition` / `validate_executable_definition`, `validate_result`, `load_schema`, `inspect_definition`,
`serialize`, `fingerprint`, and `flattened_status`. Lower-level `parse_object` and
`validate_wire` cover other wire objects. Constructed models are convenient typed
values; validate before interchange. `fingerprint` returns a **reference-only,
non-portable** `local-sha256:` identity, not canonical signing bytes.

Every executable node declares an operation requirement, typed input/output ports,
and explicit bindings. [Typed executable dataflow](spec/draft/dataflow.md) specifies
the four ValueSource variants, availability, subject/criterion binding, provider
boundary, and provenance. Execution dependency != data binding: edges transfer no
values. Providers never guess required portable input.

The engine executes registered Derive/Evaluate/Control and custom Aggregate
implementations and all eight standard reducers, including WEIGHTED_AVERAGE.
Graph reducers declare ordered aggregate_inputs and a constant-bound members input;
weights map stable member names to values. The direct ordered reducer API retains
aligned positional weights. Derive outputs never mutate global Context.
Every reducer invocation requires explicit REJECT/IGNORE handling for exceptional
and missing inputs. Empty retained input and majority ties are rejected; UNKNOWN
is never silently 0.5 or ERROR silently zero. There is no synthesized overall verdict
without an aggregation node. Reference numeric scores/measurements use binary64;
means use exact rational intermediate arithmetic and one final rounding.
Provenance comparisons distinguish JSON booleans from numbers. Admission SKIP requires every node Result to be SKIPPED/ADMISSION_SKIP;
admission DEFER requires DEFERRED/ADMISSION_DEFER. Integral severity ranks such as 1.0
normalize to SDK integers; UTC timestamps accept Z and +00:00.

Equality guards use explicit typed sources and JSON Pointers, including Result/Decision ports, run inputs and information outputs. ROUTE
checks a graph destination and selects through explicit guards. Stops record remaining nodes as SKIPPED/CONTROL_STOP. RETRY records
SKIPPED/RETRY_REQUESTED; control DEFER records DEFERRED/CONTROL_DEFER without
scheduling another occurrence. Adapter failures become ERROR Results; downstream behavior follows explicit
edges, guards, and reducer policies.

Definitions are **data**: no eval, expressions, arbitrary imports, or automatic artifact
fetching. Hosts explicitly register trusted capabilities. Demo adapters are trusted
host code, not a security sandbox. CLI `run` uses only the local demo registry.

[Open questions](spec/draft/open-questions.md) document portable canonical hashing
and numeric precision, general guards, cycles/expansion, remaining status projections,
partial UNKNOWN judgments, formal criteria/satisfaction mapping execution, richer
reducer policies, capability negotiation, portable sampling identity, maximum staleness,
retry/defer scheduling, cache equivalence, and external artifact integrity. External judgment/port schema references are rejected before execution; richer schema resolution is unsupported. Future authoring syntaxes could compile to JSON; YAML
has no implemented semantics.

## Quickstart

With uv and Python 3.13, run from the root:

```sh
uv sync
uv run openverify validate examples/prose/definition.json
uv run openverify inspect examples/prose/definition.json
uv run openverify run examples/prose/definition.json --run-inputs examples/prose/context.json --opportunity-id article-draft-1 --output run.json
```

The prose graph derives length, checks a banned phrase and length, then aggregates
ALL. The supplied input produces PASS. The same SDK works locally:

```python
from pathlib import Path

from openverify import parse_definition, parse_result, parse_run_record, serialize
from openverify.adapters.demo import demo_registry
from openverify.engine import Engine

definition = parse_definition(Path("examples/prose/definition.json").read_bytes())
record = Engine(demo_registry()).run(
    definition,
    {"text": "Careful claims help readers."},
    opportunity_id="article-draft-1",
)
result = record.final_results["all"]
assert result.verdict == "PASS"
assert parse_result(serialize(result)) == result
assert parse_run_record(serialize(record)) == record
Path("run.json").write_text(serialize(record), encoding="utf-8")
```

See [examples](examples/README.md) for a temperature measurement and mock AI judges
with UNKNOWN-to-human routing. No model provider is required. Validation accepts
`--type result` and `--type run-record`; invalid input prints a stable error object
and exits 1. A completed `run` exits 0 even when its record contains ERROR/FAIL;
callers inspect the Results.

## Development

Exactly one root environment serves SDK and engine. All normal commands run here:

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

The lock file is tracked. Pyright checks source and tests in strict mode. Tests cover
portable fixtures, Result state combinations, reducers, graphs, routing, sampling,
resources, provenance, extensions, and Hypothesis searches over scores, JSON,
resource maps, and DAGs. Test temporary files live in the ignored root pytest cache.

```text
spec/draft/                 meaning + open questions + conceptual audit
schemas/draft/              normative JSON wire schemas
profiles/standard-draft/    validated common choices, not a core ontology
conformance/               manifest + valid/invalid fixtures + expected outcomes
src/openverify/             SDK, adapter contracts, local engine, provenance stores
examples/                  prose, numerical, mock AI output examples
tests/                     unit, conformance, property, integration
tools/                     deterministic artifact maintenance scripts
```

Schema/profile copies are packaged for offline SDK use and tested against the
normative root files. Edit their maintainers and regenerate in order with
`uv run python tools/<file>`: `build_schemas.py`, `build_fixtures.py`,
`build_profile.py`, `build_dataflow_fixtures.py`, `build_examples.py`. Maintenance scripts are not package code.
See [CONTRIBUTING](CONTRIBUTING.md) for the protocol-change and open-question process.


## Breaking DRAFT dataflow revision

Definitions and RunRecords from earlier revisions require reauthoring. Node
executor_ref/shared Context injection and implicit predecessor reducer membership
are removed. CLI run uses --run-inputs. Registry.register binds exact capability
ID/version pairs; implementations execute(inputs, config) with fresh JSON objects.
All kinds can return ExecutionObservation(outputs, usage, evidence, error). Local
conveniences returning Result, Decision or information mappings normalize into that
channel. Valid reported usage survives invalid judgments and information outputs.
Engine.run accepts optional ambient context= metadata separately from run inputs.
Custom activation/selection/admission operations use the same exact-pair registry,
with typed ports/bindings and constrained outcomes. Engine.attempt returns None
for DO_NOT_ACTIVATE or empty selection; Engine.run raises NO_OCCURRENCE instead.
Valid RUN/SKIP/DEFER admission creates a RunRecord with all three policy evaluations.
See [execution policy](spec/draft/execution-policy.md) and
[lifecycle](spec/draft/lifecycle.md) for reason codes, routing and cooperative
Cancellation tokens. This is a breaking DRAFT provenance revision.
No Relay, provider discovery, cycles, iteration or dynamic expansion is implemented.
