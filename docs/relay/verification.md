# Relay v0.1 completion evidence

Implemented on `feat/openverify-relay`, based on
`2c02bfbd96fc4525c5fb33bd9fe9246d02f133f1`. The starting working tree was clean.
Implementation commit: `49e9b3a`. No remote push or publication was performed.
The following results were obtained on Windows with Python 3.13.5, using the
actual executable providers and localhost service processes.

| Check | Result |
| --- | --- |
| Existing SDK/non-golden tests | 790 passed; 0 failed/skipped |
| New Relay tests | 111 passed; 0 failed/skipped |
| VCP portable conformance manifest | 177 cases; no mismatches |
| Provider Contract portable manifest | 107 cases; no mismatches |
| `ruff check .` | Pass |
| `ruff format --check .` | Pass; all checked Python files formatted |
| Strict `pyright` | 0 errors/warnings |
| Wheel build and clean base-only installation | Pass |
| Final wheel bytes vs all package Python source files | Exact match |
| Clean installed CLI FAIL/evidence, then PASS | Exit 1 / exit 0, correct Results |
| Runtime imports of `openverify.engine.*` | None; architecture tests and clean-wheel execution probe |

Relay test grouping by test module (some modules exercise several layers):

| Group | Tests |
| --- | ---: |
| Pure core rules and authoring | 17 |
| Replaceable port contracts | 5 |
| Graph/provider semantics and all eight bound reducers | 40 |
| Concurrency and cancellation | 4 |
| Git, standard providers, process/tool integration | 19 |
| CLI/MCP/HTTP/stdio/examples and new golden fixture | 15 |
| Adversarial provenance | 9 |
| Architecture | 2 |
| Total | 111 |

No existing SDK test, historical golden expectation, normative wire schema,
Provider Contract implementation, or Reference Engine source was changed.
There are no unresolved baseline failures or newly introduced test failures.
No tracked historical `tests/golden_graph` source files exist in this checkout;
its ignored bytecode directory was left alone. The new Relay golden fixture has
independently authored expected identities/verdicts and explicit concrete bindings.

All ten requested acceptance scenarios were actually executed:

1. **Zero custom code:** built a wheel, installed it in a new virtual environment
   containing only base dependencies, ran included text verification from stdin,
   received FAIL plus prohibited-term evidence, then PASS. The installed package
   path was inside that environment, with MCP/Starlette absent.
2. **Real code:** disposable Git repositories, actual Ruff and ast-grep executables,
   intentional lint/AST violations with file/line/range findings, fix, PASS, and
   distinct changed-file versus changed-span outcomes. Explicit staged/unstaged
   scopes, rename/deletion/untracked handling and scope-capture races are tested.
3. **Custom provider:** new prohibited-phrase capability, validated complete
   manifest, registration and invocation without modifying Relay.
4. **External provider:** real initialized stdio processes, exact capability and
   manifest verification, invocation/output correlation, cancellation acknowledgement
   marker, malformed frames, duplicate outcomes, disconnect, missing executable and
   hangs. Usage survives invalid output and duplicate-terminal rejection.
5. **Agent tool:** official MCP SDK client launches the server, discovers tools,
   lists/describes an authorized graph, invokes it, inspects its retained record,
   and rejects an unauthorized graph name.
6. **Guardrail:** the helper owns the action call; a failed check never calls it,
   a passing check does, and exceptional Result axes never open the default gate.
7. **Multi-agent:** different graphs, input data and actual Git worktrees execute
   concurrently with distinct run/provider/candidate provenance. Cancelling one
   occurrence does not cancel the other.
8. **Custom infrastructure:** Binder, Driver, Store and Observer are replaced
   individually; a malformed replacement driver's correlation is still rejected.
9. **SDK consistency:** the application validates every returned RunRecord with
   the unchanged SDK. Local/external invocations cross the same Contract schemas
   and lifecycle boundary. Source/output/provider identity contradictions reject.
10. **Regression safety:** all 790 existing non-golden tests pass, all portable
    conformance cases pass, Ruff/format/Pyright pass, and architecture tests reject
    old Engine/adapters imports and inward infrastructure dependencies.

HTTP was additionally tested both through ASGI and over a real localhost socket.
Every advertised executable Python example ran successfully. Stdout/stderr limits,
explicit environment handling and descendant cleanup after a tool parent exits
are tested. The Windows Job Object implementation is exercised; the POSIX process
group path is implemented but was not executed on a separate OS in this session.

Reproduce from the checkout:

```sh
uv sync --all-extras
uv run pytest --ignore=tests/golden_graph --ignore=tests/relay -q
uv run pytest tests/relay -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

The generated local XML reports, clean environment and wheel are ignored artifacts
under `.pytest_cache`; they are not required runtime infrastructure. See
[quickstart](quickstart.md), [architecture](architecture.md), and
[limitations](limitations.md) for runnable commands and the exact supported boundary.

**RELAY USABLE TODAY: YES.** Custom graphs/providers, real code/text verification,
guardrails, Python harnesses, CLI, MCP, concurrent run isolation and compatibility
with the existing SDK are all exercised. DRAFT status and documented execution
limits remain; no stable 1.0, authenticated provenance or sandbox claim is made.
