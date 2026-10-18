"""Deterministic literal and regex verification, without semantic/factual claims."""

import asyncio
import json
import sys
from pathlib import Path
from typing import cast

from pydantic import JsonValue

from openverify.model import Context, Result
from openverify.relay.adapters.process import capture
from openverify.serialization import decode
from openverify.standard.common import STRING, STRINGS, judge, object_schema, standard


async def check_text(inputs: Context, config: Context) -> Result:
    text = cast(str, inputs["text"])
    findings: list[JsonValue] = []
    required = cast(list[str], inputs.get("required_terms", [])) + cast(
        list[str], config.get("required", [])
    )
    prohibited = cast(list[str], inputs.get("prohibited_terms", [])) + cast(
        list[str], config.get("prohibited", [])
    )
    for term in required:
        if term not in text:
            findings.append({"code": "required_text_missing", "term": term})
        if len(findings) > 10000:
            raise ValueError("Text findings exceed the 10000 observation limit")
    for term in prohibited:
        start = 0
        while (offset := text.find(term, start)) >= 0:
            if len(findings) >= 10000:
                raise ValueError("Text findings exceed the 10000 observation limit")
            findings.append(
                {
                    "code": "prohibited_text",
                    "term": term,
                    "start": offset,
                    "end": offset + len(term),
                    "line": text.count("\n", 0, offset) + 1,
                    "column": offset - text.rfind("\n", 0, offset),
                }
            )
            start = offset + max(1, len(term))
            if len(findings) % 100 == 0:
                await asyncio.sleep(0)
            if start > len(text):
                break
    patterns = cast(list[str], config.get("patterns", []))
    if patterns:
        # stdlib re has no preemption. Isolate authored patterns in a bounded process.
        observed = await capture(
            (sys.executable, "-m", "openverify.standard.pattern_worker"),
            str(Path.cwd()),
            timeout=2,
            limit=1024 * 1024,
            input_data=json.dumps({"text": text, "patterns": patterns}).encode(),
        )
        if observed.returncode:
            raise ValueError("Invalid regular expression")
        matches = cast(list[bool], decode(observed.stdout))
    else:
        matches = []
    for pattern, matched in zip(patterns, matches, strict=True):
        if not matched:
            if len(findings) >= 10000:
                raise ValueError("Text findings exceed the 10000 observation limit")
            findings.append({"code": "pattern_missing", "pattern": pattern})
    return judge(findings)


def text_provider():
    return standard(
        "text",
        "EVALUATE",
        {"text": STRING, "required_terms": STRINGS, "prohibited_terms": STRINGS},
        {},
        check_text,
        optional_inputs={"required_terms", "prohibited_terms"},
        config=object_schema(
            {"required": STRINGS, "prohibited": STRINGS, "patterns": STRINGS},
            optional={"required", "prohibited", "patterns"},
        ),
    )
