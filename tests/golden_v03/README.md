# Golden v0.3.0 — fast DRAFT profile

From the repository root, with normal project dependencies and Python 3.13:

```powershell
python -m pytest -q tests/golden_v03/test_contract_structure.py
python -m pytest -q tests/golden_v03/test_master_execution.py
```

Both together: `python -m pytest -q tests/golden_v03/`.
No installation, network, downloaded model, process provider, or external tool
is started by either suite. **Build only: tests and timings are UNVERIFIED.**

Test A batches individually identified pure contract checks by category. It
includes the full 1,024 categorical Result encodings (66 valid, 958 invalid),
2,304 observation masks, an additional observation-law check for each of the
66 valid encodings, all 24 Decision/destination cells, tiny graph mutations,
573 labeled DAGs, mathematical reducers, pure availability/guard/readiness laws,
current portable fixtures, schema field boundaries, Provider lifecycle traces,
and independently known provenance fixtures. It never invokes providers or Relay.

Test B executes one immutable 17-node graph through actual Relay and real
in-process Provider streams. It exercises all four node kinds and sources,
eight standard reducers and custom aggregation, policies, control, input/output
faults, usage, cancellation, timeout, concurrency barriers and provenance. Each
run has fresh scripts, buffers, catalog, observer and execution state. The
isolation scenario intentionally shares a Relay across two concurrent runs.
No extra runtime graphs are needed. Provenance corruption checks share the
normal run rather than executing another identical baseline.

Expectations are frozen in `conformance/golden-v0.3/`, independently of the SUT.
`coverage.json` distinguishes implemented witnesses from uncovered, ambiguous
and unsupported obligations; “covered” means code exists, **not a passing test**.
`enum-inventory.json` inventories every enum in both current normative schema
trees. `state-transitions.json` and `set-cover.json` describe the finite models
and scenario choices. Earlier Golden profiles are unchanged and remain useful.

The nine Result representatives do not stand for all categorical encodings:
the additional 528 checks exercise each observation law against every valid
encoding. The eight mask fields are judgment, score, severity, evidence,
output, usage, metadata and extensions. Verdict belongs to the categorical axes.

The availability model explicitly classifies 108 cells: six source/port profiles,
six statuses and three handling rules. Inapplicable cells retain their reason.
The previous 360-cell audit's extra dimension is unspecified in the inspected
artifacts, so reproducing its 128-applicable count is **not claimed**. Semantic
Decision rejection is checked even for the seven unresolved exact-code cases.
Numerical checks use exact representable answers or small mathematical intervals;
they do not prescribe a portable floating-point rounding convention.

## Implementation selection

The default production implementation is pinned to
`5f17f402a270882f244a54dde25eda92a085eb39` using normalized source hashes.
Test-only commits can advance this checkout's HEAD without changing that pin.
An existing import from another checkout is rejected. No older Relay is selected
automatically. To test another Git checkout explicitly:

```powershell
$env:GOLDEN_IMPLEMENTATION = 'C:\path\to\production-checkout'
python -m pytest -q tests/golden_v03/test_master_execution.py
Remove-Item Env:GOLDEN_IMPLEMENTATION
```

The report records the explicit checkout's actual HEAD, source digest and path.
The implementation checkout must contain `src/openverify/relay` and Git metadata.
Dependencies come from the Python environment running pytest. No Git subprocess
is invoked by the suites. Source/spec/expectation drift fails closed.

## Automatic timings and shards

Every execution writes unique UUID/worker/shard JSONL and summary JSON files to
`.pytest_cache/golden-v03/timings/`. Terminal summaries remain enabled under `-q`.
Case failures identify exact stable IDs. JSONL includes all individual outcomes,
inapplicability reasons, category timings, coverage links, seed, platform, Python,
implementation identity and failing IDs. `perf_counter_ns()` measures elapsed
time; UTC timestamps identify the run. Peak memory is null when unavailable.

Total duration covers the pytest worker session through session finish, including
collection, setup, integrity checks and semantic checks. Relay execution duration
measures awaited Relay calls separately from catalog/fixture setup and record
audits. Semantic-check duration includes adapter assertions and per-case setup.
Parallel time sums are CPU/task durations, not end-to-end distributed latency.

```powershell
$env:GOLDEN_SHARD_COUNT = '4'
$env:GOLDEN_SHARD_INDEX = '0' # use 0, 1, 2, 3 on separate workers/machines
python -m pytest -q tests/golden_v03/test_contract_structure.py
python -m pytest -q tests/golden_v03/test_master_execution.py
```

Partitioning is SHA-256(case ID), interpreted as a big-endian integer, modulo
shard count. Each shard has independent fixtures and report files. Optional
pytest-xdist category parallelism works if already installed (`-n auto`);
neither suite installs it. Reports from all workers are needed. Copy only the
JSONL files for the intended campaign into one directory and aggregate:

```powershell
python -m tools.golden_v03.aggregate .pytest_cache/golden-v03/timings --output .pytest_cache/golden-v03/summary.json
```

The aggregator rejects duplicate IDs, conflicting outcomes/implementations,
missing shards, wrong partitions, missing cases or expected obligations, and
failed pytest workers. Keep campaigns separate; including previous runs correctly
reports duplicate IDs. This shards tests, not Relay execution itself.

Neither suite proves universal correctness, honest external providers, coherent
external forgery detection, arbitrary custom code, large/unbounded graphs, real
filesystem/process behavior, CLI/MCP/HTTP integration or production conformance.
Known scripted manifests anchor provider versions; upstream Result snapshots and
embedded criterion bindings are checked explicitly. Malicious replacement-port
combinations remain an explicit uncovered obligation. See the coverage manifest
for precise boundaries. No runtime targets have been measured or guaranteed.
