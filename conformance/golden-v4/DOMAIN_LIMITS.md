# Declared limits

UNSUPPORTED: cycles, dynamic expansion, external/nested/dynamic schema resolution,
automatic retries, durable replay/recovery, required unknown extensions, remote
Provider transports, multi-attempt recorded cancellation and universal host API
feature parity. Check rejection only where specified.

EXCLUDED: Byzantine providers, malformed external events in real Relay, malicious
replacement ports, provider attestation and coordinated consistent record forgery.
Local malformed objects remain cheap rejection cases.

UNBOUNDED: JSON payloads, strings, schemas, numeric precision, graph sizes above
four, member lengths, event histories, custom provider/policy logic and scheduling
histories. Finite partitions and samples do not establish arbitrary-domain proof.

SAMPLED: logical reducer sequences through length five; severity through length
four; numeric extrema/means over explicit authored boundaries. Larger domains have
UNPROVED residuals in REDUCTION_LEDGER.jsonl.

CONDITIONAL: raw availability coordinates require port requiredness, producer
role, target schema, ancestor relation and trace. They are coordinate-space checks,
not a universal V/I/N split. Missing normative clause-to-assertion reviews are
MISSING coverage and prevent certification.

AMBIGUOUS: exact error precedence is asserted only when mandated. Source-supported
rejection categories whose precedence is not fixed are checked as rejection only.
Portable numeric rounding, canonical identities and clock trust remain open.
