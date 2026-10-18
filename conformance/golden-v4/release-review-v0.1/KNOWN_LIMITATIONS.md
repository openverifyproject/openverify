# Known scope and evidence limits

Status remains DRAFT. See the supported profile in [limitations.md](../../../docs/relay/limitations.md), [providers.md](../../../docs/relay/providers.md) and the canonical source references retained per record. Relative source paths in JSON are repository-root paths.

## Supported behavior with bounded evidence

The current Python package executes authored finite DAGs, typed bindings and snapshot availability; honors the tested BLOCK/OMIT/DEFAULT effects; invokes CUSTOM on an explicitly empty ordered member list; records tested cancellation, lineage and resource effects; exposes the six replaceable ports and shipped entrypoints. These are tested examples and partitions. Requirement-wide sufficiency is not established for every public operation or schema interaction. See the finite blocker list rather than interpreting this description as certification.

The 22 added tests cover two real stdio error responses, nine gate classes, invalid gate input, storage snapshots/duplicates, cancellation token values, filesystem boundaries, three FunctionProvider channels and a deterministic service concurrency barrier. Existing 366 revision cases and Golden cases are reused. No old Golden versions are inputs to these additions.

## Timing and platform

A full run concurrent with other verification/build work produced TimeoutError for the trivial pattern `\\d+` on `abc123`, at `tests/relay/test_standard.py::test_json_parse_schema_boolean_number_and_pattern`. `standard/text.py` includes interpreter startup in its two-second subprocess budget. An isolated rerun passed. This is observed resource sensitivity, not proof of a regex semantic defect or scheduler race. The fail-closed safety budget is retained; the final sequential outcome is recorded in TEST_RESULTS.md. No sleep-based race assertion was added.

The sole existing skip is `tests/relay/test_local_paths.py:66`, POSIX case/separator behavior, on Windows. Windows evidence does not establish POSIX correctness. The package requires Python >=3.13,<3.14; no other interpreter version is claimed.

## Explicit exclusions already documented by the profile

- Cycles, iteration, dynamic expansion, external schemas and required unknown extensions are not executable profile features. RETRY/DEFER terminate an occurrence; they do not create durable scheduling.
- Providers must be correct external implementations. Arbitrary malicious replacement ports, coherent record forgery, domain ownership attestation and external provider honesty are not cryptographic promises.
- Stdio process management is not isolation; in-process async providers must cooperate. No pooling, restart/replay, remote discovery, enforced provider deadline/budget or multi-attempt cancellation provenance is supplied by the helper.
- MemoryStore is volatile; JsonlStore is single-process and nontransactional. No fsync, database recovery or multiprocess safety is inferred.
- HTTP is a localhost adapter; MCP serves allowlisted graphs. No invented cross-entrypoint parity or multi-tenant service guarantee.
- Regex and deterministic text checks do not establish factual truth. Code tools do not create an atomic workspace snapshot.

These exclusions do not turn whole canonical records into unsupported requirements: a record can mix supported validation and externally owned effects. All 615 records are retained; none receives blanket unsupported status here.

## Remaining proof and coverage limits

Historical links sometimes include all assertions from shared runtime branches. Such an AST list does not prove a predicate executed for a particular case. Positive/negative acceptance alone may not establish intended error precedence, provider noninvocation, exact output, record or event effects. Existing tests may already assert some residuals; missing links are not counted as missing tests.

Root schema presence reductions do not establish arbitrary root validity. Finite Result masks do not exhaust JSON. Algebraic reducers retain rounding and identity premises. Shared mutable scheduler state lacks a universal arbitrary-size DAG proof. Nonprogressing references, annotation-location references, arbitrary recursive schemas, custom numeric payloads and external capabilities retain the precise source-defined constraints and questions in the unchanged canonical model.

Original frozen artifacts and the earlier nine-expectation correction overlay are preserved. This pass adds no frozen update mode. The separate SDK branch/worktree and eight language packages were not modified or published.
