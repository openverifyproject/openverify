# Relay architecture and contracts

Relay is a new asyncio implementation built directly on the written VCP and
Provider Contract. It imports no Reference Engine module, registry, adapters,
dispatcher, scheduler, or reducer implementation. The old implementation remains
available under its existing Python API. No VCP schema or core wire object changed.

```text
openverify/
  authoring/                 Graph, NodeRef, Ref -> portable VCP
  relay/
    api.py                   Relay, Run, passing_gate; default composition
    config.py                trusted RuntimeConfig
    core/                    state transitions, ready waves, reducers
    ports/                   six Protocols and typed request/report values
    application/             preparation, binding, policies, execution, records
    adapters/                catalog, binder, driver, transports, stores, observers
    entrypoints/             CLI, named GraphService, MCP, HTTP
    providers.py             async Python provider decorator
    templates.py             ordinary VCP graph builders
  standard/                  filesystem, Git, scopes, tools, text, structured data
```

The pure core depends on SDK types/rules. Application modules depend on core,
ports, and SDKs; they never import infrastructure or standard providers. Adapters
implement ports. Entrypoints and the public facade perform composition. Authoring
depends only on VCP SDK APIs. AST architecture tests enforce these directions,
check module initialization cycles, reject Engine imports and mutable global run
containers. No ambient Context is passed to computations.

The small public surface is `from openverify import Relay, Graph`. `Relay.run`
accepts a Graph, VerificationDefinition, or serialized VCP JSON and explicit typed
inputs. It returns `Run(record)` with `results`, `decisions`, `evidence`, `usage`,
and `to_json()`. `results` is the complete per-node final-result mapping, including
ERROR/nonexecution bookkeeping. `evidence` includes observation and Result
snapshots; repeated evidence is not an additional measurement. `usage` remains
per-node and preserves units; it is never blindly summed. `record` is an SDK
RunRecord. `RelayError`/`ProtocolError` expose stable `code`, `message`, and details.

| Port | Methods | Default |
| --- | --- | --- |
| ProviderCatalog | `providers()` | Catalog: explicit registration, trusted stdio config, opt-in package entry points |
| ProviderBinder | `bind(requirement, providers, explicit)` | DeterministicBinder: explicit exact identity, unique compatible match, else error |
| ExecutionDriver | `execute(provider, request, timeout, emit)` | LocalDriver: bounded asyncio invocation, SDK lifecycle validation |
| ProviderTransport | `invoke(request, emit)` | InProcessTransport or isolated StdioTransport session |
| RecordStore | `put(record)`, `get(run_id)` | MemoryStore; optional JsonlStore |
| EventObserver | `observe(event)` | LoggingObserver; optional CallbackObserver |

These are narrow typing.Protocol interfaces with SDK values and small dataclasses,
defined in `relay.ports`. Hosts inject replacements into Relay's constructor. The
application revalidates driver reports; replacing physical execution does not
remove Provider Contract validation. Binder choices are independently checked
against the trusted catalog and exact manifest/capability identities.

Preparation snapshots/validates the definition, entire input contract and supplied
JSON. Binding resolves graph and policy requirements before policy execution.
Activation and selection can raise NO_OCCURRENCE without creating a record.
Admission RUN/SKIP/DEFER creates an occurrence. Built-ins MANUAL/EXPLICIT,
ALWAYS/PROBABILITY and custom provider-backed policies are supported. Probability
uses a local deterministic SHA256 bucket with definition fingerprint, subject,
opportunity identity and p. It has no portable bucket-compatibility promise.
Omitting opportunity_id generates a fresh UUID; supply one for repeatable sampling.

The state machine advances PENDING -> READY -> RUNNING -> TERMINAL, or records
explicit nonexecution. Ready non-Control nodes run in bounded waves. Whole waves
settle before successors start. Records are accepted in deterministic definition
order within each wave, irrespective of completion order. Control nodes are serial
barriers: STOP, ROUTE, RETRY and DEFER cannot race with active independent work.
All incoming prerequisites, equality guards, routing exclusions, availability,
input defaults and nonexecution precedence come from the existing SDK.

Recorded cancellation tokens serialize that occurrence, because current VCP
provenance represents one interrupted attempt. Task cancellation cleans up active
processes and raises CancelledError; it returns no fabricated completed record.
Other concurrently executing runs keep their own states and inputs. Shared Python
providers serialize by default; hosts explicitly opt into `concurrency_safe=True`.

Every invocation crosses manifest, exact capability/version, input/config schema,
Provider lifecycle/correlation, output schema, VCP port, Result/Decision and
judgment-schema acceptance. Accepted information is published atomically. Rejected
outputs retain raw observations and valid incurred usage. Partial resource events
are snapshots; final usage supersedes them. Runner timing uses wall_time in seconds,
or relay_wall_time when a provider already reports wall_time in another unit.

Before storage/return, every RunRecord is parsed through `parse_run_record`.
`urn:openverify:relay` is an optional annotation retaining invocation IDs, provider
identities, events, raw terminal outcomes and observer diagnostics. It adds no VCP
meaning or authentication. Graph-node ProviderBinding remains normative. Observer
exceptions are isolated and recorded; store failures propagate to the host.

Relay depends on the `verifyanything` wheel plus Pydantic and jsonschema. The
product wheel depends on the Relay, code, and English wheels. Optional extras install
the official MCP SDK; Starlette/Uvicorn; or Ruff, pytest and ast-grep-cli. The
standard library uses stdlib asyncio/subprocess and the installed Git CLI. It does
not implement a replacement parser, linter, test runner, prover, or HTTP server.
