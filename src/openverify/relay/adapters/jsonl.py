"""Single-process local JSONL storage, without transactional durability guarantees."""

from pathlib import Path

from openverify.model import RunRecord
from openverify.relay.adapters.memory import MemoryStore
from openverify.serialization import serialize
from openverify.validation import parse_run_record


class JsonlStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._memory = MemoryStore()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                self._memory.put(parse_run_record(line))

    def put(self, record: RunRecord) -> None:
        snapshot = parse_run_record(serialize(record))
        if self._memory.get(snapshot.run_id) is not None:
            raise ValueError("Run identity already stored")
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(serialize(snapshot) + "\n")
        self._memory.put(snapshot)

    def get(self, run_id: str) -> RunRecord | None:
        return self._memory.get(run_id)
