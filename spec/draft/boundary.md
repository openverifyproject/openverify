# Verification boundary

## NORMATIVE SEMANTICS

Verification observes, derives information, judges criteria, and controls
verification execution. It does not own arbitrary external business side effects.
Meaning, Knowledge, Computation, Composition, Execution Policy, Resources,
Result/Decision, and Provenance are inside the boundary.
Application actions, runtime implementation, external storage mechanism, model
implementation, and human workflow implementation are outside it.

The boundary argument is by question: what is to be established (Meaning);
what information exists (Knowledge); what operation is performed (Computation);
how operations relate in time (Composition); what event makes one eligible
(Activation); which subjects are included (Selection); should an eligible check
run now (Admission); what is required/consumed (Resources); what happened
(Result/Decision); how it relates across time (Provenance).
If a legitimate concern inside this declared boundary cannot be represented by
one of these questions, the model is incomplete. This is a falsifiable category
argument, not proof of complete wire syntax or implemented capabilities.

## NON-NORMATIVE EXAMPLES

ROUTE("human-review"), STOP_FAILURE, and CONTINUE control verification.
Refunding money, deploying software, stopping a factory, or publishing an article
are outside. A sensor implementation supplies observations; its measurement and
evidence are inside, while device maintenance is outside.

## OPEN QUESTIONS

No additional category gap has been established. The audit in
[conceptual-audit.md](conceptual-audit.md) separates representation from execution.

