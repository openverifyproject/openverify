# Aggregation

## NORMATIVE SEMANTICS

Aggregate: Result* × Config -> Result is logically general because of its
signature, not because a list of reducers exhausts possible aggregation.
The standard draft supplies ALL, ANY, MAJORITY, MIN_SCORE, MAX_SCORE, AVERAGE,
WEIGHTED_AVERAGE, WORST_SEVERITY. Its executor_ref is standard.aggregate.

Every invocation MUST provide reducer and handling. handling is a mapping
with keys UNKNOWN, ERROR, SKIP, DEFERRED, CANCELLED, NOT_APPLICABLE, MISSING.
Every key MUST have REJECT or IGNORE. No hidden default is permitted.
REJECT makes the reference aggregator raise AGGREGATE_INPUT (the engine records
an ERROR). IGNORE excludes that input. Neither invents a satisfaction value.
Known logical inputs require verdict; numeric inputs require score; severity
inputs require severity. Absent required value uses MISSING handling.
A KNOWN result with no binary verdict is not UNKNOWN.
Empty input, including empty after filtering, MUST be rejected.

ALL passes iff all retained verdicts PASS. ANY passes iff at least one PASS.
MAJORITY passes iff PASS count exceeds FAIL count, fails iff FAIL exceeds PASS.
A tie is rejected: tie resolution is not specified.
Numeric reducers produce KNOWN score without implying verdict. MIN/MAX select
extrema; AVERAGE is arithmetic mean. WEIGHTED_AVERAGE requires one finite
nonnegative weight per original input and positive retained weight total;
filtering preserves original positions. Zero total MUST be rejected.
WORST_SEVERITY requires an explicit severity_domain {id, levels}, whose labels
are unique, nonempty and have distinct integer ranks; higher rank is worse.
Inputs MUST refer to that domain and labels in it. Output contains its greatest
ranked severity without implying verdict. All output Results are successful,
applicable, KNOWN; evidence from retained inputs is concatenated in input order.

## NON-NORMATIVE EXAMPLES

Security may want ERROR -> fail closed, UNKNOWN -> escalation, and required
SKIP -> failure. Style may ignore exceptional inputs. This profile implements
REJECT/IGNORE only. Other policies can be explicit Evaluate adapters; core does
not silently turn UNKNOWN into 0.5 or ERROR into 0.
Escalation is a Control decision rather than a synthetic score.

## OPEN QUESTIONS

Portable fail-closed/warning/escalation aggregation policies and majority ties
are not implemented. No general policy language is defined.

