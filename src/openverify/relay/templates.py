"""Named, inspectable VCP graphs. These execute through the same public API."""

from openverify.authoring import Graph
from openverify.standard.common import ARRAY, OBJECT, STRING, STRINGS


def text_graph(*, document: bool = False) -> Graph:
    graph = Graph("document" if document else "text")
    if document:
        file = graph.input("file", STRING)
        read = graph.derive(
            "read",
            "openverify.read_text",
            inputs={"file": file},
            outputs={"text": STRING, "identity": OBJECT},
        )
        text = read["text"]
    else:
        text = graph.input("text", STRING)
    required = graph.evaluate(
        "required",
        "openverify.text",
        inputs={"text": text},
        config={"required": ["Migration", "Rollback"]},
    )
    prohibited = graph.evaluate(
        "prohibited",
        "openverify.text",
        inputs={"text": text},
        config={"prohibited": ["TODO", "TBD"]},
    )
    graph.aggregate("all", {"required": required.result, "prohibited": prohibited.result})
    return graph


def guardrail_graph() -> Graph:
    graph = Graph("guardrail")
    inputs = {
        n: graph.input(n, STRINGS if n == "allowed_prefixes" else STRING)
        for n in ("action", "target", "allowed_prefixes")
    }
    check = graph.evaluate("policy", "openverify.action_policy", inputs=inputs)
    combined = graph.aggregate("all", {"policy": check.result})
    graph.control("gate", "openverify.gate", inputs={"checked": combined.result})
    return graph


def code_graph(*, changed_spans: bool = False) -> Graph:
    graph = Graph("code_spans" if changed_spans else "code")
    cwd = graph.input("cwd", STRING)
    base = graph.input("base", STRING)
    scope = graph.derive(
        "git",
        "openverify.git_scope",
        inputs={"cwd": cwd, "base": base},
        config={"mode": "WORKTREE", "include_untracked": True},
        outputs={
            "changed_files": ARRAY,
            "changed_hunks": ARRAY,
            "diff": STRING,
            "candidate": OBJECT,
            "changes": ARRAY,
            "deleted_files": ARRAY,
        },
    )
    lint = graph.evaluate(
        "ruff",
        "openverify.ruff",
        inputs={"cwd": cwd, "files": scope["changed_files"]},
        outputs={"findings": ARRAY},
        config={"select": ["F"]},
    )
    scan = graph.derive(
        "ast",
        "openverify.astgrep",
        inputs={"cwd": cwd, "files": scope["changed_files"]},
        outputs={"findings": ARRAY},
        config={"language": "python", "pattern": "print($$$ARGS)"},
    )
    filtered = graph.derive(
        "ast_changed",
        "openverify.scope",
        inputs={
            "findings": scan["findings"],
            "files": scope["changed_files"],
            "ranges": scope["changed_hunks"],
        },
        outputs={"findings": ARRAY},
        config={"mode": "changed_spans"},
    )
    ast = graph.evaluate(
        "no_ast_violations", "openverify.no_findings", inputs={"findings": filtered["findings"]}
    )
    lint_result = lint.result
    if changed_spans:
        filtered_lint = graph.derive(
            "ruff_changed",
            "openverify.scope",
            inputs={
                "findings": lint["findings"],
                "files": scope["changed_files"],
                "ranges": scope["changed_hunks"],
            },
            outputs={"findings": ARRAY},
            config={"mode": "changed_spans"},
        )
        lint_result = graph.evaluate(
            "no_lint_violations",
            "openverify.no_findings",
            inputs={"findings": filtered_lint["findings"]},
        ).result
    unchanged = graph.evaluate(
        "fresh",
        "openverify.candidate_unchanged",
        inputs={"cwd": cwd, "candidate": scope["candidate"]},
        dependencies=[lint, ast],
    )
    graph.aggregate("all", {"ruff": lint_result, "ast": ast.result, "fresh": unchanged.result})
    return graph


def templates() -> dict[str, Graph]:
    return {
        "text": text_graph(),
        "document": text_graph(document=True),
        "guardrail": guardrail_graph(),
        "code": code_graph(),
        "code_spans": code_graph(changed_spans=True),
    }
