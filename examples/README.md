# Local domain-neutral examples

From the repository root:

```sh
uv run openverify run examples/prose/definition.json --context examples/prose/context.json --opportunity-id article-draft-1
uv run openverify run examples/generic/definition.json --context examples/generic/context.json --opportunity-id reading-1
uv run openverify run examples/ai-output/definition.json --context examples/ai-output/context.json --opportunity-id response-1
```

Prose derives length, checks a banned phrase and length, then aggregates ALL.
Generic checks a temperature envelope; it does not control a physical device.
AI output uses a deterministic form check and a mock inconclusive judge, then
routes to a mock human review. No external model or human service is connected.
The examples do not imply an overall verdict without an Aggregate node.

`--output run.json` saves the complete portable RunRecord. CLI `run` uses the
explicit local demo registry. Host applications may supply their own registry.
No adapter names authorize imports or expressions from definitions.
