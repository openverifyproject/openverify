# Independent current-draft golden suite

This suite pins **VCP `draft`**, **Provider Contract `0.1` DRAFT**, and the
**Relay local profile `0.1`** independently. Its own release is **0.1.0**.
The semantic revision is `efe9abdfabbe913e9633687721690af47ef61b26`.
Nothing here claims stable VCP 1.0 compatibility.

The version index is `manifest.json`. Each version contains a source snapshot,
feature matrix, literal expected bundles, separate input bundles, case index,
coverage inventory, and SHA-256 manifest. JSON Pointer references in `cases.jsonl`
identify individual cases inside bundles. Arrays remain ordered; JSON booleans
and numbers are distinct. Explicit judgment/output null remains data.

The author read normative prose, all normative schemas, the standard profile,
and public Relay documentation before writing the expectations. No production
module was read to calculate expectations, and Relay was not run. The first
commit freezes `tools/golden/{oracle,provider_oracle,compare,enumerate_states,
enumerate_graphs,build_baseline,stdio_provider,verify_manifest}.py` and the baseline.
Later commits add invocation adapters and the harness. Audit is a separate stage.

Run from this worktree with Python 3.13 and the repository development environment:

```sh
python -m tools.golden.verify_manifest
python tools/golden/run_suite.py --profile all
python -m pytest tests/golden_current -q
```

The runner verifies frozen hashes first. There is no snapshot-update mode.
Reports go outside the immutable baseline, under `.pytest_cache/golden-current-reports`.
Use `--profile vcp`, `provider`, `relay-local`, or `integration` for narrower runs.
`--self-check` audits only the suite; it never imports or invokes OpenVerify.
Use `--case CASE_ID` for precise reproduction. Nonzero exit means a failure,
environment gap, specification block, or incomplete adapter coverage; none is PASS.

Expected semantics come from literal fixtures and small independent tables:

- Result axes: all 1,024 categorical combinations including omitted and null
  optional axes; 66 valid, 958 invalid. Optional observation presence is separately
  covered with all 256 masks over nine representative semantic states.
- DAG topology: all labeled DAGs at 0–4 nodes (1, 1, 3, 25, 543).
  Node-kind assignment is separately bounded at two nodes (52 assignments,
  including structurally inapplicable Aggregate assignments as negative cases).
- Abstract scheduler: all reachable PENDING/RUNNING/TERMINAL states at 0–3 nodes,
  290 states and 364 transitions across those DAGs. This is model coverage,
  distinct from forced interleavings against a real runtime.
- Larger DAGs: 32 samples with seed 71717, 5–12 nodes, deterministic edge
  deletion shrinking. Metamorphic cases reorder independent nodes/edges and add
  an irrelevant node. This is not exhaustive arbitrary-program coverage.
- Reducers: all eight standard reducers, all 128 exceptional-handling masks
  for each exceptional partition, explicit membership and weighted 0.75 regression.
  Exact mathematical means with unspecified portable rounding are blocked.
- Provider traces: lifecycle flags, six event kinds, terminal outcomes, sequence
  constraints, correlation, cancellation and decimal-precision deadlines.

The stdio test peer uses only Python's standard library. It writes actual
Content-Length frames and has deterministic, failing, cancelling, delayed,
partial-event, malformed, duplicate-terminal and lost-process behaviors.
It explicitly rejects deadline/budget enforcement it does not implement;
deadline conformance traces are separate from physical timeout tests.

Public adapters invoke the implementation under test; they cannot create or
update expected values. Production validators are SUT operations when parsing
fixtures or testing mutated records, never independent expectation calculators.

The historical suite, existing fixtures/tests, implementation, schemas, specs,
examples, and production dependencies are unchanged. No old expectation has
been declared stale or superseded. This release has no superseded suite.

Read `BLOCKED_BY_SPEC.md` for unresolved rules. See `BUILD_REPORT.md` for adapter
coverage and execution status. A feature-to-case link alone does not establish
complete interface or interaction coverage; generated inventory, adapter coverage,
and execution evidence are reported separately.

## Release discipline

Protocol changes require a new spec revision and semantic baseline. More tests
with unchanged semantics require a new suite release while preserving this one.
Corrected expectations require independent written adjudication, a new version,
and preserved prior fixtures. Implementation fixes do not change goldens.
New optional profiles add their own cases. Unsupported features have explicit
rejection expectations. Git anchors the checksum manifest; this is integrity
checking, not authenticated provider attestation or cryptographic signing.
