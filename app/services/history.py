"""SQLite-backed persistent conversion history."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.config import config
from app.core.jobs import JobItem, JobState, jobs


class HistoryEntry(BaseModel):
    id: str
    source_path: str
    target_path: Optional[str] = None
    source_format: str
    target_format: str
    engine: Optional[str] = None
    status: str
    settings: Dict[str, Any] = {}
    source_size_bytes: Optional[int] = None
    output_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: float


class HistoryService:
    """Manages SQLite storage for conversion history."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.history_db
        self._init_db()
        # Connect to job manager callback
        jobs.register_completion_callback(self.record_job)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    source_path TEXT NOT NULL,
                    target_path TEXT,
                    source_format TEXT NOT NULL,
                    target_format TEXT NOT NULL,
                    engine TEXT,
                    status TEXT NOT NULL,
                    settings_json TEXT,
                    source_size_bytes INTEGER,
                    output_size_bytes INTEGER,
                    duration_seconds REAL,
                    error_message TEXT,
                    created_at REAL NOT NULL
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def record_job(self, job: JobItem):
        """Save completed or failed job record."""
        # Derive source format from path or settings
        src_ext = Path(job.source_path).suffix.lower().lstrip(".") or "unknown"
        conn = self._get_conn()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO history (
                    id, source_path, target_path, source_format, target_format,
                    engine, status, settings_json, source_size_bytes,
                    output_size_bytes, duration_seconds, error_message, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.source_path,
                job.target_path,
                src_ext,
                job.target_format,
                job.engine,
                job.status,
                json.dumps(job.settings),
                job.source_size_bytes,
                job.output_size_bytes,
                job.duration_seconds,
                job.error_message,
                job.created_at
            ))
            conn.commit()
        finally:
            conn.close()

    def list_history(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List conversion history entries with optional filtering."""
        query = "SELECT * FROM history"
        params: List[Any] = []
        conditions = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if search:
            conditions.append("(source_path LIKE ? OR target_path LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        conn = self._get_conn()
        try:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                settings = {}
                if r["settings_json"]:
                    try:
                        settings = json.loads(r["settings_json"])
                    except Exception:
                        pass
                results.append({
                    "id": r["id"],
                    "source_path": r["source_path"],
                    "target_path": r["target_path"],
                    "source_format": r["source_format"],
                    "target_format": r["target_format"],
                    "engine": r["engine"],
                    "status": r["status"],
                    "settings": settings,
                    "source_size_bytes": r["source_size_bytes"],
                    "output_size_bytes": r["output_size_bytes"],
                    "duration_seconds": r["duration_seconds"],
                    "error_message": r["error_message"],
                    "created_at": r["created_at"],
                })
            return results
        finally:
            conn.close()

    def clear_history(self) -> int:
        conn = self._get_conn()
        try:
            cur = conn.execute("DELETE FROM history")
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def delete_entry(self, entry_id: str) -> bool:
        conn = self._get_conn()
        try:
            cur = conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


# Singleton history service instance
history = HistoryService()
