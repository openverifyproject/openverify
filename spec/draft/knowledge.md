# Knowledge

## NORMATIVE SEMANTICS

Context is available structured information: a mapping of names to JSON values.
ArtifactRef contains id, type (media/type identifier), locator, optional schema_id,
metadata, and extensions. Its locator is an opaque structured value identifying
external content; implementations MUST NOT assume it contains artifact bytes or
automatically fetch it. Hosts supply content through Context.

Evidence contains optional id, nonempty message, artifact_ref, locator,
structured_data, metadata, and extensions. At least one of message, artifact_ref,
locator, or structured_data MUST be non-null; id and metadata alone do not count.
Empty structured mappings/sequences remain meaningful data. Empty messages do not.

Locator semantics are profile/extension-owned and opaque to core. Fundamental
Evidence properties MUST NOT encode code-specific paths or line numbers.

## NON-NORMATIVE EXAMPLES

Locators can identify character ranges, paragraphs, PDF pages/regions,
spreadsheet ranges, image regions, audio intervals, JSON Pointers, database row
keys, or execution events.

## OPEN QUESTIONS

Resolution, integrity, availability, and access control for external artifacts
are host concerns; this draft does not define a resolution transport.

