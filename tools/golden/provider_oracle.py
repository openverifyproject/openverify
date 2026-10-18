"""Provider Contract DRAFT 0.1 trace tables derived solely from its prose."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from tools.golden.oracle import schema_errors


def instant(value: str) -> Decimal:
    m = re.fullmatch(r"(\d{4})-(\d\d)-(\d\d)[Tt](\d\d):(\d\d):(\d\d)(\.\d+)?(?:[Zz]|\+00:00)", value)
    if not m:
        raise ValueError("UTC timestamp required")
    y, month, day, h, minute, second = map(int, m.groups()[:6])
    if h > 23 or minute > 59 or second > 59:
        raise ValueError("invalid time")
    return Decimal(date(y, month, day).toordinal() * 86400 + h * 3600 + minute * 60 + second) + Decimal(m[7] or "0")


def trace_error(trace: dict) -> str | None:
    """Finite trace validator; does not schedule work or communicate with providers."""
    from jsonschema import Draft202012Validator
    manifest, initialize = trace["manifest"], trace["initialize"]
    if schema_errors("provider-manifest", manifest, True):
        return "INVALID_PROVIDER_OUTPUT"
    pairs = [(c["capability_id"], c["capability_version"]) for c in manifest["capabilities"]]
    if len(pairs) != len(set(pairs)):
        return "INVALID_PROVIDER_OUTPUT"
    if schema_errors("initialize-request", initialize, True):
        return "CONTRACT_VERSION_UNSUPPORTED"
    common = [v for v in initialize["supported_contract_versions"] if v == "0.1" and v in manifest["supported_contract_versions"]]
    if not common:
        return "CONTRACT_VERSION_UNSUPPORTED"
    vcp = set(manifest["supported_vcp_versions"]) & set(initialize["supported_vcp_versions"])
    attempts = {}
    for step in trace["steps"]:
        action = step["action"]
        obj = step.get("invocation", step.get("event", step.get("request", step.get("outcome"))))
        identity = obj.get("invocation_id")
        if action == "accept":
            if identity in attempts:
                return "PROTOCOL_VIOLATION"
            if schema_errors("invocation", obj, True):
                return "INVALID_INVOCATION"
            if obj["contract_version"] != common[0]:
                return "CONTRACT_VERSION_UNSUPPORTED"
            caps = [c for c in manifest["capabilities"] if c["capability_id"] == obj["capability_id"]]
            if not caps:
                return "CAPABILITY_UNAVAILABLE"
            caps = [c for c in caps if c["capability_version"] == obj["capability_version"]]
            if not caps:
                return "CAPABILITY_VERSION_UNSUPPORTED"
            cap = caps[0]
            if cap.get("vcp_version") != obj.get("vcp_version") and "vcp_version" in cap:
                return "INVALID_INVOCATION"
            if "vcp_version" in obj and (obj["vcp_version"] != "draft" or "draft" not in vcp):
                return "INVALID_INVOCATION"
            if not Draft202012Validator(cap["input_schema"]).is_valid(obj["input"]):
                return "INVALID_INPUT"
            if not Draft202012Validator(cap["config_schema"]).is_valid(obj["config"]):
                return "INVALID_CONFIG"
            if "deadline" in obj:
                if not cap["lifecycle_features"]["deadlines"] or "now" not in step:
                    return "INVALID_INVOCATION"
                try:
                    instant(obj["deadline"]); instant(step["now"])
                except ValueError:
                    return "INVALID_INVOCATION"
            if "resource_budget" in obj:
                if obj.get("vcp_version") != "draft" or any(v["kind"] != "EXACT" for v in obj["resource_budget"].values()):
                    return "INVALID_INVOCATION"
            attempts[identity] = {"invocation": obj, "capability": cap, "terminal": False, "cancel": False, "sequence": 0, "first": True, "expired": "deadline" in obj and instant(step["now"]) >= instant(obj["deadline"])}
            continue
        if identity not in attempts:
            return "PROTOCOL_VIOLATION"
        state = attempts[identity]
        cap, invocation = state["capability"], state["invocation"]
        if action == "cancel":
            if schema_errors("cancel-request", obj, True):
                return "PROTOCOL_VIOLATION"
            if not state["terminal"] and not cap["lifecycle_features"]["cancellation"]:
                return "PROTOCOL_VIOLATION"
            state["cancel"] = True
            continue
        if state["terminal"]:
            return "PROTOCOL_VIOLATION"
        if action == "event":
            if schema_errors("provider-event", obj, True):
                return "INVALID_PROVIDER_OUTPUT"
            if not cap["lifecycle_features"]["streaming"]:
                return "PROTOCOL_VIOLATION"
            if (state["first"] and obj["sequence"] != 1) or obj["sequence"] <= state["sequence"]:
                return "PROTOCOL_VIOLATION"
            if obj["kind"] in ("evidence", "artifact", "resource_usage") and invocation.get("vcp_version") != "draft":
                return "INVALID_PROVIDER_OUTPUT"
            if obj["kind"] == "resource_usage" and not cap["lifecycle_features"]["resource_reporting"]:
                return "INVALID_PROVIDER_OUTPUT"
            if obj["kind"] == "evidence" and not any(obj["payload"].get(k) is not None for k in ("message", "artifact_ref", "locator", "structured_data")):
                return "INVALID_PROVIDER_OUTPUT"
            state.update(sequence=obj["sequence"], first=False)
        elif action == "outcome":
            if schema_errors("outcome", obj, True):
                return "INVALID_PROVIDER_OUTPUT"
            if obj["state"] == "CANCELLED" and not state["cancel"]:
                return "PROTOCOL_VIOLATION"
            if "deadline" in invocation:
                if "now" not in step:
                    return "PROTOCOL_VIOLATION"
                state["expired"] |= instant(step["now"]) >= instant(invocation["deadline"])
            if obj["state"] == "DEADLINE_EXCEEDED" and not state["expired"]:
                return "PROTOCOL_VIOLATION"
            if state["expired"] and obj["state"] != "DEADLINE_EXCEEDED":
                return "PROTOCOL_VIOLATION"
            if obj["state"] == "COMPLETED" and not Draft202012Validator(cap["output_schema"]).is_valid(obj["output"]):
                return "INVALID_PROVIDER_OUTPUT"
            if "resource_usage" in obj and (invocation.get("vcp_version") != "draft" or not cap["lifecycle_features"]["resource_reporting"]):
                return "INVALID_PROVIDER_OUTPUT"
            state["terminal"] = True
        else:
            raise ValueError(f"unknown independent trace action {action}")
    if trace.get("finish", True) and any(not s["terminal"] for s in attempts.values()):
        return "PROTOCOL_VIOLATION"
    return None


def encode_frame(message: dict) -> bytes:
    import json
    data = json.dumps(message, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    return f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data


def decode_frames(data: bytes) -> list[dict]:
    from tools.golden.oracle import strict_loads
    frames = []
    while data:
        header, sep, remaining = data.partition(b"\r\n\r\n")
        if not sep or not re.fullmatch(b"[Cc][Oo][Nn][Tt][Ee][Nn][Tt]-[Ll][Ee][Nn][Gg][Tt][Hh]: [0-9]+", header):
            raise ValueError("PROTOCOL_VIOLATION")
        length = int(header.split(b": ")[1])
        if not 0 < length <= 16 * 1024 * 1024 or len(remaining) < length:
            raise ValueError("PROTOCOL_VIOLATION")
        obj = strict_loads(remaining[:length])
        if not isinstance(obj, dict):
            raise ValueError("PROTOCOL_VIOLATION")
        frames.append(obj)
        data = remaining[length:]
    return frames
