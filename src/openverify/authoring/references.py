"""Typed references compile directly into VCP ValueSource objects."""

from dataclasses import dataclass

from pydantic import JsonValue

from openverify.model import ArtifactRef, Constant, ExternalReference, JsonSchema, ValueSource


@dataclass(frozen=True)
class Ref:
    source: ValueSource
    schema: JsonSchema


def constant(value: JsonValue, schema: JsonSchema = True) -> Ref:
    return Ref(Constant(value=value), schema)


def external(reference: ArtifactRef) -> Ref:
    return Ref(ExternalReference(reference=reference), {"type": "object"})
