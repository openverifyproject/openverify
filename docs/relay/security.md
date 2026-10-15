# Execution and trust boundary

Relay is a local execution harness, **not a security sandbox**. Python providers,
pytest tests/plugins and authorized external tools run with their process's real
privileges. Use separate OS accounts, containers, or equivalent host isolation for
untrusted executable code. No graph can name an executable and automatically
authorize it through the generic command capability.

The host approves provider registration, entry-point names, stdio argv/cwd/env,
filesystem roots, executable paths, timeout and concurrency. Graphs choose among
available capabilities and supply typed data/config. Caller authorization remains
the host's responsibility. A graph's config is not trusted executable config.
Only an explicitly registered Command fixes generic command argv/cwd/environment;
the default catalog provides command observation verification but no command
launcher registration. External network access requires a configured provider;
Relay performs no automatic artifact or schema fetching.

Filesystem operations resolve paths against authorized roots; default roots are
the current working directory at Relay/catalog construction. Relative document
paths require one configured root. `--root` replaces defaults and can be repeated.
Tool files must also belong to the declared cwd. Symlinks resolving outside roots
reject. These checks do not create an atomic filesystem sandbox against a hostile
process racing path changes. File reads are bounded to 2 MiB and selection to
10,000 files by default, configurable with FileAccess. Binary documents explicitly
error; read_file provides bounded base64 observation instead.

Subprocesses use argv arrays and explicit absolute cwd, with no shell=True. Default
environment inheritance is from the trusted host process; pass a complete env
mapping on Command or StdioTransport to restrict it. On Windows only SystemRoot
is supplemented when required for OS runtime services. No secrets are automatically
copied into graph ports or logs. Be aware that graph snapshots, full RunRecords,
provider diagnostics/evidence and command output may intentionally contain caller
secrets. Store/share them according to your application policy.

The local driver enforces a per-invocation host timeout (30 s default), independent
of provider-declared deadlines. It does not send an unsupported provider deadline
or claim budget enforcement. Commands bound output to 2 MiB per stream; stdio uses
the SDK's 16 MiB message limit and 1 MiB stderr limit. Violations/transport loss are
ERROR, never criterion FAIL. Provider event capture is bounded to 10,000 events
and 16 MiB by default (LocalDriver settings); deterministic text findings are
bounded to 10,000 observations. Cancellation sends a cooperative request where
supported, then terminates the process tree within a bounded grace period.

On Windows a supervisor establishes a kill-on-close Job Object **before** tool
code starts. Its descendants belong to that job even after the tool parent exits.
On POSIX a new session/process group is killed on cleanup. Programs deliberately
escaping their process group are outside this local lifetime mechanism; use OS
isolation when running hostile code. Cleanup is tested on the current platform.
No claims of cross-platform runtime testing are made merely from having both code
paths. Providers should not daemonize or retain inherited pipes after completion.

In-process providers must be async and cooperative. Sync callbacks reject at
decoration. Blocking native code or a coroutine suppressing cancellation cannot
be forcibly stopped safely inside Python; configure it as a stdio provider for a
physical termination boundary. Regex patterns run in a bounded worker process,
because stdlib regex itself cannot be preempted. Deterministic substring checks
remain local. Unknown/malformed provider events, duplicate terminal outcomes,
identity substitution, schema/type mismatches and invalid semantic outputs reject.

Git code checks associate observations with captured worktree/HEAD/content
fingerprints and perform a later freshness check. This is a best-effort stale
check, not an atomic workspace snapshot. Changes and reverts between observations
cannot be detected reliably without a host-provided immutable checkout/snapshot.
Separate worktrees avoid ordinary agent collisions. Tracked diff identities and untracked membership are rechecked too; filesystem
races and change/revert sequences still favor immutable candidates for
high-assurance checks.

Provider Binding provenance detects structural contradictions, not authenticity of
a binary, service, tool output or host. Coherently rewriting an entire record is
not detectable without an independent authenticated authority. The local-sha256
definition fingerprint is not a signature or portable canonical hash. Optional
Relay invocation annotations are not authenticated and are not independently
replayed by the VCP SDK. No stronger guarantee is advertised.
