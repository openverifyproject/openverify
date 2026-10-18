# Open questions

Status: DRAFT. These are deliberately unsupported, not inferred from SDK behavior.

| question | DRAFT 0.1 boundary |
| --- | --- |
| Capability compatibility beyond exact versions | Exact ID/version only; no ranges |
| Mandatory extension negotiation | Optional annotation maps only; requiring unnegotiated semantics is rejected |
| Remote/network bindings | Standard stdio only |
| Authentication and authorization | Deployment concern; no portable handshake |
| Provider trust/signing and namespace ownership proof | No trust system or registry |
| Resumable invocation, checkpoint, migration | New attempt only; CANCEL is the sole control |
| Event replay/durable delivery | Ordered live events; no replay or delivery guarantees after loss |
| Discovery registries | Discovery is outside the contract |
| Portable VCP draft revision identity | Existing draft marker plus agreed specification revision; no VCP redesign |
| Numeric canonicalization and extreme precision | JSON types preserved; no canonical signing or arithmetic profile |
| Clock trust, adjustments, and leap seconds | Local UTC observation only; observed expiry is irreversible; leap-second notation unsupported |
| Richer capability schema resolution | Local pointers within one root resource only; no nested IDs, anchors, or external fetching |
| Hard resource isolation and budgets across remote subprocesses | Accept only constraints a provider can enforce; no isolation implementation |

This contract does not decide provider selection, estimator formulas, VCP
interpretation, cache equivalence, or scheduling. Those are outside its boundary.
