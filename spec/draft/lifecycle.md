# Occurrence and node lifecycle

## NORMATIVE SEMANTICS

Only activated, selected opportunities with valid admission outcomes are
occurrences; see [execution policy](execution-policy.md). Every node has exactly
one terminal record, including nodes that never execute.

Logically a node is PENDING until all incoming prerequisites are terminal, READY
when policy/routing/guards/required inputs permit execution, RUNNING when the
runner starts an attempt, then TERMINAL. Pending/ready nodes may become terminal
without starting. This is not a new wire enum. Terminal record states are
SUCCESS, ERROR, NONEXECUTED, and CANCELLED (an interrupted attempt).

Invoked Evaluate/Aggregate implementations MUST return EXECUTED with SUCCESS or
ERROR. Returning SKIPPED/DEFERRED/CANCELLED is invalid graph output and becomes
EXECUTED/ERROR. Standalone Result interchange and direct reducers may still use
all dispositions. Successful Derive/Control retain information/Decision without
a fabricated evaluation Result. NOT_APPLICABLE means evaluation ran and found
no applicable criterion; UNKNOWN means it ran without determining an answer.
FAIL is a known judgment; exceptions/output rejection are EXECUTED/ERROR.
None of those states represents nonexecution. Nonexecuted/cancelled Results contain no evaluation fields
or successful evaluation evidence. Diagnostic output and incurred usage remain
possible. Cancelled attempts publish no accepted information or Decision.

Runner-synthesized nonexecution has stable NodeRecord.reason codes, repeated in
Result.output.reason:

| Cause | Disposition | Reason |
| --- | --- | --- |
| Admission SKIP | SKIPPED | ADMISSION_SKIP |
| Admission DEFER | DEFERRED | ADMISSION_DEFER |
| Explicit cancellation prevents or interrupts work | CANCELLED | CANCELLATION |
| STOP_SUCCESS / STOP_FAILURE | SKIPPED | CONTROL_STOP |
| Control DEFER | DEFERRED | CONTROL_DEFER |
| Control RETRY | SKIPPED | RETRY_REQUESTED |
| Excluded route branch | SKIPPED | ROUTE_EXCLUDED |
| False/unavailable guard operand | SKIPPED | GUARD_FALSE |
| Required input unavailable/invalid | SKIPPED | INPUT_UNAVAILABLE |

CONTINUE changes no eligibility. STOP_SUCCESS/STOP_FAILURE intentionally end
further work without synthesizing a verification verdict. DEFER prevents further
work in this occurrence. RETRY ends the local pass and records its Decision;
no scheduling or new occurrence is implied.

ROUTE MUST name a direct outgoing execution successor of that Control. Exclude
other successors and their descendants except nodes also reachable from the
selected successor (shared joins). Independent work outside those branches stays
eligible. Exclusions accumulate and cannot be undone. Routing never bypasses
prerequisites/guards. All incoming guards must hold. Ordinary false guards do not
implicitly disable unguarded descendants: explicit RESULT bindings may inspect
nonexecution, while unpublished information remains unavailable.

Precedence for an unstarted node is admission non-RUN, cancellation already
observed, earlier terminating control, route exclusion, false guard, blocked input.
Occurrence DEFER/cancellation therefore never collapses into INPUT_UNAVAILABLE.
Completed terminal records never change retroactively.

## Cancellation

Cancellation is an explicit host decision/event, distinct from failed, unknown,
skipped or deferred. RunRecord.cancellation identifies the first affected node,
phase BEFORE_START or RUNNING, and host reason. It is legal only in admission RUN.
BEFORE_START makes that and subsequent unstarted nodes NONEXECUTED/CANCELLED.
RUNNING makes the affected node state CANCELLED with a CANCELLED Result; later
nodes are NONEXECUTED/CANCELLED. Earlier terminal records remain unchanged.
Cancellation cannot be inferred from a provider Result.

The sequential engine accepts a host Cancellation token, checked before attempts
and immediately after invocation, before accepting outputs. Exceptions during a
cancelled invocation still yield CANCELLED. Cancellation after the final terminal
transition has no effect. This is cooperative and cannot preempt blocking code.
Interrupted attempt observations/usage may be retained but cannot become accepted
evaluation/information. No distributed cancellation system is defined.
