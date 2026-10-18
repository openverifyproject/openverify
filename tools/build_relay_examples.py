"""Compile example VCP definitions without executing any providers."""

from pathlib import Path

from openverify.relay.templates import code_graph, guardrail_graph, text_graph


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    graphs = {
        "first-run": text_graph(),
        "text-verification": text_graph(document=True),
        "guardrail": guardrail_graph(),
        "code-verification": code_graph(),
    }
    for directory, graph in graphs.items():
        (root / "examples" / directory / "definition.json").write_text(
            graph.to_json() + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
