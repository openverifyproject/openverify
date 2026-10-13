# Changelog

## 0.1.0 - Initial draft

### Protocol draft changes

Domain-neutral semantics, strict JSON schemas, standard profile, and conformance cases.
Protocol remains DRAFT; unresolved public semantics are listed in open questions.
Clarified admission-SKIP and JSON-type-preserving provenance invariants, integral
severity ranks, and UTC timestamp forms. Weighted graph aggregation is unsupported
pending explicit predecessor input/weight identity; ordered direct reducers remain
supported.

### Python SDK changes

Typed values, strict validation, serialization, inspection, reference-only fingerprints.
Offline packaged schemas/profile, stable error objects, partial flattened projection,
and UTF-8-safe JSON serialization preserving optional extension data.

### Reference engine changes

Local DAG execution, registered adapters, explicit aggregation handling,
probability admission, and serializable provenance.
Registered local demo adapters, mock escalation, per-node wall time, memory/JSONL
stores, and exact intermediate arithmetic for reference means. No distributed runtime.

