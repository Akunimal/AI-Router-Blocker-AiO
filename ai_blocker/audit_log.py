# -*- coding: utf-8 -*-
"""
SQLite-based audit log for recording all gateway proxy activity.

Provides append-only storage for request/response metadata including
DPI actions, DLP findings, and token counts.  Supports JSON-based
search queries and data export.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from ai_blocker.config import get_config_path

_DB_NAME = "audit.db"


def _get_db_path() -> str:
    base_dir = os.path.dirname(get_config_path())
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, _DB_NAME)


_SCHEMA = """\
CREATE TABLE IF NOT EXISTS audit_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    direction       TEXT    NOT NULL,
    domain          TEXT,
    path            TEXT,
    method          TEXT,
    action          TEXT    NOT NULL,
    token_count_in  INTEGER DEFAULT 0,
    token_count_out INTEGER DEFAULT 0,
    request_hash    TEXT,
    dlp_findings    TEXT,
    metadata        TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_entries(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_domain    ON audit_entries(domain);
CREATE INDEX IF NOT EXISTS idx_audit_action    ON audit_entries(action);
"""


@dataclass
class AuditEntry:
    """A single audit log entry."""
    direction: str  # "inbound" | "outbound"
    action: str  # "allowed" | "blocked" | "redacted" | "logged"
    domain: str = ""
    path: str = ""
    method: str = ""
    token_count_in: int = 0
    token_count_out: int = 0
    request_hash: str = ""
    dlp_findings: list[dict] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    id: int | None = None


class AuditLog:
    """Append-only SQLite audit log with search and export capabilities."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or _get_db_path()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    @staticmethod
    def compute_hash(body: str | bytes) -> str:
        """Compute a SHA-256 hash of the request body for deduplication."""
        if isinstance(body, str):
            body = body.encode("utf-8")
        return hashlib.sha256(body).hexdigest()

    def log_entry(self, entry: AuditEntry) -> int:
        """Insert an audit entry and return its row ID."""
        if not entry.timestamp:
            entry.timestamp = datetime.utcnow().isoformat()

        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO audit_entries
                   (timestamp, direction, domain, path, method, action,
                    token_count_in, token_count_out, request_hash,
                    dlp_findings, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.timestamp,
                    entry.direction,
                    entry.domain,
                    entry.path,
                    entry.method,
                    entry.action,
                    entry.token_count_in,
                    entry.token_count_out,
                    entry.request_hash,
                    json.dumps(entry.dlp_findings),
                    json.dumps(entry.metadata),
                ),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def search_entries(
        self,
        domain: str | None = None,
        action: str | None = None,
        since: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """Search audit entries with optional filters."""
        conditions: list[str] = []
        params: list[Any] = []

        if domain:
            conditions.append("domain LIKE ?")
            params.append(f"%{domain}%")
        if action:
            conditions.append("action = ?")
            params.append(action)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM audit_entries {where} ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_entry_count(self) -> int:
        """Return the total number of audit entries."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM audit_entries").fetchone()
            return row[0] if row else 0

    def export_json(self, limit: int = 1000) -> str:
        """Export recent audit entries as a JSON string."""
        entries = self.search_entries(limit=limit)
        return json.dumps([self._entry_to_dict(e) for e in entries], indent=2)

    def purge_older_than(self, days: int) -> int:
        """Delete entries older than *days* and return the count removed."""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM audit_entries WHERE timestamp < ?", (cutoff,)
            )
            return cur.rowcount

    def get_token_summary(self, hours: int = 1) -> dict[str, int]:
        """Aggregate token counts for the last *hours*."""
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(token_count_in), 0),
                          COALESCE(SUM(token_count_out), 0),
                          COUNT(*)
                   FROM audit_entries WHERE timestamp >= ?""",
                (since,),
            ).fetchone()
        return {
            "tokens_in": row[0],
            "tokens_out": row[1],
            "request_count": row[2],
        }

    # ── Private helpers ────────────────────────────────────────────────────

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            direction=row["direction"],
            domain=row["domain"] or "",
            path=row["path"] or "",
            method=row["method"] or "",
            action=row["action"],
            token_count_in=row["token_count_in"],
            token_count_out=row["token_count_out"],
            request_hash=row["request_hash"] or "",
            dlp_findings=json.loads(row["dlp_findings"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
        )

    @staticmethod
    def _entry_to_dict(entry: AuditEntry) -> dict:
        return {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "direction": entry.direction,
            "domain": entry.domain,
            "path": entry.path,
            "method": entry.method,
            "action": entry.action,
            "token_count_in": entry.token_count_in,
            "token_count_out": entry.token_count_out,
            "request_hash": entry.request_hash,
            "dlp_findings": entry.dlp_findings,
            "metadata": entry.metadata,
        }
