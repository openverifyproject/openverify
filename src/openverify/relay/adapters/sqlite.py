"""Local transactional graph and run storage for the Relay Client host."""
# pyright: basic

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from openverify.model import RunRecord
from openverify.serialization import serialize
from openverify.validation import parse_definition, parse_run_record


class SQLiteStore:
    def __init__(self, path: Path):
        self.connection = sqlite3.connect(path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS graphs (
                graph_id TEXT PRIMARY KEY, current_revision INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS revisions (
                graph_id TEXT NOT NULL, revision INTEGER NOT NULL,
                definition TEXT NOT NULL, PRIMARY KEY(graph_id, revision)
            );
            CREATE TABLE IF NOT EXISTS runs (
                request_id TEXT PRIMARY KEY, graph_id TEXT NOT NULL,
                revision INTEGER NOT NULL, state TEXT NOT NULL,
                record TEXT, reason TEXT
            );
            CREATE TABLE IF NOT EXISTS records (run_id TEXT PRIMARY KEY, record TEXT NOT NULL);
        """)
        self.connection.execute(
            "UPDATE runs SET state='INTERRUPTED', reason='Host restarted' WHERE state='RUNNING'"
        )
        self.connection.commit()

    def register(self, definition: object) -> dict[str, object]:
        encoded = serialize(parse_definition(json.dumps(definition)))
        graph_id = str(uuid4())
        with self.connection:
            self.connection.execute("INSERT INTO graphs VALUES (?, 1)", (graph_id,))
            self.connection.execute("INSERT INTO revisions VALUES (?, 1, ?)", (graph_id, encoded))
        return {"graph_id": graph_id, "revision": 1}

    def replace(self, graph_id: str, definition: object) -> dict[str, object]:
        encoded = serialize(parse_definition(json.dumps(definition)))
        with self.connection:
            row = self.connection.execute(
                "SELECT current_revision FROM graphs WHERE graph_id=?", (graph_id,)
            ).fetchone()
            if row is None:
                raise KeyError(graph_id)
            revision = row[0] + 1
            self.connection.execute(
                "INSERT INTO revisions VALUES (?, ?, ?)", (graph_id, revision, encoded)
            )
            self.connection.execute(
                "UPDATE graphs SET current_revision=? WHERE graph_id=?", (revision, graph_id)
            )
        return {"graph_id": graph_id, "revision": revision}

    def definition(self, graph_id: str, revision: int | None = None) -> dict:
        if revision is None:
            row = self.connection.execute(
                "SELECT current_revision FROM graphs WHERE graph_id=?", (graph_id,)
            ).fetchone()
            if row is None:
                raise KeyError(graph_id)
            revision = row[0]
        row = self.connection.execute(
            "SELECT definition FROM revisions WHERE graph_id=? AND revision=?",
            (graph_id, revision),
        ).fetchone()
        if row is None:
            raise KeyError((graph_id, revision))
        return {"graph_id": graph_id, "revision": revision, "definition": json.loads(row[0])}

    def begin(self, request_id: str, graph_id: str, revision: int) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, 'RUNNING', NULL, NULL)",
                (request_id, graph_id, revision),
            )

    def finish(
        self, request_id: str, state: str, reason: str | None = None, record: str | None = None
    ) -> None:
        with self.connection:
            self.connection.execute(
                "UPDATE runs SET state=?, reason=?, record=? WHERE request_id=?",
                (state, reason, record, request_id),
            )

    def run(self, request_id: str) -> dict:
        row = self.connection.execute(
            "SELECT graph_id, revision, state, record, reason FROM runs WHERE request_id=?",
            (request_id,),
        ).fetchone()
        if row is None:
            raise KeyError(request_id)
        return dict(zip(("graph_id", "revision", "state", "record", "reason"), row, strict=True))

    def put(self, record: RunRecord) -> None:
        encoded = serialize(parse_run_record(serialize(record)))
        with self.connection:
            self.connection.execute("INSERT INTO records VALUES (?, ?)", (record.run_id, encoded))

    def get(self, run_id: str) -> RunRecord | None:
        row = self.connection.execute(
            "SELECT record FROM records WHERE run_id=?", (run_id,)
        ).fetchone()
        return parse_run_record(row[0]) if row and row[0] else None
