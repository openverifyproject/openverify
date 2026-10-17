# Golden v0.3.1

Production target: `5f17f402a270882f244a54dde25eda92a085eb39`. Earlier frozen
releases and production/specification files are unchanged. The stable command
paths delegate to the new adapters in `tests/golden_v031`:

```powershell
python -m pytest -q tests/golden_v03/test_contract_structure.py
python -m pytest -q tests/golden_v03/test_master_execution.py
```

Use the normal Python 3.13 environment. To select the isolated pinned checkout:

```powershell
$env:GOLDEN_IMPLEMENTATION = (Resolve-Path .pytest_cache/golden-v03/production-5f17f402).Path
```

For an enforced 300-second subprocess wall timeout, using the same two commands:

```powershell
python -m tools.golden_v031.run_measured A
python -m tools.golden_v031.run_measured B
```

`--cases ID,ID` runs only explicitly named logical cases. Unknown IDs reject.
Targeting is reported separately from full-suite execution. Automatic JSONLs and
summaries go to `.pytest_cache/golden-v031/timings/`; external launch wall times
and console output go to `.pytest_cache/golden-v031/launches/`. Category/case,
Relay-call, collection/setup/call/teardown and semantic durations are monotonic.
The full suites contain **7,350 structure cases** and **323 runtime scenarios**.
All 55 existing runtime scenarios and their master graph are preserved.

The three Result failures were fixture errors. Absent keys and empty containers
are distinct JSON shapes; both can be valid. No universal wire normalization is
invented. The producer now explicitly authors `evidence=[]` and `usage={}` and
the adapter retains exact consumed-value comparisons, including null and types.

## Availability reconciliation

The recovered historical inventory is explicitly anchored by SHA-256 in
`availability-reconciliation.json`. Every original cell has its own stable ID:

* Four consumer node kinds.
* Five binding categories: CONSTANT, RUN_INPUT, EXTERNAL_REFERENCE,
  UPSTREAM_OUTPUT and UNBOUND. UNBOUND is an absent binding, not a ValueSource.
* Six availability states and three handling modes.

All **360 cells** are classified independently from the specification:
**128 runtime-applicable, 232 inapplicable**. The classifications match the
historical inventory one-to-one. Its **44 missing cells** now have separate
executable witnesses. Aggregate optional handling applies to supplementary
information inputs, never to reducer member ports.

The 108-cell v0.3 model lacked the consumer-kind axis and UNBOUND. It also tested
invalid constant/reference resolution in isolation, although those known values
reject a graph before execution. Those earlier pure checks remain as regressions;
they are not misrepresented as legal runtime graph cells.

Result/Decision are output roles of UPSTREAM_OUTPUT, not new ValueSources. There
are 144 supplementary role cells with **80 executable runtime witnesses** and
64 inapplicable cells. The first independent snapshot accidentally treated
optional Result bindings on Aggregate as supplementary information. The explicit,
separately committed `expectation-errata.json` fixes this from dataflow.md's rule
that ALL Result bindings belong to required BLOCK membership. Four optional-role
cells assert exact structural rejection; two BLOCK witnesses include complete
membership. Initial frozen files remain preserved; `revision.json` and
`coverage-effective.json` are the authoritative effective inventory.

Each applicable cell has a pure resolver test and its own actual Relay run with
exact values, source identity, status/default/value-presence, invocation or
nonexecution, outputs and lineage assertions. Each exercises a deliberate status
mutation against the same independent assertion. No consumer-kind equivalence is
assumed. Runtime graphs have one to four nodes and no external work.

## Six custom ports

`port-inventory.json` inventories Catalog.providers, Binder.bind, Driver.execute,
Transport.invoke, Store.put/get and Observer.observe. Sixty scenarios exercise
valid behavior, applicable invalid/malformed returns, errors, catalog iteration,
transport/driver streaming, trusted identity violations, cancellation and
concurrent run isolation through actual Relay. Typed errors retain their codes
and details. Record corruption mutations test the known provider-version anchor.

Port limitations are explicit in `questions.json`:

* Relay.run calls Store.put but not Store.get. Invalid/exceptional get responses
  are exercised as host retrieval obligations; no imaginary Relay.get validator
  is claimed.
* None-returning put/observe have no judgment channel. The contract does not
  specify rejection of a non-None return; tests assert no semantic effect.
* Arbitrary custom Store.put argument mutation has no declared isolation rule.
* Synchronous callbacks have no asynchronous cancellation point. External task
  cancellation is tested while invocation is held by events; directly raising
  CancelledError from a synchronous callback has no specified translation rule.

The initial targeted port batch exposed a reporting-only string-expectation bug,
now fixed. A single put_return run raised PROVENANCE_LINEAGE; its isolated
reproduction passed without changing stimulus/expectation. It is retained as an
unresolved transient observation, not silently converted into an expected result.
Failure JSONLs now include full tracebacks for diagnosis.

Sharding remains SHA-256(case ID) modulo GOLDEN_SHARD_COUNT, with
GOLDEN_SHARD_INDEX selecting the shard. Reports use unique run/worker/shard files.
Use `tools.golden_v031.aggregate` to combine only one campaign's JSONLs. Coverage
is confirmed only when ALL linked witnesses pass, rather than any one passing
case. General custom code, process/filesystem/CLI/MCP/HTTP integration, external
forgery and other documented unsupported behavior remain outside this profile.
