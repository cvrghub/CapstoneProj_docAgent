"""SQLite storage with full audit trail: raw OCR, VLM extraction, corrections."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from config import SQLITE_PATH
from models.schemas import ProcessingRecord


def _get_conn() -> sqlite3.Connection:
    Path(SQLITE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invoice_records (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id      TEXT UNIQUE NOT NULL,
                source_path      TEXT,
                raw_ocr_text     TEXT,
                vlm_extraction   TEXT,
                corrections      TEXT,
                final_data       TEXT,
                validation_status TEXT,
                processing_notes TEXT,
                created_at       TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                event       TEXT,
                details     TEXT,
                timestamp   TEXT DEFAULT (datetime('now'))
            )
        """)


def save_record(record: ProcessingRecord) -> int:
    with _get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO invoice_records
                (document_id, source_path, raw_ocr_text, vlm_extraction,
                 corrections, final_data, validation_status, processing_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                vlm_extraction   = excluded.vlm_extraction,
                corrections      = excluded.corrections,
                final_data       = excluded.final_data,
                validation_status = excluded.validation_status,
                processing_notes = excluded.processing_notes
            """,
            (
                record.document_id,
                record.source_path,
                record.raw_ocr_text,
                json.dumps(record.vlm_extraction),
                json.dumps(record.corrections_applied),
                json.dumps(record.final_data),
                record.validation_status.value,
                json.dumps(record.processing_notes),
            ),
        )
        return cursor.lastrowid


def log_event(document_id: str, event: str, details: dict | None = None) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_log (document_id, event, details) VALUES (?, ?, ?)",
            (document_id, event, json.dumps(details or {})),
        )


def get_record(document_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM invoice_records WHERE document_id = ?", (document_id,)
        ).fetchone()
    return dict(row) if row else None


def list_records(limit: int = 100) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM invoice_records ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
