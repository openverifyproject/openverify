# Hosts, agents, services, and infrastructure

Every host uses the same API. Relay does not hardcode any agent or trigger.
Shell-capable agents call `openverify run`; Python harnesses await `Relay.run`;
MCP clients call run_graph. Your host registers after-edit, before-action,
after-output, pre-completion, CI, or manual hooks and delivers feedback itself.
MCP availability does not automatically trigger verification after edits.

```sh
python examples/custom-graph/run.py
python examples/application-integration/run.py
python examples/multi-agent/run.py
python examples/guardrail/run.py
```

`Relay.verify_before(action, graph, inputs=..., gate_policy=passing_gate)` owns the
action call and waits. The action must be a zero-argument async callable. The
default gate requires at least one Result and successful, applicable, known binary
PASS on **every** recorded Result. It rejects FAIL, UNKNOWN, ERROR, SKIPPED,
DEFERRED, CANCELLED, NOT_APPLICABLE and score-only outcomes. Providers/configuration
errors propagate before the action. Supply an explicit gate policy to select a
particular aggregate or authorize different handling. Relay only mediates actions
actually passed to this helper; it cannot prevent unrelated host actions. The
included guardrail example records a denied protected-path action and a permitted
temporary-path action without deleting any real files.

The application example validates an already-produced inventory object, with no
coding/LLM assumptions. Inputs are arbitrary declared JSON types. Large/binary
artifacts should use explicit ArtifactRefs and separately configured retrieval
providers; references are never automatically dereferenced.

MCP installation and default server:

```sh
python -m pip install '.[mcp]'
openverify mcp
```

Configure your agent's MCP client with command `openverify`, args `["mcp"]`.
The official SDK serves tools `list_graphs`, `describe_graph(name)`,
`run_graph(name, inputs)`, `inspect_result(run_id)`. The default allowlist contains
text and guardrail only. There is no tool for Python execution, executable
configuration, or loading an arbitrary graph path. Responses contain structured
RunRecords, not file/line-only feedback. Results are retained in process memory
until shutdown; they are not durable recovery state.

To authorize other graphs, create a trusted Python entrypoint:

```python
from openverify import Relay
from openverify.relay.entrypoints.mcp import create_server
from openverify.relay.entrypoints.service import GraphService
from openverify.relay.templates import text_graph

service = GraphService(Relay(), {"review-document": text_graph()})
create_server(service).run(transport="stdio")
```

Services limit active runs to eight by default (`max_concurrent_runs` on
GraphService). Each run has its own bounded ready waves. A shared Python provider
serializes unless its host explicitly declares concurrency safety. No mutable
run-state dictionary is shared among runs. Recorded token cancellation affects
only its occurrence; task cancellation does not signal other runs.

Optional HTTP adapter:

```sh
python -m pip install '.[http]'
openverify http --port 8765
```

It binds to `127.0.0.1`. GET /health reports health. POST /verify accepts exactly
`{"graph":"text","inputs":{"text":"Migration Rollback"}}`. This returns the
same complete VCP RunRecord. Use curl on Linux/macOS:

```sh
curl -H 'Content-Type: application/json' -d '{"graph":"text","inputs":{"text":"Migration Rollback"}}' http://127.0.0.1:8765/verify
```

PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8765/verify -ContentType 'application/json' -Body '{"graph":"text","inputs":{"text":"Migration Rollback"}}'
```

`create_app(service, token="host-secret")` enforces an Authorization Bearer token;
the host supplies and protects it. Request bodies are bounded to 1 MiB. A valid
FAIL is an HTTP 200 RunRecord; malformed/unauthorized graph/input requests are
400, bad token 401, oversized body 413. Public deployment, tenant authorization,
TLS and rate limiting belong to a properly configured host, not this localhost
adapter. No arbitrary command execution endpoint is exposed.

Replace infrastructure without changing core:

```python
from pathlib import Path
from openverify import Relay
from openverify.relay import RuntimeConfig
from openverify.relay.adapters.binder import DeterministicBinder
from openverify.relay.adapters.local import LocalDriver
from openverify.relay.adapters.jsonl import JsonlStore
from openverify.relay.adapters.logging import CallbackObserver

relay = Relay(
    binder=DeterministicBinder(),
    driver=LocalDriver(),
    store=JsonlStore(Path("runs.jsonl")),
    observer=CallbackObserver(lambda event: print(event.kind)),
    config=RuntimeConfig(max_concurrency=4, timeout=60),
)
```

Each constructor argument accepts its narrow port Protocol. Small independent
replacement examples for Binder, Driver, Store and Observer are executable in
`tests/relay/test_ports.py`. An observer receives run/node lifecycle events and
validated provider events. Diagnostic/progress events are not semantic evidence.
Default logging records identity metadata, not input/config payloads. Observer
failures appear in the run annotation; storage failures raise. Memory/JSONL stores
snapshot records on both write and retrieval.

For an external provider plus usable exported CLI config:

```sh
python examples/stdio-provider/run.py --export-dir .pytest_cache/stdio-example
openverify run .pytest_cache/stdio-example/graph.json --inputs .pytest_cache/stdio-example/inputs.json --providers .pytest_cache/stdio-example/providers.json --json
```

This deliberately produces FAIL/exit 1 for prohibited TBD. Exported argv/cwd are
absolute paths for your machine. Keep provider config under trusted host control.
