# Computation

## NORMATIVE SEMANTICS

Derive produces INFORMATION, Evaluate produces a Result, and Control produces a
Decision. Aggregate is specialized Evaluate. Every kind has explicit typed inputs,
outputs, bindings and an exact provider-neutral operation requirement as specified
in [typed dataflow](dataflow.md). Information outputs may accompany Results or
Decisions; execution observations and usage remain separate from semantic outputs.

The exact input object contains only resolved declared ports. There is no injected
Context or predecessor-Results argument. Trusted local implementations are explicitly
registered; operation requirements never authorize imports or expressions.

## OPEN QUESTIONS

Provider discovery and selection are implementation responsibilities outside VCP
meaning. Relay v0.1 implements a trusted catalog and exact deterministic binding;
see [Relay architecture](../../docs/relay/architecture.md) for the non-normative runtime boundary.
