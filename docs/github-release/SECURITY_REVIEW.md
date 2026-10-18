# Pre-upload security and repository review

Scope: the release branch's reachable Git history and tracked source tree. Other worktrees and untracked attachments were not imported. This is a secret-detection and repository hygiene review, not a full application penetration test or dependency vulnerability certification.

## Findings

**No committed credential or private key was confirmed.** Gitleaks 8.30.1 was downloaded from its official GitHub release and its archive checked against the published SHA-256 list. Windows archive SHA-256: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`.

The initial Git-patch history scan reported six generic-api-key candidates. Each was reviewed:

| Candidate path | Classification | Evidence |
|---|---|---|
| `conformance/golden-v4/release-review-v0.1/SOURCE_HASHES.json:112` | False positive | Value is SHA-256 of the historical `src/openverify/relay/api.py` content |
| `conformance/golden-v4/verification-final/EXECUTION_REPORT.json:49` | False positive | Same independently verified source-content digest |
| `conformance/golden-v4/NORMATIVE_SOURCE_HASHES.json:118` | False positive | Same source-content digest, not an API credential |
| `tests/golden_v4/integration.py:139` | False positive | Local ASGI HTTP test arguments; token is an authored test-only literal, not an external service account |
| `conformance/golden-v0.3.1/implementation-sources.json:45` | False positive | Source-content digest matching historical `relay/api.py` bytes |
| `conformance/golden-v0.3/implementation-sources.json:45` | False positive | Same source digest; identical historical JSON blobs share content identity |

To cover binary/archive content that a Git patch can omit, every unique reachable Git blob was also exported by object ID and scanned, with archive and decoding depth two. This second scan covered 1,498 blobs / 355,008,635 stored bytes at `b992b92`; it reported five overlapping candidates, all explained by the table. Export names were mapped back to source paths. No scanner exclusion or blanket secret-rule suppression was introduced. The raw reports are redacted; scan findings are not blindly treated as real secrets or silently ignored.

The published source also retains historical machine paths (including the local Windows username) and Git author identity. These are privacy metadata, not credentials. Review whether you want these details public before the manual push. Preserving original audit files and history precludes silently rewriting them. No history rewrite or redaction was performed.

## Tracked-file hygiene

No tracked `.worktrees`, `.pytest_cache`, `.venv`, `node_modules`, `vendor`, Rust target, .NET obj, or Python bytecode cache was found. No credential-named `.env`, `.netrc`, `.pypirc`, private-key or Composer auth file was tracked. The root ignore policy now also excludes worktrees, local environments, common credential files and signing material. Ignore rules do not remove already committed data; history was checked separately.

Golden stimuli, bundled normative schemas, shared fixtures and review evidence are intentional generated artifacts, not disposable caches. They remain present, with historical freezes preserved. Three reachable blobs exceed GitHub's 50 MiB warning threshold:

- `conformance/golden-v4/RUN_EVIDENCE/results.jsonl`: 76,613,747 bytes.
- `conformance/golden-v4/CASES.jsonl`: 66,487,390 bytes.
- `conformance/golden-v4/OBLIGATIONS.jsonl`: 55,209,297 bytes.

No reachable blob exceeds GitHub's 100 MiB hard limit. Use Git push, not the browser file uploader. No LFS migration, file deletion or history rewrite is needed for the observed sizes. [GitHub's size limits](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

## Workflow boundaries

Project and SDK PR jobs have `contents: read`, no registry secrets and no publishing step. Checkout credentials are not persisted. Every external action is pinned to a full commit ID, with the resolved upstream ref documented beside it. Only npm, PyPI wire and RubyGems publication jobs request `id-token: write`; other registry jobs use narrowly scoped environment secrets. Publication requires a matching per-language tag and environment ownership variable. No `pull_request_target` workflow is used. [GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use).

Release environment protection and tag-creation restrictions are owner settings, not guarantees provided by YAML. In particular, pushing a Go module tag already publishes that Git version; a later environment review cannot undo its visibility. The PHP token must be restricted to the dedicated distribution mirror, not this source repository.

All scan reports, archive checksums and repository-shape evidence are linked from the handoff verification records. Rule-based scanning cannot prove absence of every possible credential, encrypted payload or sensitive fact. No network authentication token, registry secret, private signing key or authenticated account configuration was added by this preparation.

## Dependency advisory found during verification

The original Node lockfile selected Ajv 8.17.1. `npm audit` reported moderate
[GHSA-2g4f-4pwh-qvx6 / CVE-2025-69873](https://github.com/advisories/GHSA-2g4f-4pwh-qvx6),
which concerns the optional `$data` facility. This SDK does not enable `$data`,
but retaining the vulnerable dependency floor was unnecessary. Its manifest now
pins Ajv `8.20.0`, and the lockfile selects 8.20.0. The subsequent npm audit
reports zero advisories. Node native tests, both package builds and its clean
consumer are rerun for that change; their final result is retained separately
from the initial run. No fixture expectation or validator option was weakened.

This is a measured npm audit result, not a dependency-vulnerability certificate
for all eight ecosystems. Owner-side dependency alerts should remain enabled.
