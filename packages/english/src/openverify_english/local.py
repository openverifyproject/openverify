"""Deterministic English rules owned by openverify-english."""
# pyright: basic

import re
from pathlib import Path

from openverify.relay.local import finding, run_rules

RULES = {
    "phrase": "Prohibited phrases",
    "terminology": "Preferred terminology",
    "replacement": "Suggested replacements",
    "em-dash": "Em dash occurrences",
}


def english_rule(rule: str, root: Path, files: list[str], settings: dict) -> list[dict]:
    findings = []
    if rule == "phrase":
        patterns = [(p, f"Prohibited phrase: {p}") for p in settings.get("prohibited", [])]
    elif rule == "terminology":
        patterns = [
            (p, f"Use {replacement}", replacement)
            for p, replacement in settings.get("terms", {}).items()
        ]
    elif rule == "replacement":
        patterns = [
            (p, f"Consider {replacement}", replacement)
            for p, replacement in settings.get("replacements", {}).items()
        ]
    else:
        patterns = [("—", "Em dash")]
    for name in files:
        data = (root / name).read_bytes()
        if b"\0" in data:
            raise ValueError(f"Binary selected file: {name}")
        text = data.decode("utf-8")
        fenced = False
        for line_no, line in enumerate(text.splitlines(), 1):
            if name.lower().endswith(".md") and re.match(r"^\s*(```|~~~)", line):
                fenced = not fenced
                continue
            if fenced:
                continue
            for pattern in patterns:
                needle, message = pattern[:2]
                for match in re.finditer(re.escape(needle), line, re.IGNORECASE):
                    extra = {"replacement": pattern[2]} if len(pattern) > 2 else {}
                    findings.append(
                        finding(rule, name, line_no, match.start() + 1, message, **extra)
                    )
    return findings


def check(root: Path, names: list[str], staged: bool = False) -> dict:
    return run_rules("english", root, names, staged, RULES, english_rule)
