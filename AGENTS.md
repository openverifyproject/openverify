# Repository rules

1. Read README and relevant spec pages before changing protocol semantics.
2. Protocol semantics must never be inferred from Python implementation.
3. Never resolve public ambiguity silently. Update spec/draft/open-questions.md.
4. New protocol objects require spec semantics, wire schema, Python support if
   implemented, tests, and portable conformance fixtures.
5. Fix correctness bugs with reusable regression/property tests. If a bug reveals
   semantic ambiguity, update open questions rather than patching around it.
6. Do not add external infrastructure merely because it may be useful later.
7. Keep core concepts domain-neutral.
8. Keep the reference engine replaceable and intentionally small.
9. Do not claim stable 1.0 compatibility while protocol status is DRAFT.
10. Documentation describes actual behavior. Label future/open behavior explicitly.

