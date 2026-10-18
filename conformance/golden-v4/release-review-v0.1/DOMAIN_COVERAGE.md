# Mathematical evidence and limits

This is a review of existing domains, not a new inventory. Candidate projections overlap; there is no summed candidate total. The canonical source is [CANONICAL_MATH.md](../canonical-review-v2/CANONICAL_MATH.md). Per-record applicability and residuals are retained in REQUIREMENT_COVERAGE.jsonl. A formula does not establish that the implementation satisfies its predicate.

The independently authored checks in `tests/golden_v4_reconciliation/test_domain_integrity.py` compare the **coordinate set**, unique IDs and classifications against separate Cartesian products and predicates. They do not merely compare generator length with a constant.

| Projection | Candidates | Valid | Invalid | Precisely established scope |
|---|---:|---:|---:|---|
| Result categorical wire axes | 4×4⁴ = 1,024 | 66 | 958 | Five categorical fields, absent and null distinguished on wire |
| Result semantic quotient | 4×3⁴ = 324 | 9 | 315 | Absence/null equivalence only for these categorical semantics |
| Observation presence masks | 9×2⁸ = 2,304 | 960 | 1,344 | Actual eight observation fields, valid payloads and judgment schema true; not arbitrary JSON |
| Labeled loop-free directed topologies n=0..4 | Σ2^(n(n−1)) = 4,166 | 573 DAG | 3,593 cyclic | Topology only; not bindings, guards, all node kinds, or all definitions |
| Standard reducer handling configurations | 8×2⁷ = 1,024 | Configuration-specific | Configuration-specific | Full coordinate product is checked; this is not all input sequences or all numeric results |
| RunRecord presence | 2¹⁸ = 262,144 | 16 | 262,128 | Independently valid present field values fixed; 14 required, four optional |
| NodeRecord presence | 2²⁰ = 1,048,576 | 256 | 1,048,320 | Independently valid present field values fixed; 12 required, eight optional |
| Gate valid-Result quotient | 9 | 9 | 0 | Nine accepted semantic classes; only KNOWN PASS continues |

Result wire validity partitions into disjoint classes: three nonexecution dispositions contribute 3×2⁴=48; executed ERROR contributes 2³=8; NOT_APPLICABLE contributes 2²=4; UNKNOWN contributes 2; KNOWN contributes four (absent/null/PASS/FAIL verdict). Total 48+8+4+2+4=66. The semantic quotient has 3+1+1+1+3=9 valid states. No Result payload constraint follows from this counting alone.

For observations, three known states allow all eight flags; six other states allow only five neutral flags. Thus 3×256+6×32=960. Nulls, wrong types, nonfinite numbers, evidence length and judgment schema interactions need separate assertions and are not silently included in that result.

Presence reduction fixes all field values and examines the root schema's actual allowed keywords and required set. With `required` conjunctive and no cross-key root presence condition, any mask missing one required key is invalid, whatever its optional bits. Tests execute every valid optional mask and each single required-field deletion. RunRecord saves 262,128−14=262,114 redundant invalid executions; NodeRecord saves 1,048,320−12=1,048,308. The proof does not cover arbitrary field values, lineage, resource arithmetic, timing or accepted record provenance. Those remain separate requirements. The full root predicates are not discharged by presence proofs.

RG.GATE.QUOTIENT follows the documented standard-gate rule. Nine semantic classes exhaust accepted categorical states. Inspection of the gate's five-field conjunction establishes independence from other accepted payload fields, conditional on correct Result acceptance. Nine exact Decision expectations witness each quotient element. Invalid Result acceptance is a separate prerequisite and is not universally proved here.

## Conditional and unbounded domains

- Availability is a snapshot relation over source definitions, accepted outputs, producer records and consumer schemas. The raw 360 coordinates do **not** classify reachability. Persisted CANCELLED without an accepted port is OUTPUT_MISSING, regardless of retained raw observations. Handler, consumed value, used_default and reason remain separately observable. Revision tests exercise authored reachable classes; arbitrary producer/consumer schemas and arbitrary records are not exhausted by them.
- Reducer member lengths, scores, severity/evidence payloads and weight identity are unbounded. Eight-by-128 configuration coverage does not prove algebraic laws over every member list. Binary64 rounding is not a portable exact-real-number guarantee.
- DAG induction requires node correctness, typed binding correctness, readiness and isolation premises. Small-graph enumeration and motif tests do not prove these premises for arbitrary shared mutable state, graph size or scheduler interleaving. No universal DAG correctness proof is claimed.
- Draft 2020-12 reference recursion and applicators are unbounded. Undefined results for nonprogressing references do not remove the nonlooping obligation. Boolean references into annotation locations, recursive evaluation boundaries and complete root normalization retain explicit per-record residuals.
- Schema values, Unicode, regexes, file sizes/paths, protocol traces, provider implementations and user functions are unbounded. The existing canonical partitions are not automatically implementation proofs. No arbitrary sample ceiling is promoted to a mathematical total.

The finite identities above are reproducible evidence for their projections. Remaining canonical records require the exact residual relation listed under their own ID; none is removed because a different projection passed.
