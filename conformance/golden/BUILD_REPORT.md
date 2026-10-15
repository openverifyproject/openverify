# Golden suite build report

**GOLDEN SUITE COMPLETE FOR THE FULL REQUESTED CURRENT PROFILE: NO.**

This is an implemented, versioned suite with 11,943 collected cases, independent
frozen expectations, public invocation adapters, provider simulators, bounded
generators, reports and a runnable harness. It does not fulfill every requested
interaction matrix or every finite interface rule. Four source-range adapter
experiments remain explicitly unimplemented because the published finding/range
wire shape needs independent profile adjudication. They fail as
`ERROR / ADAPTER_UNIMPLEMENTED`; they never become PASS.

No Relay execution was performed. This preserves the requested separation from
Stage C. Syntax, collection, inventory, checksums and independent model checks
were performed. No implementation mismatch was inspected, and the frozen oracle
and expectations have not been edited since their freeze commit.

## Git and revisions

- Branch: `test/openverify-golden-current`.
- Worktree: `.pytest_cache/golden-current/worktree` inside the original checkout.
- Original branch preserved: `feat/openverify-relay`, `efe9abd`.
- Confirmed base: `2c02bfbd96fc4525c5fb33bd9fe9246d02f133f1`.
- Expectation freeze: `33b511c`, `golden: freeze spec-derived expectations`.
- Adapters/tests/runner: `300de76`, `golden: add public adapters tests and audit runner`.
- Coverage/build evidence: subsequent `golden: document coverage limits and audit manifest` commit.
- No push, deployment or package publication.

VCP marker is `draft`, Provider Contract is `0.1` DRAFT, Relay local profile is
`0.1`, and the separate golden release is `0.1.0`. Normative revision for both
protocols is `efe9abdfabbe913e9633687721690af47ef61b26`.

VCP specification source-set SHA-256:
`4be3020e378734d9c83d26a464222e431a0d660551a04dfa4a700eec1227a727`.
Provider Contract specification source-set SHA-256:
`8c9d95d03f87134a18aa9ac13767367df943be46c135bc44514d1d264d5a3905`.
These are hashes of sorted path-to-file-hash maps, defined in the frozen authoring
tool. The source snapshot also records each document/schema's exact byte hash.

## Artifacts

```text
conformance/golden/
  README.md
  BLOCKED_BY_SPEC.md
  BUILD_REPORT.md
  manifest.json
  build/
    adapter-manifest.json
    coverage.json
    coverage.md
    selfcheck.json
  versions/draft-efe9abd/
    manifest.json
    specification-snapshot.json
    feature-matrix.json
    cases.jsonl
    coverage.json
    checksum-manifest.json
    expected/{vcp,providers,relay,integrations,mutation,blocked}/
    fixtures/{vcp,providers,relay,integrations,mutation,blocked}/
tools/golden/
  oracle.py
  provider_oracle.py
  compare.py
  enumerate_states.py
  enumerate_graphs.py
  build_baseline.py
  stdio_provider.py
  verify_manifest.py
  execution.py
  coverage.py
  run_suite.py
  selfcheck.py
tests/golden_current/
  test_vcp.py
  test_provider_contract.py
  test_relay_graphs.py
  test_concurrency.py
  test_provenance.py
  test_extensions.py
  test_integrations.py
  test_adversarial.py
  conftest.py
  check.py
  adapters/{public,runtime,ports,provenance,standard,integrations,mutations}.py
```

## Counts and evidence

| Profile | Unique declared cases |
| --- | ---: |
| vcp | 3,498 |
| provider | 138 |
| relay-local | 8,204 |
| integration | 103 |
| Total | **11,943** |

The feature matrix has 108 rows: 100 supported, three unsupported, five explicitly
open. Every supported row has case links. Links demonstrate declared coverage,
not exhaustive interaction coverage. Full per-feature valid/invalid/boundary/
interaction counts are in [build/coverage.md](build/coverage.md) and
[build/coverage.json](build/coverage.json). Category totals and operation counts
are recorded separately, without counting one case multiple times as a unique test.

