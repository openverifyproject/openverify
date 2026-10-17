# Golden v4 contract inventory

Status: discovery in progress; NOT CERTIFIED.

Pinned production: `5f17f402a270882f244a54dde25eda92a085eb39`. Blueprint SHA-256: `3c73fee1826a65d7101c375d21421988a798ae6ee336824546b055ca92d5a6d2`.

D-001 is explicitly adjudicated by the user: retain all 53 declared identifiers; distinguish authority. The unchanged blueprint's 51-declaration row is corrected to 53 declarations, not 53 portable VCP requirements.

Schema roots independently counted: 24 VCP, 9 Provider.

The two SDK diagnostics are covered only at implementation boundaries. Error code membership does not establish exact error precedence.

| Identifier | Authority | Source references |
| --- | --- | --- |
| `ADMISSION_POLICY` | NORMATIVE_VCP | `src/openverify/error_codes.py:7-7`; `spec/draft/conformance.md:20-20` |
| `AGGREGATE_CONFIG` | NORMATIVE_VCP | `src/openverify/error_codes.py:8-8`; `spec/draft/conformance.md:21-21` |
| `AGGREGATE_INPUT` | NORMATIVE_VCP | `src/openverify/error_codes.py:9-9`; `spec/draft/aggregation.md:13-13`; `spec/draft/conformance.md:22-22` |
| `DATAFLOW_BINDING` | NORMATIVE_VCP | `src/openverify/error_codes.py:10-10`; `spec/draft/conformance.md:24-24` |
| `DATAFLOW_CONFIG` | NORMATIVE_VCP | `src/openverify/error_codes.py:11-11`; `spec/draft/conformance.md:25-25` |
| `DATAFLOW_SCHEMA` | NORMATIVE_VCP | `src/openverify/error_codes.py:12-12`; `spec/draft/conformance.md:25-25` |
| `EVIDENCE_EMPTY` | NORMATIVE_VCP | `src/openverify/error_codes.py:13-13`; `spec/draft/conformance.md:18-18` |
| `EXECUTOR_ERROR` | NORMATIVE_VCP | `src/openverify/error_codes.py:14-14`; `spec/draft/conformance.md:22-22` |
| `EXECUTOR_UNSUPPORTED` | NORMATIVE_VCP | `src/openverify/error_codes.py:15-15`; `spec/draft/conformance.md:22-22` |
| `EXTENSION_UNSUPPORTED` | NORMATIVE_VCP | `src/openverify/error_codes.py:16-16`; `spec/draft/conformance.md:20-20`; `spec/draft/extensions.md:11-11` |
| `GRAPH_DUPLICATE` | NORMATIVE_VCP | `src/openverify/error_codes.py:17-17`; `spec/draft/conformance.md:19-19` |
| `GRAPH_REFERENCE` | NORMATIVE_VCP | `src/openverify/error_codes.py:18-18`; `spec/draft/conformance.md:18-18` |
| `GRAPH_UNSUPPORTED` | NORMATIVE_VCP | `src/openverify/error_codes.py:19-19`; `spec/draft/composition.md:24-24`; `spec/draft/conformance.md:19-19` |
| `JUDGMENT_INVALID` | NORMATIVE_VCP | `src/openverify/error_codes.py:20-20`; `spec/draft/conformance.md:27-27` |
| `NO_OCCURRENCE` | NORMATIVE_VCP | `src/openverify/error_codes.py:21-21`; `spec/draft/execution-policy.md:76-76` |
| `OUTPUT_INVALID` | NORMATIVE_VCP | `src/openverify/error_codes.py:22-22`; `spec/draft/conformance.md:26-26`; `spec/draft/result.md:49-49` |
| `OUTPUT_MISSING` | NORMATIVE_VCP | `src/openverify/error_codes.py:23-23`; `spec/draft/conformance.md:26-26`; `spec/draft/dataflow.md:109-109` |
| `POLICY_ERROR` | SDK_SPECIFIC | `src/openverify/error_codes.py:24-24` |
| `POLICY_INPUT` | NORMATIVE_VCP | `src/openverify/error_codes.py:25-25`; `spec/draft/execution-policy.md:77-77` |
| `POLICY_OUTPUT` | NORMATIVE_VCP | `src/openverify/error_codes.py:26-26`; `spec/draft/execution-policy.md:78-78` |
| `POLICY_UNSUPPORTED` | NORMATIVE_VCP | `src/openverify/error_codes.py:27-27`; `spec/draft/conformance.md:23-23` |
| `PROFILE_DOMAIN` | NORMATIVE_VCP | `src/openverify/error_codes.py:28-28`; `spec/draft/conformance.md:21-21` |
| `PROTOCOL_JSON` | NORMATIVE_VCP | `src/openverify/error_codes.py:29-29`; `spec/draft/conformance.md:24-24` |
| `PROTOCOL_STRUCTURE` | NORMATIVE_VCP | `src/openverify/error_codes.py:30-30`; `spec/draft/conformance.md:17-17` |
| `PROTOCOL_VERSION` | NORMATIVE_VCP | `src/openverify/error_codes.py:31-31`; `spec/draft/conformance.md:17-17`; `spec/draft/wire-format.md:8-8` |
| `PROVENANCE_LINEAGE` | NORMATIVE_VCP | `src/openverify/error_codes.py:32-32`; `spec/draft/conformance.md:21-21`; `spec/draft/conformance.md:31-31`; `spec/draft/provenance.md:16-16`; `spec/draft/provenance.md:51-51`; `spec/draft/provider-binding.md:53-53` |
| `PROVIDER_BINDING_MISMATCH` | NORMATIVE_VCP | `src/openverify/error_codes.py:33-33`; `spec/draft/provider-binding.md:71-71` |
| `PROVIDER_BINDING_REQUIRED` | NORMATIVE_VCP | `src/openverify/error_codes.py:34-34`; `spec/draft/provider-binding.md:64-64` |
| `PROVIDER_MANIFEST_INVALID` | NORMATIVE_VCP | `src/openverify/error_codes.py:35-35`; `spec/draft/provider-binding.md:72-72` |
| `RESOURCE_MEASUREMENT` | NORMATIVE_VCP | `src/openverify/error_codes.py:36-36`; `spec/draft/conformance.md:19-19` |
| `RESULT_PROJECTION` | SDK_SPECIFIC | `src/openverify/error_codes.py:37-37` |
| `RESULT_STATE` | NORMATIVE_VCP | `src/openverify/error_codes.py:38-38`; `spec/draft/conformance.md:18-18` |
| `RUN_INPUT` | NORMATIVE_VCP | `src/openverify/error_codes.py:39-39`; `spec/draft/conformance.md:26-26`; `spec/draft/dataflow.md:38-38`; `spec/draft/execution-policy.md:11-11` |
| `SCHEMA_UNSUPPORTED` | NORMATIVE_VCP | `src/openverify/error_codes.py:40-40`; `spec/draft/conformance.md:25-25`; `spec/draft/dataflow.md:99-99` |
| `SEMANTIC_BINDING` | NORMATIVE_VCP | `src/openverify/error_codes.py:41-41`; `spec/draft/conformance.md:25-25` |
| `BINDER_FAILURE` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:7-7` |
| `CATALOG_FAILURE` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:8-8` |
| `CATALOG_INVALID` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:9-9` |
| `GATE_REJECTED` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:10-10` |
| `GRAPH_UNAVAILABLE` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:11-11` |
| `OPPORTUNITY_ID` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:12-12` |
| `PROVIDER_AMBIGUOUS` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:13-13` |
| `PROVIDER_CONFLICT` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:14-14` |
| `PROVIDER_UNTRUSTED` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:15-15` |
| `RUN_UNAVAILABLE` | RELAY_SPECIFIC | `src/openverify/relay/error_codes.py:16-16` |
| `CONTRACT_VERSION_UNSUPPORTED` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:8-8` |
| `CAPABILITY_UNAVAILABLE` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:9-9` |
| `CAPABILITY_VERSION_UNSUPPORTED` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:10-10` |
| `INVALID_INVOCATION` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:11-11` |
| `INVALID_CONFIG` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:12-12` |
| `INVALID_INPUT` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:13-13` |
| `INVALID_PROVIDER_OUTPUT` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:14-14` |
| `PROTOCOL_VIOLATION` | NORMATIVE_PROVIDER_CONTRACT | `provider-contract/spec/draft/errors.md:15-15` |

Counts: normative VCP 33; normative Provider Contract 8; SDK-specific 2; Relay-specific 10. These are declarations partitioned by authority; codes with identical spelling across layers remain separate entries.

Exact byte hashes and source ranges are retained in ERROR_INVENTORY.json and NORMATIVE_SOURCE_HASHES.json. Indexing is conservative and is not itself proof of obligation coverage. No historical Golden material is an oracle input.
