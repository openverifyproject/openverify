# Draft specification

Protocol status: **DRAFT**. Implementation releases do not version protocol meaning.
The marker `protocol: "draft"` identifies this evolving wire draft; compatibility is
established against a particular repository revision and its conformance suite.

## NORMATIVE SEMANTICS

MUST / MUST NOT mean required for draft conformance.
SHOULD / SHOULD NOT mean recommended unless an implementation documents a reason.
MAY means optional. These words express ordinary requirements, not a decorative
reference to another standard.

Protocol prose is normative for meaning. JSON Schemas in schemas/draft are
normative for structural JSON validity. Semantic validation supplements them.
The Python implementation is one implementation, never the source of meaning.
A conforming consumer MUST distinguish malformed structure, invalid semantics,
and valid but unsupported execution capabilities.

Read in order: [boundary](boundary.md), [meaning](meaning.md),
[knowledge](knowledge.md), [typed executable dataflow](dataflow.md), [computation](computation.md), [result](result.md),
[aggregation](aggregation.md), [composition](composition.md),
[execution policy](execution-policy.md), [resources](resources.md),
[provenance](provenance.md), [extensions](extensions.md),
[wire format](wire-format.md), [conformance](conformance.md).
The engine subset is deliberately narrower than the conceptual model.

## NON-NORMATIVE EXAMPLES

A temperature envelope, prose criterion, and human categorical review share
these concepts while using different evaluators.

## OPEN QUESTIONS

See [open questions](open-questions.md). The draft makes no stable 1.0 promise.

