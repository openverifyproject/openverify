# Overview

Status: DRAFT. Contract version: "0.1". MUST/MUST NOT express requirements;
SHOULD recommendations; MAY optional behavior. Prose and schemas are normative.
Python convenience types are not normative.

The contract answers: how can a runner use a capability implemented by software
it did not build? Its objects describe, match, invoke, observe, control, and end
one attempted operation. An accepted invocation MUST have exactly one Outcome.

The contract MUST NOT redefine Subject, Criterion, PASS/FAIL/UNKNOWN, Evidence,
composition, provenance, admission, or aggregation. Those remain in
[VCP](../../../spec/draft/README.md). A successful SMT execution returning SAT has
Outcome COMPLETED. Whether that observation supports PASS or FAIL belongs to the
VCP definition. Provider ERROR MUST NOT automatically become VCP FAIL.

Provider discovery and selection are outside the contract. Configuration, PATH,
package metadata, containers, or endpoints can supply a provider. Cheapest,
fastest, local-first, vendor preference, random choice, and organization policy
are runner decisions. The Manifest describes a provider once found.

The public contract is the entire interoperability surface for future Relay and
competing runners. Direct implementations need no adapter; legacy tools need one
contract adapter per tool, reusable across runners. No Relay or legacy provider
adapter is implemented here.
