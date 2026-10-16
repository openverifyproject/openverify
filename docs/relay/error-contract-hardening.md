# Error-contract hardening after the Golden 0.2.0 freeze

This implementation branch follows Golden freeze 5d62e2d and adapter commit
620b17f. It changes no frozen expectation, normative specification, reference
Engine source or pre-existing test.

Three independent string enums own their vocabularies: `VcpErrorCode` in
openverify.error_codes, `ProviderErrorCode` in openverify.provider_codes and
`RelayErrorCode` in openverify.relay.error_codes. Exceptions retain typed known
codes. ProviderError models type the eight reserved codes and preserve extensible
provider-namespaced strings. VCP's existing local SDK diagnostics POLICY_ERROR and
RESULT_PROJECTION are identified separately by registry consistency tests; they
are not new normative protocol codes.

Wire dictionaries explicitly convert codes to plain strings. Every existing code
spelling, message/path/details field and namespaced provider code is retained.
The exception constructors continue accepting existing string callers. Underlying
causes remain chained; structured boundary diagnostics retain their cause type
and message. No enum merges VCP, Provider and Relay categories.

Python wire dictionaries also accept StrEnum as its existing JSON string value,
so copying `error.code` directly remains compatible. Numeric enums and other
non-JSON Python values remain rejected; boolean/number distinctions are unchanged.

Two targeted correctness repairs accompany the types:

- Malformed custom policy outcomes now raise the existing normative POLICY_OUTPUT
  at the policy boundary. The original structured parsing error, including its
  path/details, remains in details.cause and exception chaining. This corrects the
  previous PROTOCOL_STRUCTURE classification at that boundary; clients relying on
  that incorrect classification will observe POLICY_OUTPUT.
- Catalog/Binder infrastructure failures now use Relay-only CATALOG_FAILURE,
  CATALOG_INVALID and BINDER_FAILURE. These replace unstructured Python exceptions
  where no error wire object previously existed. Existing structured protocol
  errors propagate unchanged. Conforming custom Sequence catalogs remain valid.

Store failure propagation and Observer isolation are unchanged. No FAIL, UNKNOWN,
ERROR, nonexecution, resource or graph scheduling meaning changes. Production
mutation testing and universal correctness of arbitrary custom ports are not
claimed. Frozen Golden failures and coverage gaps remain reported separately.

String enum inputs normalize to their underlying strings without invoking custom
display or equality methods. Normalization copies only changed containers and
does not mutate caller data.
