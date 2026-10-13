"""Replaceable local storage; no database or durability guarantees."""

from pathlib import Path
from typing import Protocol

from openverify.model import RunRecord
from openverify.serialization import serialize
from openverify.validation import parse_run_record


class RunStore(Protocol):
    def append(self, record: RunRecord) -> None: ...


class MemoryStore:
    def __init__(self) -> None:
        self._records: list[str] = []

    def append(self, record: RunRecord) -> None:
        # Validate and snapshot; later caller mutation cannot rewrite history.
        self._records.append(serialize(parse_run_record(serialize(record))))

    def records(self) -> list[RunRecord]:
        return [parse_run_record(record) for record in self._records]


class JsonlStore:
    def __init__(self, path: Path):
        self.path = path

    def append(self, record: RunRecord) -> None:
        checked = parse_run_record(serialize(record))
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(serialize(checked) + "\n")

    def records(self) -> list[RunRecord]:
        return [
            parse_run_record(line)
            for line in self.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
