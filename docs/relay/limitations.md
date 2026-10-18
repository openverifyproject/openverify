# Implemented boundary and limitations

Protocol status is DRAFT. Relay v0.1 implements this checkout's exact VCP/Provider
Contract SDK/schema revision; the string "draft" alone does not promise stable
revision equivalence or stable 1.0 compatibility.

- Only finite acyclic graphs, all prerequisites and typed equality guards execute.
  Cycles, iteration, dynamic expansion and required unknown extensions reject.
- RETRY/DEFER end this occurrence; no invisible loop, durable scheduling or
  recovery is implemented. Inactive/unselected opportunities create no RunRecord.
- Control nodes form serial barriers. Ready waves wait for all members. This is
  conservative concurrency, not a claim of maximal throughput.
- Recorded host cancellation serializes the occurrence; multi-attempt concurrent
  cancellation provenance is an open VCP question. Task cancellation aborts the
  call and cleans up; no completed record is invented.
- In-process Python execution requires cooperative async providers. Use stdio
  for blocking/noncooperative code. Process lifecycle management is not isolation.
  Share a Relay across concurrent calls on one event loop; use separate instances
  across threads/event loops for providers that use asyncio synchronization.
- Stdio sessions are fresh per invocation, with no provider pooling, restart,
  replay or remote discovery. The supplied Python server helper does not accept
  deadline/budget constraints it cannot enforce.
- MemoryStore is volatile. JsonlStore is single-process, nontransactional local
  append/reload convenience; it does not promise fsync durability, multiprocess
  safety, retention policy, or database-backed recovery.
- Files/read output and stdio messages are bounded; use explicit artifact and
  resolver providers for larger inputs. External schemas are unsupported.
- Code fingerprints and freshness checks do not create atomic workspace snapshots.
  STAGED/UNSTAGED are scope observations; the shipped code graph checks worktree
  content with an explicit base, not hidden index/revision contents.
- The shipped deterministic text checker is not factual/semantic verification.
  No LLM, retrieval provider, Guardrails AI, theorem prover, OPA or Semgrep is
  bundled. Install actual external providers rather than treating regex as truth.
- Generic standard capabilities establish their documented properties. Custom
  subject/criterion meanings require appropriately configured honest providers.
- HTTP is a small localhost adapter, not a multi-tenant public service. MCP makes
  allowlisted graphs available, with no automatic host hooks.
- Validation detects contradictory lineage, not coherent forgery or provider
  honesty. Transport/policy identity annotations are optional, unauthenticated
  Relay metadata; normative graph bindings are preserved separately.

The work is available from this checkout. No package publication, deployment,
remote push, external infrastructure or stable release claim is part of it.
