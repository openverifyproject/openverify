# Contributing

Use Python 3.13 and uv from the repository root. SDK and engine share exactly
one root .venv and one locked dependency graph:

```sh
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Before protocol changes, explicitly answer: does this change meaning, wire format,
conformance, or the standard profile? Write semantics first; update schemas,
language-neutral conformance fixtures, SDK support, and tests together.
Implementation-only changes must not alter these accidentally. SDK behavior must
not introduce hidden semantics.

Record unresolved public questions in spec/draft/open-questions.md, identifying
the affected supported subset. Draft compatibility can change; record changes
in CHANGELOG.md and fixtures explicitly. Do not promise 1.0 stability.
Adapters are trusted host code registered explicitly; definitions are data.
Do not add infrastructure or provider integrations.

