"""Validated snapshot storage. Caller mutation never changes stored records."""

from openverify.model import RunRecord
from openverify.serialization import serialize
from openverify.validation import parse_run_record


class MemoryStore:
    def __init__(self) -> None:
        self._records: dict[str, str] = {}

    def put(self, record: RunRecord) -> None:
        encoded = serialize(record)
        parse_run_record(encoded)
        if record.run_id in self._records:
            raise ValueError("Run identity already stored")
        self._records[record.run_id] = encoded

    def get(self, run_id: str) -> RunRecord | None:
        encoded = self._records.get(run_id)
        return parse_run_record(encoded) if encoded is not None else None
