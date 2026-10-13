# JSON wire format

## NORMATIVE SEMANTICS

Semantics describes meaning; wire format describes interchange representation.
This draft's sole normative representation is UTF-8 JSON, with Draft 2020-12
JSON Schemas. Top-level Definition, Result, Decision, RunRecord, and standard
profile MUST have protocol: "draft". Other markers are PROTOCOL_VERSION errors.
Objects MUST reject unknown core fields except in explicit metadata, config,
Context, structured data, judgment schemas, and extension containers.
Duplicate mapping keys, NaN, Infinity, binary bytes, and non-JSON values MUST be
rejected. Explicit null in optional nullable fields is equivalent to absence.
Schema defaults are documentation, not automatic portable wire transformations.
Artifact references are preferred for external content; the core fetches nothing.

Schemas use URN ids under urn:verification:draft: independently of package name.
Local reference resolution MUST use shipped schemas, not network retrieval.
JSON Schema validity and semantic validity are distinct checks.
JSON Schema integer fields admit integral numeric values regardless of notation
(for example 1 and 1.0), excluding booleans and numeric strings.

## NON-NORMATIVE EXAMPLES

Python serializes with UTF-8, no nonfinite values, stable key ordering, and no
optional nulls. Its fingerprint is "local-sha256:" plus SHA-256 of sorted compact
JSON of that serialization. That is deterministic within this implementation,
NOT normative canonical JSON, cross-language hashing, or signing.
The SDK normalizes integral severity ranks to Python integers. Its provenance
comparison recursively distinguishes JSON types, with int/float sharing the JSON
number type. Numeric comparison uses parsed values, including the existing binary64
normalization of scores/measurements; it introduces no portable rounding guarantee.

## OPEN QUESTIONS

Canonical portable hashing requires exact number/string/Unicode/default handling;
it is unresolved. No signing standard or YAML semantics is implemented.

