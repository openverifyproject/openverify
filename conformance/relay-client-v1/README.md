# Relay Client v1 portable request fixtures

`valid/` and `invalid/` contain language-neutral JSON request fixtures. A client
substitutes the graph ID returned by `register` for `$GRAPH_ID`. Every fixture
is a complete request envelope. Validity here covers client request shape;
execution can still fail because a provider is unavailable or a graph rejects
inputs. `register`, `replace`, `run`, `get`, `lookup`, and `cancel` each have a
valid fixture. The Python fixture test checks request validity; the SQLite
integration test checks revision persistence, repeated runs, binding failure,
and restart interruption. The dedicated Node test checks Provider Contract
success, error, evidence, and cancellation across stdio.
