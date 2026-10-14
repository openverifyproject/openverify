# OpenVerify Provider Contract

**Status: DRAFT. Contract version: "0.1".** No stable compatibility promise.

One open, language-neutral contract lets a runner invoke an independently
implemented capability. Provider authors implement it once, instead of writing
an adapter for every runner. Capabilities can verify, execute, evaluate policy,
estimate resources, analyze dependencies, or perform future kinds of work.

```text
                         VCP
              verification semantics
                          |
                          v
                        RUNNER
                  Provider Contract
              +-----------+-----------+
              v                       v
          Provider A              Provider B
              |                       |
         arbitrary work          arbitrary work
```

VCP defines what verification means. This contract defines invocation and runtime
interoperability below VCP. OpenVerify Relay is a planned runner implementing both;
it does not exist yet. Competing runners use the exact same public contract and
providers. There is no private OpenVerify provider path.

```text
DESCRIBE -> MATCH -> INVOKE -> EVENTS / CONTROL -> OUTCOME
```

Every interaction within this boundary occurs before work, when work starts,
while work exists, or when work ends. Portable interoperability therefore needs
exactly six pieces: Manifest, compatibility/versioning, Invocation, Events,
Control, and Outcome. This is a lifecycle coverage argument, not a mathematical
claim about all possible systems. Verification meaning remains VCP; provider
internals remain provider-specific; selection remains runner policy; delivery
mechanics belong to transport bindings.

A tool implementing this contract directly needs no OpenVerify adapter. Legacy
software such as pytest needs one Provider Adapter, reusable by every compatible
runner. The current reference Engine's in-process adapters are separate existing
interfaces; this task does not change them or implement tool adapters.

Read [overview](spec/draft/overview.md), [lifecycle](spec/draft/lifecycle.md),
[capabilities](spec/draft/capabilities.md), [wire format](spec/draft/wire-format.md),
[versioning](spec/draft/versioning.md), [errors](spec/draft/errors.md), and
[transports](spec/draft/transports.md). Prose defines meaning; Draft 2020-12
[schemas](schemas/draft/) define structure; [conformance](conformance/manifest.json)
tests both. None requires Python. [Open questions](spec/draft/open-questions.md)
mark deliberately unsupported behavior.

The optional `openverify.provider` SDK supplies typed wire objects, parsing,
validation, lifecycle checking, and a stdio framing/session validation binding.
It supplies no runner, process launcher, scheduling, selection, or tool providers.

To check the portable suite with this implementation:

```python
from pathlib import Path
from openverify.provider.conformance import check_manifest

assert check_manifest(Path("provider-contract/conformance")) == []
```
