# Resources

## NORMATIVE SEMANTICS

ResourceVector is an open mapping from dimension identifier to measurement.
Each measurement contains unit and kind EXACT, ESTIMATED, RANGE, or UNKNOWN.
EXACT/ESTIMATED require a finite nonnegative value. RANGE requires finite
nonnegative minimum and maximum with minimum <= maximum. UNKNOWN has no value
or bounds. Other kind-dependent numeric fields MUST be absent.
ResourceDimension describes id, unit, description, metadata, and extensions.
Units are explicit; incompatible units MUST NOT be summed implicitly.
Custom identifiers and units are permitted; the core does not prescribe conversion.

ResourceEstimate precedes execution; ResourceUsage records actual consumption.
Node resource_estimate and Result/RunRecord usage distinguish them.
A reference engine MUST retain adapter usage and record its own duration
separately in node usage. The reference wall_time measurement is EXACT seconds
measured by a monotonic clock; it does not claim physical clock precision.

The standard profile describes wall_time, money, input_tokens, output_tokens,
cpu_time, gpu_time, human_time, network_bytes. Money uses an explicit currency
unit supplied by the measurement, not a hidden universal currency.

## NON-NORMATIVE EXAMPLES

Energy and API_calls are custom dimensions. INSTANT/FAST/NORMAL/DEEP/BACKGROUND
could be scheduler hints; they are not the resource model and are not built-ins.

## OPEN QUESTIONS

Probability distributions and automatic unit conversions are outside this draft.

