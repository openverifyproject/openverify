# OpenVerify Relay v0.1

Relay runs the current **DRAFT** VCP and Provider Contract revision. Python 3.13
is required by this repository. No cloud account, initialization, API key, or
database is required. Install this checkout; publication to PyPI is a separate
release operation and is not performed by this change.

```sh
python -m pip install .
openverify run text --inputs examples/first-run/fail.json --json
openverify run text --inputs examples/first-run/pass.json --json
```

The first run exits **1** and returns FAIL with structured evidence for missing
Rollback and prohibited TODO. The second exits **0** with PASS. The output is the
complete VCP RunRecord, including provider bindings and consumed input snapshots.

The same commands work in PowerShell. To select Python explicitly:

```powershell
py -3.13 -m pip install .
'{"text":"Migration Rollback"}' | openverify run text --inputs - --json
```

On Linux/macOS:

```sh
printf '%s' '{"text":"Migration Rollback"}' | openverify run text --inputs - --json
```

Verify actual documents:

```sh
openverify run document --inputs examples/text-verification/fail.json --json
openverify run document --inputs examples/text-verification/pass.json --json
openverify validate examples/text-verification/definition.json
openverify inspect document
openverify providers list
openverify providers inspect openverify.standard.text
openverify examples
```

`--inputs -` reads strict JSON from stdin. A graph path can also be `-`; only one
input can use stdin. `--output run.json` saves the record. With `--json`, stdout
contains only a RunRecord; errors go to stderr. Without it, stdout summarizes
node outcomes and supplied evidence. `--run-inputs` aliases `--inputs`.

| Exit | Meaning |
| --- | --- |
| 0 | All terminal judgment results have binary PASS |
| 1 | A terminal judgment has FAIL |
| 2 | Invocation/configuration error, or an execution ERROR anywhere in the record |
| 3 | No terminal binary determination: UNKNOWN, nonexecution, NOT_APPLICABLE, score-only, or no judgment |

Terminal judgments are Results with no descendant Result node. No overall verdict
is invented. Use explicit aggregation/handling and your own gate policy when a
different host decision is needed. These exit codes replace the legacy demo CLI's
"always zero for completed runs" convention. The Reference Engine API is unchanged.

For Git/Ruff/ast-grep (Git must be installed separately):

```sh
python -m pip install '.[code]'
python examples/code-verification/run.py
```

PowerShell also accepts the single-quoted extra. This executable example creates a
disposable Git repository, introduces real lint/AST violations, verifies FAIL with
file/range evidence, fixes them, and verifies PASS. To check your own worktree, save
`{"cwd":"/absolute/path/to/repo","base":"HEAD"}` as `inputs.json`, then run:

```sh
openverify run code --inputs inputs.json --root /absolute/path/to/repo --json
openverify run code_spans --inputs inputs.json --root /absolute/path/to/repo --json
```

For Windows use JSON-escaped paths (`C:\\work\\repo`) or forward slashes
(`C:/work/repo`). `code` checks Ruff over changed Python files and AST matches
intersecting changed lines. `code_spans` filters Ruff findings by changed lines too.
Both scan whole files, then filter. Both check candidate freshness after tool work.

Python/harness entry:

```python
import asyncio
from openverify import Relay
from openverify.relay.templates import text_graph


async def main():
    relay = Relay()
    run = await relay.run(text_graph(), inputs={"text": "Migration Rollback"})
    print(run.results["all"].verdict)
    print(run.to_json())


asyncio.run(main())
```

`Relay.run_sync(...)` is available outside an already-running event loop. Run the
full examples for [authoring](../../examples/custom-graph/run.py),
[custom providers](../../examples/custom-provider/check.py),
[guardrails](../../examples/guardrail/run.py),
[typed applications](../../examples/application-integration/run.py), and
[concurrent hosts](../../examples/multi-agent/run.py).

See [providers](providers.md), [integration](integration.md),
[security](security.md), and [limitations](limitations.md) before exposing tools
or file access to another caller.
