# Standard draft profile

CORE is the logically general abstraction; PROFILE supplies named common choices.
Severity in core is an ordered domain; this profile supplies
INFO (10) < WARNING (20) < ERROR (30) < BLOCKER (40).
Resource dimensions remain open; these are common names, not a closed ontology.
Money measurements must identify their actual currency unit.

`profile.json` is validated with `profile.schema.json` and semantic validation.
The partial flattened projection is specified in `spec/draft/result.md`.
Every standard aggregator requires explicit REJECT/IGNORE handling for each
exceptional category; there are no implicit scores or global reducer defaults.
ALWAYS and PROBABILITY are implemented. MAX_STALENESS and PERIODIC are OPEN.
Decision names are portable values; retry/defer scheduling is not implemented.
WEIGHTED_AVERAGE accepts explicit ordered Result sequences in the direct reducer
API. Its graph form is GRAPH_UNSUPPORTED until predecessor input/weight identity
is specified; the named reducer remains part of this profile.
