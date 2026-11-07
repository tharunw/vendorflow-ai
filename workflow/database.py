"""SQLite persistence for VendorFlow AI. Uses only the Python standard library."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS cases (
 case_id TEXT PRIMARY KEY, vendor_id TEXT NOT NULL,
 business_decision TEXT NOT NULL, lifecycle_status TEXT NOT NULL,
 current_version INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
 submission_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 version INTEGER NOT NULL, payload_json TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(case_id, version), FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE TABLE IF NOT EXISTS assessments (
 assessment_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 version INTEGER NOT NULL, result_json TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE TABLE IF NOT EXISTS audit_logs (
 audit_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 event_type TEXT NOT NULL, actor TEXT NOT NULL, details_json TEXT NOT NULL,
 created_at TEXT NOT NULL, FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE TABLE IF NOT EXISTS email_drafts (
 draft_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 version INTEGER NOT NULL, recipient TEXT, subject TEXT NOT NULL,
 body TEXT NOT NULL, created_at TEXT NOT NULL,
 FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE TABLE IF NOT EXISTS magic_links (
 link_id INTEGER PRIMARY KEY AUTOINCREMENT, case_id TEXT NOT NULL,
 token_hash TEXT NOT NULL UNIQUE, expires_at TEXT NOT NULL,
 used_at TEXT, created_at TEXT NOT NULL,
 FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
"""
class Database:
    def __init__(self, db_path="vendorflow.db"):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True) if self.db_path != ":memory:" else None
        with self.connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        """Yield a connection and always close it (required for Windows temp DB cleanup)."""
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
