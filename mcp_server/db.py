"""Database access shared by the MCP server and the human approval module.

Everything points at the working copy only. Read tools use a read-only
connection; write tools use a read-write connection that refuses to open the
original database.
"""

import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Any
import calendar

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_DB_PATH = PROJECT_ROOT / "data" / "campus_customs.db"
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"

# Optional override, used by tests to point at a scratch copy.
DB_PATH_ENV = "CAMPUS_CUSTOMS_DB_PATH"

# Invoice status values in the invoices table: "open" means unpaid.
INVOICE_OPEN = "open"
INVOICE_PAID = "paid"

# Approval lifecycle.
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EXECUTED = "executed"

# Tables created lazily, only inside the working copy.
NEW_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    ref_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    account TEXT NOT NULL,
    ticket_id INTEGER,
    requested_by TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL,
    created_on TEXT NOT NULL,
    decided_by TEXT,
    decided_on TEXT,
    decision_note TEXT,
    executed_on TEXT,
    payment_id INTEGER
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER NOT NULL,
    sku TEXT NOT NULL,
    size TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    ticket_id INTEGER,
    created_by TEXT NOT NULL,
    created_on TEXT NOT NULL,
    expected_arrival TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);
CREATE TABLE IF NOT EXISTS customer_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_on TEXT NOT NULL,
    status TEXT NOT NULL
);
"""


class WriteRefused(Exception):
    """Raised when a write is attempted against the original database."""


def get_db_path() -> Path:
    """Resolve the database path (env override first, else the working copy)."""
    override = os.environ.get(DB_PATH_ENV)
    return Path(override).resolve() if override else DB_PATH


def _is_original(path: Path) -> bool:
    if path.resolve() == ORIGINAL_DB_PATH.resolve():
        return True
    return path.exists() and ORIGINAL_DB_PATH.exists() and path.samefile(ORIGINAL_DB_PATH)


def connect_ro() -> sqlite3.Connection:
    """Open the working database read-only."""
    conn = sqlite3.connect(f"{get_db_path().as_uri()}?mode=ro", uri=True, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def connect_rw() -> sqlite3.Connection:
    """Open the working database read-write, never the original.

    Autocommit mode is used so callers control transactions explicitly.
    New tables are created here if they do not exist yet.
    """
    path = get_db_path()
    if _is_original(path):
        raise WriteRefused("Refusing to write: the path resolves to the original database.")
    if not path.exists():
        raise WriteRefused(f"Working database not found: {path.name}")
    conn = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(NEW_TABLES_SQL)
    return conn


def shop_date(conn: sqlite3.Connection) -> date | None:
    """Return desk.date_today as a date, or None if it is missing."""
    row = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    return date.fromisoformat(row["date_today"]) if row else None


def add_days(start: date, days: int) -> str:
    return (start + timedelta(days=days)).isoformat()


def add_one_month(start: date) -> str:
    """Move a date forward one calendar month, clamping to the month's last day."""
    year, month = (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day).isoformat()


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]