| Enumeration | Exact bound/count |
| --- | --- |
| Result categorical axes | 1,024 combinations; 66 valid, 958 invalid; omission and explicit null included |
| Optional observation presence | 256 masks × nine representative semantic states = 2,304 cases |
| All labeled DAGs | 0–4 nodes: 1 + 1 + 3 + 25 + 543 = 573 |
| Node-kind assignments | 1–2 nodes, all four kinds: 52 assignments including invalid Aggregate structures |
| Abstract scheduler | DAGs through three nodes; 290 reachable states, 364 transitions, 30 graph-model cases |
| Seeded larger graphs | Seed 71717; 32 DAGs, 5–12 nodes; deterministic edge-deletion shrinking |
| Reducer cases | 7,289; all eight reducer names; 128 exceptional-handling masks per exceptional partition |
| Provider cases | 132 lifecycle traces + six framing cases |
| Six extension ports | Six representative variants per port = 36 experiments |
| Mutation sensitivity | 13 independent assertion probes, all detected, zero surviving assertion probes |
| SUT cases executed during build | **0** |

The abstract scheduler and assertion probes are labeled model/assertion checks.
They are never counted as SUT conformance execution. The mutation result does not
claim a production mutation-testing campaign or runtime mutant coverage.

Build validation passed:

- Frozen integrity audit: 71 source documents/schemas and 71 checksum entries;
  unique IDs, fixture references, orphan checks, feature references, oracle-import
  checks and independent table agreement passed.
- Independent model self-checks: Result counts; strict boolean/number and
  missing/null distinctions; weighted 0.75; majority tie; DAG counts; shrink
  validity; abstract prerequisites; UTF-8 frame lengths; decimal deadlines.
- Python compilation of the new tools and tests passed.
- `pytest --collect-only`: **11,943 tests collected**; no Relay invocation.
- Ruff undefined/unused-name checks passed for the new adapter/harness files.

Git, Ruff, pytest and ast-grep executables were found in the current environment.
Dependency versions and paths are in [build/adapter-manifest.json](build/adapter-manifest.json).
Availability is not a claim that their integration tests ran. Optional tool
absence is `ENVIRONMENT_UNAVAILABLE`, not PASS. Pytest displays explicit skip
reasons; the complete runner records separate machine-readable status counts.

## Uncovered or blocked work

- Every node kind has minimum/full definitions, typed-source cases and full-graph
  participation. The requested complete cross-product of per-kind output errors,
  binding faults, guards, policy outcomes, cancellation and resource cases is absent.
- All Result categorical combinations are enumerated. Invalid custom-policy
  outcomes, typed policy inputs and all policy-failure interactions are incomplete.
- All four input sources are exercised. All six availability names are inventoried,
  but exact source-to-consumer behavioral coverage for every availability partition
  is incomplete; a failure tagged with an availability feature is not proof of that
  exact resolution status.
- All reducers and custom Aggregate are represented. Most exceptional-state cases
  invoke the advertised standard capability directly, because nonexecution Results
  cannot legally be emitted by an invoked graph evaluator. The full requested graph
  matrix for every reducer is incomplete. Contract error codes are observed verbatim;
  the adapter does not parse diagnostic text to invent semantic error categories.
- Provider lifecycle flag/event partitions are covered; full RPC initialization,
  rejection/correlation/session transitions and all fault sequences are incomplete.
- All six ports have representative complete-run experiments. This does not
  establish exhaustive interface-rule coverage, and custom persistence honesty is
  not authenticated by a store response.
- Concurrency, cancellation, failures and provenance have executable experiments;
  their complete Cartesian product with graph/control states is absent.
- All shipped capability names and public entrypoints are represented. The exact
  changed-span/AST-range/zero-deletion/half-open-boundary scope adapters require a
  published finding/range object shape and are explicit errors. Fully integrated
  code+scope+freshness and document graphs do not meet the entire requested matrix.
- No end-to-end or Relay pass count is claimed before the separate audit.

