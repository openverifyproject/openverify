# Composition arguments and tested premises

Edges impose dependency; explicit UPSTREAM_OUTPUT bindings transport values. A
guard gates eligibility. CONTROL routing and ordered Aggregate membership are
separate declarations. No edge-type wire enum is introduced.

For a finite DAG choose a topological ordering. The base requires correct local
execution and immutable authored inputs. Assuming all predecessors are terminal,
typed binding resolution and target validation establish each successor's exact
inputs. Readiness then permits a single attempt; terminal immutability permits
induction. This argument requires noninterference of shared state and separate
proofs of global route exclusion, cancellation, waves and barriers.

Status: UNPROVED for arbitrary DAG size and arbitrary shared services. Small
INDEPENDENT, EDGE, CHAIN, FORK, JOIN, DIAMOND, ROUTE, GUARDED_JOIN, AGG_FANIN,
PARALLEL_BARRIER, STOP_CANCEL and MULTIRUN witnesses test the stated finite
premises. They do not establish universal scheduler or race correctness.

Explicit higher-order obligations: admission+cancellation+record;
filtering+weights+identity; route+guard+join; completion+cancellation+usage;
features+event kind+VCP compatibility. Pairwise success is not a proof of these.
Cross-module independence and a complete pair-obligation graph remain subject to
the fail-closed inventory gate; no implicit proof is claimed.
