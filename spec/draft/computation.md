# Computation

## NORMATIVE SEMANTICS

Inside the boundary, an operation produces information, judgment, or a control
decision. Accordingly Derive: Information* -> Information*;
Evaluate: Context × prior Results -> Result;
Control: Context × Results -> Decision.
This output-type argument makes the three categories exhaustive within the
declared boundary; an operation with multiple kinds of output can be decomposed.

Aggregate: Result* × configuration -> Result is specialized Evaluate, exposed as
a convenient first-class graph node. It is not a fourth fundamental output type.
Regex, scripts, tools, model judges, humans, APIs, theorem provers, sensors, and
statistical tests are adapter implementations, not core semantic kinds.

Nodes contain id, kind (DERIVE/EVALUATE/CONTROL/AGGREGATE), executor_ref, config,
optional resource_estimate, metadata, and extensions. executor_ref identifies
a capability; it MUST NOT authorize dynamic imports or arbitrary expression
execution. Hosts explicitly register trusted implementations.

## NON-NORMATIVE EXAMPLES

Executor characteristics can be described in metadata: deterministic/probabilistic,
local/remote, human/machine, reproducible, trusted. They do not change node meaning.

## OPEN QUESTIONS

The reference Derive contract returns a Context update. Merge/order behavior
is engine-local: sequential updates replace named values. No portable conflict
resolution between parallel derives is specified.

