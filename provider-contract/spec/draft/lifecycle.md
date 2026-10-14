# Lifecycle

Session: UNKNOWN -> INITIALIZED, following DESCRIBE/MATCH. No capability work may
begin before successful initialization. Invocation validation occurs before
acceptance: reject malformed/incompatible input without running work or emitting
events. Acceptance is the provider's commitment after validation to deliver one
terminal Outcome. There is no extra acceptance message; a pending invoke can
already be accepted before its first event, and its terminal response proves it.

Invocation: unseen -> accepted/running -> terminal. Rejected attempts never become
running. Each accepted attempt MUST emit exactly one Outcome. Zero events are
permitted. First event sequence MUST be 1; later sequences MUST strictly increase
(gaps are permitted; they imply no replay guarantee). Events MUST be delivered in
sequence order for their invocation. Different invocations may interleave.
Unknown correlation, duplicates/reordering, events after terminal, duplicate
outcomes, and invalid transitions are PROTOCOL_VIOLATION. Completed output MUST
validate against the matched output_schema; malformed output is
INVALID_PROVIDER_OUTPUT, never a verification FAIL.

CANCEL is a request, not a terminal state. A supported running cancellation
requests cooperative termination; the provider SHOULD stop promptly but there is
no timing guarantee. Repeat requests are permitted. A race may yield COMPLETED,
ERROR, CANCELLED, or DEADLINE_EXCEEDED. Only termination caused by a runner cancel
request yields CANCELLED. A cancel for a terminal attempt is an acknowledged no-op;
an unknown/rejected attempt is PROTOCOL_VIOLATION. An unsupported running cancel
is PROTOCOL_VIOLATION and does not end the invocation. CancelRequested remains
running until the Outcome. Internal provider failures use ERROR.

Deadline: the provider compares the supplied absolute UTC instant against its
local UTC clock. At acceptance it MUST check expiry; an already-expired but otherwise
valid request is accepted and ends DEADLINE_EXCEEDED without starting work. For an
active request it MUST monitor expiry, stop capability work at expiry, and commit
DEADLINE_EXCEEDED if no earlier terminal state was committed. It MUST NOT commit
COMPLETED at or after that instant. Cancellation/error committed before expiry may
win the race. A late request or delayed transport does not move the deadline.
Delivery of the terminal response can occur later; this is no bound on network,
stdio buffering, OS scheduling, shutdown latency, clock skew, or distributed clock
trust. Providers MUST reject deadlines if unable to enforce them. SDK validators
check supplied provider-clock observations; they do not execute work or timers.

Outcome meanings:

| state | meaning |
| --- | --- |
| COMPLETED | the operation completed successfully, not verification PASS |
| ERROR | the provider/execution failed to perform the operation |
| CANCELLED | the operation actually ended because of requested cancellation |
| DEADLINE_EXCEEDED | deadline expiry prevented completion |

Resource events/final usage transport observations, not estimation formulas.
Final usage is authoritative for that attempt; intermediate vectors are snapshots,
not additive deltas, and MUST NOT be summed with final usage automatically.
Dimensions may be partial; VCP units/kinds retain their meaning.

A lost process/transport cannot guarantee physical delivery of one Outcome. The
runner reports a transport failure separately and MUST NOT fabricate a provider
Outcome or a VCP FAIL. Exactly-once terminal emission applies to functioning
sessions, not exactly-once side effects, durable delivery, or recovery.

Portable lifecycle fixtures contain manifest, initialize, steps, and finish.
Steps are accept/invocation, event/event, cancel/request, outcome/outcome, each
with optional UTC `now` for provider-clock observation. finish true requires all
accepted attempts to be terminal; false describes a valid unfinished prefix.
With a deadline, accept/outcome require now. Validators reject premature
DEADLINE_EXCEEDED, late non-deadline Outcomes, unsolicited CANCELLED, and missing
terminal outcomes at finish. The trace harness is conformance data, not an RPC.
