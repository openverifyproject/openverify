# Meaning

## NORMATIVE SEMANTICS

Every verification requires a Subject and Criterion. Subject identifies what is
being examined; Criterion identifies the property to establish.
Selection MUST remain distinct from Criterion.

A portable VerificationDefinition MUST contain protocol marker, id, version,
subject (ArtifactRef), criterion (id and description), judgment_schema, graph,
run_inputs, and execution_policy. Optional satisfaction_mapping describes a mapping's identity
or configuration; execution remains adapter-owned. Metadata and extensions carry
additional information. Explicit id/version and a reference-only fingerprint
identify definition evolution in provenance.

Criterion metadata describes and identifies a criterion; it is not an expression
language. Evaluate adapters execute criteria. judgment_schema is a JSON Schema object or boolean describing judgments when present. A definition consumer MUST verify it
is a valid Draft 2020-12 schema. The reference engine MUST validate emitted
judgments against it. External or unresolved schema references invalidate a definition up front; schemas use the self-contained subset in [dataflow](dataflow.md). Evaluate semantic ports bind the definition subject and criterion explicitly.

## NON-NORMATIVE EXAMPLES

Subject: a text artifact. Criterion: absence of a phrase pattern.
Subject: a measurement set. Criterion: readings within an envelope.

## OPEN QUESTIONS

Portable formal criterion expressions and satisfaction-mapping execution are not
defined. Definitions can describe mappings; core does not derive verdicts from them.

