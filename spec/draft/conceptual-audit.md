# Conceptual exhaustiveness audit

## NORMATIVE SEMANTICS

This read-only conceptual audit adds no semantics. An inside-boundary concern that
fits none of the categories would disprove the boundary's category claim.
Category representation is distinct from implemented wire and execution support.

## NON-NORMATIVE EXAMPLES

### A. Writing: phrase rejection, 20% sampling, daily minimum, uncertain human review

| Concern | Mapping |
| --- | --- |
| Meaning | Subject is an article; Criterion is absence of phrase pattern X. |
| Knowledge | Typed text run input, artifact identity, matching-span Evidence. |
| Derive | Extract or normalize text information. |
| Evaluate | Phrase check, uncertainty-producing check if needed, and human judgment. |
| Control | Route uncertain Results to human review. |
| Composition | Dependencies and destination guards link evaluation and review. |
| Activation | Host submission event; daily ticks need a host scheduler. |
| Selection | Candidate drafts, independently of their phrase criterion. |
| Admission | PROBABILITY p=0.20; daily minimum needs maximum-staleness/history semantics, OPEN. |
| Resources | Estimated/actual machine and human time. |
| Result | Known PASS/FAIL; uncertainty remains UNKNOWN. |
| Decision | ROUTE("human-review"); host communicates with reviewers. |
| Provenance | Definition/text identity, opportunities, evidence, reviewer/executor and times. |

The prose example exercises Derive/checks/ALL. Daily minimum fits admission but
cannot currently execute portably. Claiming this entire sentence is implemented
would be false; no new semantic category is needed to identify that gap.

### B. AI: three model judges, deterministic rule, score aggregation, disagreement

| Concern | Mapping |
| --- | --- |
| Meaning | AI output subject; criterion identifies the quality/property. |
| Knowledge | Output, prompt/context artifacts, judge observations and Evidence. |
| Derive | Extract information used by checks. |
| Evaluate | Three model adapters, deterministic rule, and score Aggregate. |
| Control | Inspect Results and route disagreement for further verification. |
| Composition | Independent judges converge on Aggregate/Control; guarded escalation. |
| Activation | New output or explicit host invocation. |
| Selection | Output identities from a host candidate universe. |
| Admission | ALWAYS, probability, or explicit resource/history policy. |
| Resources | Input/output tokens, explicit currency, wall time, open dimensions. |
| Result | Optional known scores/judgments or UNKNOWN/ERROR under explicit reducer handling. |
| Decision | ROUTE to another evaluator; publishing is outside. |
| Provenance | Definition/subject, executor/version when known, upstream Results, usage, time. |

Disagreement thresholds and calibration are criterion/adapter configuration; core
does not invent them. The mock example demonstrates uncertainty routing, not actual
provider integration. Scores need explicit missing/error handling.

### C. Physical measurement: temperature envelope, sensor evidence, unavailability

| Concern | Mapping |
| --- | --- |
| Meaning | Reading-set subject; stated envelope criterion. |
| Knowledge | Readings/units, sensor artifact/event references, calibration annotations. |
| Derive | Trusted extraction/conversion with explicit supplied units. |
| Evaluate | Envelope judgment; availability information may be separate. |
| Control | DEFER indicates waiting for sensor availability. |
| Composition | Availability precedes evaluation; guards control eligibility. |
| Activation | Measurement event supplied by a host capability. |
| Selection | Sensor/reading identities or chosen interval. |
| Admission | Host can choose DEFER for unavailability; reference built-ins do not implement this. |
| Resources | Energy, calls, elapsed time with explicit units. |
| Result | Known judgment, nonexecuted DEFERRED attempt, or ERROR for adapter failure. |
| Decision | DEFER serializes; host manages rescheduling/device repair. |
| Provenance | Sensor/input identity, evidence, criterion version, availability reason, times. |

The numerical example implements the range judgment. Local Control can record
DEFER and stop but provides no sensor driver or scheduler. No implicit unit
conversion or treatment of missing readings is defined.

### D. Human review: categorical document judgment with evidence

| Concern | Mapping |
| --- | --- |
| Meaning | Document subject and categorical review criterion. |
| Knowledge | Document reference, explicit reviewer inputs, localized Evidence. |
| Derive | Optional document-information extraction. |
| Evaluate | Human implementation returns a category matching judgment_schema. |
| Control | Route to review, continue, or stop based on Results. |
| Composition | Review dependencies/guards; asynchronous human workflow is external. |
| Activation | Explicit review request or host event. |
| Selection | Document identity distinct from criterion. |
| Admission | Spend reviewer time under host policy; ALWAYS available locally. |
| Resources | Human time, wall time, actual currency. |
| Result | SUCCESS/APPLICABLE/KNOWN category and Evidence; verdict optional. |
| Decision | CONTINUE/STOP/ROUTE; category is distinct from workflow decision. |
| Provenance | Reviewer/executor when known, definition/document version, evidence, times. |

Categorical judgment without a satisfaction mapping need not have PASS/FAIL or a
score. Its flattened projection is intentionally undefined. Communication and
reviewer identity assurance belong to the host mechanism.

### E. External service: artifact validation and occasional API errors

| Concern | Mapping |
| --- | --- |
| Meaning | Artifact subject and externally checked property. |
| Knowledge | Artifact reference, explicit request inputs, response/evidence annotations. |
| Derive | Optional request preparation or response-information extraction. |
| Evaluate | Trusted API adapter normalizes successful judgment or failed execution. |
| Control | Decide escalation, stop, retry, or defer after Results. |
| Composition | API dependencies and simple Result/Decision guards. |
| Activation | Host request or externally supplied event. |
| Selection | Artifact identities from a candidate universe. |
| Admission | ALWAYS, probability, or another host capability. |
| Resources | Calls, bytes, time, currency; estimate distinct from usage. |
| Result | ERROR differs from successful FAIL or UNKNOWN. |
| Decision | RETRY/DEFER serialize; transport retries and scheduling remain external/open. |
| Provenance | Definition/artifact/input identity, dependencies, executor/version, error, usage, time. |

No API integration exists. Failed-adapter regression tests exercise normalization
and provenance locally. Service-specific acceptance mappings belong to criterion
and adapter, not an undocumented global conversion.

## OPEN QUESTIONS

No missing top-level category was established. These examples expose existing
limits: maximum-staleness/history coverage, dynamic composition, portable sampling,
retry/defer scheduling, and satisfaction mappings. See [open questions](open-questions.md).
This audit does not prove complete syntax, all-domain execution, or the truth of any
particular judgment.
