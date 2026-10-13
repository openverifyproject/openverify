"""Shared typed fixture helpers."""

import json
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, VerificationDefinition
from openverify.validation import parse_definition

ROOT = Path(__file__).resolve().parents[1]


def definition(example: str = "prose") -> VerificationDefinition:
    return parse_definition((ROOT / f"examples/{example}/definition.json").read_bytes())


def context(example: str = "prose") -> Context:
    return cast(
        Context, json.loads((ROOT / f"examples/{example}/context.json").read_text(encoding="utf-8"))
    )


def handling(action: str = "REJECT") -> dict[str, JsonValue]:
    return {
        name: action
        for name in [
            "UNKNOWN",
            "ERROR",
            "SKIP",
            "DEFERRED",
            "CANCELLED",
            "NOT_APPLICABLE",
            "MISSING",
        ]
    }