Portable numeric rounding, sampling identity, multiple interrupted-attempt
provenance, transport/policy annotations and authenticity are documented in
[BLOCKED_BY_SPEC.md](BLOCKED_BY_SPEC.md). The stable Decision-invariant error
category is also unspecified in normative prose. None was chosen from Relay output.

## Immutability and production safety

Frozen checksum-manifest SHA-256:
`3d04a1054f370c40ae21bdcddcd395cfffb691c5ac0ce59100df2bc4b18f8af7`.

Frozen version-manifest SHA-256:
`2818158da175c898077d8ad40d4b85e338ac10165b930c2758251ffaa4700753`.

Frozen specification-snapshot SHA-256:
`ae74454faf9c5c207f24ce5e2174e309f6fc497783754e8c60d3bcd6d2f64139`.

Individual fixture and oracle hashes are in the frozen manifests. Git commit
`33b511c` anchors the checksum manifest itself. Later commits add only adapters,
tests and documentation; the frozen baseline and oracle are unchanged.

**Zero production changes confirmed.** `src` tree identity at both the original
revision and the build is `e1526435e621aca2f68399775b5c1be261395f8e`.
No preexisting tracked file was modified, deleted, renamed or type-changed.
Normative specs, VCP/Provider schemas, existing tests, historical goldens, examples,
production dependencies and the Relay branch are untouched. No prior expectation
is imported, declared stale or superseded.

## Exact read-only audit commands

Run from the new worktree, using its Python 3.13 environment. These commands leave
tracked files unchanged; execution reports and disposable fixtures use temporary
or ignored paths. The full SUT commands are for the separate audit session.

```sh
git status --short
git log -3 --oneline
git diff --name-only --diff-filter=MDRT efe9abd HEAD
git diff --exit-code 33b511c -- conformance/golden/versions tools/golden/oracle.py tools/golden/provider_oracle.py tools/golden/compare.py tools/golden/enumerate_states.py tools/golden/enumerate_graphs.py tools/golden/build_baseline.py tools/golden/stdio_provider.py tools/golden/verify_manifest.py
python -m tools.golden.verify_manifest
python tools/golden/run_suite.py --self-check
python tools/golden/run_suite.py --profile all
python -m pytest tests/golden_current -q
```

`uv run python ...` and `uv run pytest ...` also work with the repository's
existing environment setup. No production dependency change is required.

The runner writes `report.json`, `report.md`, `coverage.json` and `coverage.md`
under `.pytest_cache/golden-current-reports`. Per-case records contain expected
data, observed failure details, status, classification and exact reproduction
command. Exit 1 means FAIL/ERROR, 2 environment unavailable, 3 specification block,
and 4 known incomplete all-profile coverage. There is no `--update-goldens` mode.

## Required verdicts

YES below means represented in the built suite; it is not a Stage C pass claim.
For combined requirements, any remaining requested coverage gap makes the answer NO.

| Requirement | Verdict |
| --- | --- |
| GOLDEN SUITE COMPLETE FOR CURRENT SUPPORTED PROFILE | **NO** |
| EVERY SUPPORTED NODE KIND | YES — four kinds represented; interaction matrix incomplete |
| EVERY FINITE RESULT/CONTROL/POLICY STATE | NO — Result axes exhaustive, policy/interface states incomplete |
| EVERY SUPPORTED INPUT SOURCE/AVAILABILITY | NO — sources covered, exact availability matrix incomplete |
| ALL REDUCERS + CUSTOM | NO — all names represented, complete per-reducer graph matrix absent |
| ALL PROVIDER CONTRACT STATES | NO |
| ALL SIX RELAY PORTS | YES — 36 representative experiments; exhaustive rules unproven |
| CONCURRENCY / FAULTS / PROVENANCE | NO — representative executable coverage only |
| CURRENT END-TO-END INTEGRATIONS | NO — runnable entrypoints exist, complete requested matrix absent |
| EXPECTATIONS INDEPENDENT OF RELAY | YES |
| VERSIONED AND IMMUTABLE | YES |
