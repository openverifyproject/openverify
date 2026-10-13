# Result and Decision

## NORMATIVE SEMANTICS

Result has protocol marker and disposition: EXECUTED, SKIPPED, DEFERRED, CANCELLED.
Executed attempts MUST have execution_outcome SUCCESS or ERROR. Nonexecuted
results MUST NOT have execution_outcome, applicability, determination, judgment,
verdict, score, or severity. SUCCESS MUST have applicability APPLICABLE or
NOT_APPLICABLE. ERROR MUST NOT carry those evaluation fields.
NOT_APPLICABLE MUST NOT carry determination, judgment, verdict, score, or severity.
Successful applicable evaluation MUST have determination KNOWN or UNKNOWN.
UNKNOWN MUST NOT carry judgment, verdict, score, or severity in the supported
draft subset: interpretation of partial judgments is OPEN.
KNOWN MAY carry typed structured judgment, binary verdict PASS/FAIL, normalized
score, or severity. They are optional independent observations; no default
mapping among them is implied.

Score MUST be a JSON number in [0,1]; 1 means stronger satisfaction and 0 stronger
violation. Severity is {domain, label}, referring to an ordered domain defined by
a profile, never a closed global enum. Evidence is a sequence, output is arbitrary
JSON information, usage is actual ResourceVector, and metadata/extensions are
available in every disposition. Scores are not required.

The standard flattened projection is partial:
executed SUCCESS/APPLICABLE/KNOWN with verdict -> that verdict;
executed SUCCESS/APPLICABLE/UNKNOWN -> UNKNOWN;
executed ERROR -> ERROR; SKIPPED -> SKIP.
A consumer MUST NOT invent a flattened status for other states.

Decision has protocol marker, kind CONTINUE, STOP_SUCCESS, STOP_FAILURE, ROUTE,
RETRY, or DEFER; ROUTE MUST have a nonempty destination and other kinds MUST NOT.
Optional reason, metadata, and extensions preserve supporting information.
Decision is not a judgment. Human review is an Evaluate implementation.

## NON-NORMATIVE EXAMPLES

An API failure is ERROR, an inconclusive judgment is UNKNOWN, and an admission
rejection is SKIPPED. These are independent meanings, not interchangeable labels.

## OPEN QUESTIONS

Flattened status for DEFERRED/CANCELLED/NOT_APPLICABLE and KNOWN without verdict;
partial judgments on UNKNOWN; and generic retry/defer scheduling remain open.

