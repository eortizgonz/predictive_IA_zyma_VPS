"""Persistencia SQLite lista para demo; migrable a PostgreSQL."""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DatabaseService:
    def __init__(self, path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent
        self.path = Path(path or os.getenv("DATABASE_PATH", base_dir / "data" / "predictive.db"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    id TEXT PRIMARY KEY,
                    profile TEXT NOT NULL,
                    machine_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS work_order_drafts (
                    id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    estimated_hours REAL,
                    estimated_cost REAL,
                    status TEXT NOT NULL,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    actor TEXT,
                    entity_id TEXT,
                    payload_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def ensure_conversation(self, conversation_id: str | None, profile: str, machine_id: str | None) -> str:
        conversation_id = conversation_id or str(uuid.uuid4())
        now = self.now()
        with self.connect() as db:
            db.execute(
                """INSERT INTO chat_conversations(id, profile, machine_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id) DO UPDATE SET profile=excluded.profile,
                       machine_id=excluded.machine_id, updated_at=excluded.updated_at""",
                (conversation_id, profile, machine_id, now, now),
            )
        return conversation_id

    def save_message(self, conversation_id: str, role: str, content: str, payload: Any = None) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO chat_messages VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), conversation_id, role, content, json.dumps(payload, ensure_ascii=False) if payload is not None else None, self.now()),
            )

    def create_work_order_draft(self, payload: dict) -> dict:
        draft_id = f"WO-DRAFT-{uuid.uuid4().hex[:8].upper()}"
        with self.connect() as db:
            db.execute(
                "INSERT INTO work_order_drafts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    draft_id,
                    payload["machine_id"], payload["priority"], payload["title"],
                    payload["description"], payload.get("estimated_hours"),
                    payload.get("estimated_cost"), "draft",
                    json.dumps(payload, ensure_ascii=False), self.now(),
                ),
            )
        return {"id": draft_id, "status": "draft", **payload}

    def audit(self, event_type: str, payload: dict, actor: str = "demo-user", entity_id: str | None = None) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO audit_events VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), event_type, actor, entity_id, json.dumps(payload, ensure_ascii=False), self.now()),
            )
