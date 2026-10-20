# Local verification MVP

The local product reads `openverify.toml` from the selected project root. Profiles
use `include` and `exclude` glob arrays. Rules use `[rules.<id>]` tables with
`enabled` and rule parameters. Project checks return VCP Results; each violation
is VCP Evidence with a `structured_data` Finding v1 object:

```json
{"rule_id":"ruff","file":"src/example.py","line":3,"column":1,
 "message":"Unused import","code":"F401"}
```

`file`, `line`, and `column` are profile-owned observation data, not fundamental
VCP Evidence fields. Rule metadata in `rules list/show` is product metadata, not
a new VCP object. The Finding v1 required fields are `rule_id`, `file`, `line`,
`column`, and `message`; tools may add `code`, `text`, `replacement`, or `stdout`.
Line and column are one-based. An empty file and zero positions denote a
project-wide check such as pytest.

The same TOML file may contain `[providers]` with `entry_points` and
`[[providers.stdio]]` entries (`argv`, `manifest_file`, optional `cwd` and `env`).
`openverify client --project-root . --database relay.db` loads those trusted
host bindings. Provider executables and manifests remain outside graph input.

`openverify code check --staged` materializes the complete Git index in a
temporary directory. It reads NUL-delimited index paths and blob object IDs;
unmerged entries, symlinks, and submodules are reported as setup errors. This
means an unstaged fix cannot satisfy a staged violation. The staged project
configuration and tool configuration are read from the same materialization.
`--changed` uses working-tree bytes. Both commands leave source untouched.

Ruff lint and Ruff format run by default on selected Python files and honor
project Ruff configuration. pytest runs only when `tests` is configured.
ast-grep runs only when a language/pattern or rule file is configured. Missing
required executables are execution ERROR. English phrase, terminology,
replacement, and em-dash checks are deterministic; Markdown fenced blocks are
excluded. Optional external writing tools are outside this MVP and are
unavailable until a configured provider exists.

The CLI exits 0 for PASS, 1 for FAIL, 2 for setup or execution ERROR, and 3 for
any other VCP determination. `--json` writes a machine-readable report with
per-rule VCP Results and Evidence.

Golden V4 is a sealed historical audit of the release baseline. CI runs its
cases in that exact baseline checkout and runs current production, Relay,
conformance, and reconciliation tests on this feature source. The frozen Golden
result does not certify the new harness behavior; the new integration and
cross-language tests provide that evidence.
