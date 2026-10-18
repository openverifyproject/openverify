# Golden 0.2.0 — frozen, with explicit coverage limits

This is a separate DRAFT Golden release. Golden 0.1.0, its tools, tests and frozen
expectations remain byte-for-byte unchanged. Use its original b72942d worktree to
verify its original specification snapshot. This checkout appends non-normative
audit questions to spec/draft/open-questions.md; it changes no normative rule.

The v0.2 suite is **not complete for the entire requested current profile**. Its
reports distinguish semantic passes, exact-code ambiguity, implementation failure,
environment failure and unexecuted coverage. A case link is not an exhaustiveness
claim. The final BUILD_REPORT and machine-readable evidence give actual results.

```sh
python -m tools.golden_v02.verify_manifest
python tools/golden_v02/run_suite.py --self-check
python tools/golden_v02/run_suite.py --profile all
python -m pytest tests/golden_v02/test_oracle_regressions.py --noconftest
```

Use Python 3.13 with the existing project development environment and its installed
console script. CLI/MCP tests invoke that real script, with this checkout on the
child PYTHONPATH. Reports and disposable environments stay under .pytest_cache.
No expected file is written by execution adapters. There is no update-goldens mode.

The version directory contains exact JSON stimuli/expectations, source references,
per-case allowed nondeterminism, enumeration bounds, checksum manifests and frozen
executable assertion programs. Those programs seal the inherited experiments'
concrete setup and assertions before final execution. They do **not** resolve the
remaining independence deficiency: some integration stimuli still construct graphs
and manifests through public APIs rather than freezing complete portable wire
objects independently. This is disclosed as a gap, not promoted to independent
protocol conformance.

The closed Provider error vocabulary is distinct from VCP computation causes.
Direct reducer failures assert the existing local namespaced wrapper error and
retain the independently calculated VCP cause as a separate field. Complete graph
cases separately check Result axes, membership, propagation and observations.
The wrapper code is local API compatibility, not a ninth reserved Provider code.

`FROZEN` prevents reauthoring this revision. Checksums and the freeze commit anchor
it. Corrections after freeze require a new suite revision, never in-place changes.
Production source is unchanged on this Golden branch. The separate error-contract
audit inventories current representations and targeted implementation follow-up.
