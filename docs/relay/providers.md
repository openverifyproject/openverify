# Providers and standard capabilities

All computations, including custom reducers and policies, use Provider Contract
0.1. The provider contract remains independent of Relay. SDK manifests and schemas
can be used by other runners or providers in other languages.

```sh
python examples/custom-provider/check.py
openverify providers inspect openverify.standard.text
```

The custom example prints its complete validated manifest, registers the decorated
async function, authors/binds a new capability, invokes it and prints a validated
FAIL Result with a structured prohibited-phrase finding. No Relay source changes.
`@provider(provider_id=..., provider_version=..., capability_id=...,
capability_version=..., kind=..., input_schema=..., config_schema=...,
output_schema=...)` requires all three schemas and the operation role. The
function receives only fresh `(inputs, config)` objects. It may return an explicit
port mapping, Result, Decision, ExecutionObservation, or the role's policy outcome.
The decorator's declared output schema describes the resulting actual wire output.
Result/Decision conveniences produce `{"result":...}` / `{"decision":...}`;
policy outcomes are direct. This normalization is provider authoring, not a
runtime bypass of schemas. Ordinary externally invoked output is never wrapped.

Use ExecutionObservation for information plus Result/Decision, measured usage,
observed evidence or an explicit computation error. The wrapper emits evidence and
usage as Contract events and final authoritative usage. Exceptions are ERROR
Outcomes, never FAIL. Do not measure usage you cannot observe. Direct SDK Provider
objects can implement async event/outcome streams and cancel themselves.

`Catalog.register(provider)` is an explicit trust decision. Calls serialize unless
registered with `concurrency_safe=True`. `Catalog.register_transport(manifest,
transport)` accepts an explicit external connection. Duplicate provider ID/version
registration rejects. Capability IDs/versions match exactly; ranges/fallbacks do
not exist. One matching provider is selected; multiple matches require explicit
`RuntimeConfig(bindings={node_id: ProviderBinding(...)})`. Custom policy bindings use
`policy:ACTIVATION`, `policy:SELECTION`, `policy:ADMISSION` as host keys.

Entry-point factories use group `openverify.providers`; discovery alone executes
nothing. `catalog.load_entry_points({"trusted_package_entry_name"})` loads only
explicit host-approved entries. Distribution/name ownership is not authenticated.

Run an external provider with
`StdioTransport((absolute_python, absolute_provider_script), absolute_cwd)`.
The complete example is [provider.py](../../examples/stdio-provider/provider.py).
`serve_stdio(provider)` is an optional Python convenience for the published
Content-Length/JSON-RPC binding. Other languages implement the same published
initialize/invoke/event/cancel protocol. One isolated initialized session is used
per invocation. Its manifest must equal the trusted catalog snapshot. Providers
must handle EOF, cancellation, and stdout framing; stdout is never a log stream.

CLI `--providers providers.json` is **trusted host configuration**. Generate
complete, runnable configuration using the real external provider example:

```sh
python examples/stdio-provider/run.py --export-dir .pytest_cache/stdio-example
openverify run .pytest_cache/stdio-example/graph.json --inputs .pytest_cache/stdio-example/inputs.json --providers .pytest_cache/stdio-example/providers.json --json
```

The export contains its complete validated manifest and absolute argv/cwd, plus a
portable graph and typed inputs. It produces FAIL/exit 1 for prohibited TBD.
The configuration object has `stdio` entries with manifest/argv/cwd, and an optional
`entry_points` allowlist. `--bindings bindings.json` supplies exact four-field
concrete binding objects by node ID when disambiguation is required. Graph JSON
cannot authorize an executable.

The following table specifies v1 standard capability meaning. Manifest schemas
are available through `providers inspect`; all Evaluate/Aggregate inputs also
include explicit subject and criterion. All declared information outputs must
match graph port declarations exactly.

| Capability (`openverify.` prefix) | Inputs; configuration | Outputs/meaning |
| --- | --- | --- |
| read_text | file | UTF-8 text and identity {path,sha256,size}; missing/binary/oversized is ERROR |
| read_file | file | base64 bytes and identity; bounded binary observation |
| select_files | directory; mode files/glob/directory, files/glob | Sorted authorized file paths |
| git_scope | cwd, base; mode WORKTREE/STAGED/UNSTAGED, include_untracked | changed_files, changed_hunks, diff, candidate, changes, deleted_files |
| candidate_unchanged | cwd, candidate | FAIL with stale_candidate if checked identities/content/HEAD changed |
| ruff | cwd, files; select diagnostic codes | Result plus findings; exit 1 is lint FAIL, runner errors are ERROR |
| pytest | cwd; optional tests (default []) | Full test scope by default; exit 1 is FAIL, exits 2–5 are ERROR |
| astgrep | cwd, files; language/pattern OR rule_file | Whole-file findings from actual CLI, normalized source coordinates |
| scope | findings, files, ranges; mode files/changed_files/directory/changed_spans/ast_ranges | Filtered findings; directory mode requires directory config |
| no_findings | findings | PASS iff supplied findings are empty |
| text | text, optional required_terms/prohibited_terms; optional required/prohibited/patterns | Deterministic literal/regex Result with structured missing/match findings |
| json_parse | text | Strict parsed value; duplicate keys/nonfinite/malformed JSON error |
| schema | value; schema | SDK offline JSON Schema property check |
| action_policy | action,target,allowed_prefixes | Only delete under an allowed directory prefix passes; rejects traversal/absolute paths |
| gate | checked Result | CONTINUE only for successful applicable known PASS; otherwise STOP_FAILURE |
| command | no inputs; host Command object fixes argv/cwd/env | observation {argv,cwd,returncode,stdout,stderr}; no automatic verdict |
| command_check | observation; exit_code, optional stdout/stderr required substrings | Verify host-supplied or captured command observations |
| aggregate | explicit members, Results and semantic inputs; reducer/handling | VCP standard reducers |

Text input terms and configured terms combine; configuration never overwrites
bound semantic inputs. Text offsets are zero-based Unicode indices, end exclusive;
lines/columns are one-based. Tool finding ranges use one-based half-open end
coordinates. Changed Git hunks use one-based new-file start/count; zero-count
deletions contain no new-file lines. AST intersection compares full half-open
ranges; changed-line filtering compares occupied lines.

Git WORKTREE compares explicit base commit to tracked working content; STAGED
compares base to the index; UNSTAGED compares index to worktree and requires empty
base. `include_untracked` is explicit in every scope config. Untracked files get
whole-file new ranges. Renames preserve old/new paths in changes; deleted paths
are reported separately and excluded from executable file scopes. Candidate
fingerprints describe actual working content. Staged scope alone is not a claim
that tools checked index bytes: materialize a separate checkout to verify those.
The shipped code graph uses WORKTREE, base supplied by the host, and untracked files.

Ruff runs isolated with explicit codes; it does not execute repository Ruff config.
pytest executes configured tests/repository Python code and plugins with actual
process privileges. AST rules are actual ast-grep pattern rules or authorized rule
files, not a substitute parser. Tools are found in the active Python scripts
directory, then PATH, at trusted catalog construction. Hosts can pass explicit
`Tools(FileAccess(...), ruff=..., pytest=..., astgrep=...)`. Git is installed
separately. Missing tools return actionable execution ERROR messages.

Semgrep, OPA, Z3, Lean, TLC, Guardrails AI, LLM judges, and retrieval services are
not bundled. Add real installed implementations through the same Provider Contract.
