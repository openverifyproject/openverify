# Execution policy

## NORMATIVE SEMANTICS

Activation(explicit inputs) -> boolean asks whether an event makes verification
eligible. Selection(explicit inputs) -> SubjectSet asks which subjects are
included. Admission(explicit inputs) -> RUN | SKIP | DEFER
asks whether resources should be spent on an eligible selected subject.
These MUST remain distinct. Percentage sampling belongs to Admission.

Any policy consuming event, history, budget, risk, staleness or opportunity facts MUST declare typed inputs and explicit bindings (run/constant/external only) as in [dataflow](dataflow.md). Upstream graph outputs cannot feed pre-execution policy. The reference engine rejects custom policy inputs before invoking nodes. The simple built-ins consume their explicit definition configuration and host opportunity identity only.

execution_policy contains activation and selection capability references with
configuration, and admission. The standard implemented activation MANUAL means
the host explicitly invoked a run; EXPLICIT selection takes the one subject
identified in the definition. No global closed trigger/selector ontology exists.
Other capability names remain valid wire references, but the reference engine
rejects unsupported capabilities clearly.

ALWAYS admits every eligible selected opportunity.
PROBABILITY requires a finite number p in [0,1]. p=0 skips all, p=1 admits all;
otherwise roughly p of eligible opportunities are admitted by sampling.
Hosts MUST give a nonempty opportunity_id and subject identity for every run.
Reference deterministic sampling uses stable inputs, not global random state.
Its exact hashing is non-normative; identical admission across engines is OPEN.
A reference admission decision and reason MUST appear in RunRecord.

maximum_staleness conceptually ensures that probability does not leave a verifier
unevaluated indefinitely. It is not in the implemented wire policy; consumers
MUST NOT accept it as an unnoticed extra field.

## NON-NORMATIVE EXAMPLES

Changed documents, impacted measurements, random subject sets, and explicit IDs
are selection. Events such as periodic ticks are activation. Resource budgets
and history may influence admission. No PERIODIC scheduler is implemented.

## OPEN QUESTIONS

MAX_STALENESS timing, history coverage, missing-history behavior, and combination
with probability need precise semantics; not implemented. Cross-engine sampling
identity and retry/opportunity identity are unresolved.

