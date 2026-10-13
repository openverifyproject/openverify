# Extensions

## NORMATIVE SEMANTICS

An extension object contains namespace, version, required (boolean), and data
(JSON value). Namespace MUST be a nonempty identifier containing a colon, such
as org.example:locator. No registry service is required.
Core fields MUST be strictly validated; unknown core fields MUST be rejected.
Unknown optional extension data MUST be preserved without interpreting its meaning.
A consumer unable to implement a required extension MUST report
EXTENSION_UNSUPPORTED. The reference SDK/engine has no extension capability
implementations and therefore rejects all required extensions.
Metadata remains arbitrary JSON annotations and cannot override core meaning.

## NON-NORMATIVE EXAMPLES

A range locator profile can add org.example:paragraph metadata.
Preserving it does not mean that the engine understands paragraph addressing.

## OPEN QUESTIONS

Full required/optional capability negotiation, namespace governance, and
interaction among extension versions are unresolved.

