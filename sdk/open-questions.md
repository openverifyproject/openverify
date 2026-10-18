# SDK integration questions (non-normative)

The user explicitly prohibited changes to normative specs, including the draft
open-questions file. These observations are recorded here for a later spec review;
this file does not resolve them or redefine the protocol.

1. `spec/draft/result.md` specifies Decision's destination invariant, while
   `spec/draft/conformance.md` lists no dedicated Decision invariant error code.
   The new wire libraries reject these cases with local `PROTOCOL_STRUCTURE`.
   Shared fixtures require rejection without asserting a normative Decision code.
   The existing Python SDK uses `RESULT_STATE`. This difference is documented;
   it is not used to infer or change protocol meaning.
2. The existing Python standalone Invocation parser accepts an unknown
   `vcp_version`; Provider Contract versioning prose requires `draft` in that
   standard field. Its contextual lifecycle validation is a separate boundary.
   The new SDKs reject the standalone object with `INVALID_INVOCATION`. The
   compatibility audit records the existing parser case as an expected failure.
   No production Python/Relay source is changed by this task.
   Integration update: the finalized production parser now rejects the unknown
   marker with `INVALID_INVOCATION`. The compatibility audit no longer has an
   expected-failure escape for this case. The original observation remains
   historical evidence for the SDK branch's production baseline.
3. Portable exact numeric representation, canonical hashing and cross-language
   normalization remain open in the normative draft. SDKs preserve supported JSON
   values and reject values outside their faithful native range. This bounded
   suite is not proof of exhaustive arbitrary-precision interoperability.
4. The `draft` VCP marker alone does not identify a compatible revision. Packages
   therefore expose the exact source commit as SDK metadata; this does not add
   a new normative wire field or version-negotiation mechanism.

Full graph/provenance semantic validation, field-by-field native model generation
and Provider lifecycle/transport support are implementation gaps, not unresolved
protocol decisions. They are listed separately in the README/report.
