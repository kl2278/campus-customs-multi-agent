"""Plain (non-MCP) board functions for the backend: tickets, cash, and ticket status.

Kept next to the shop rules so the routes stay thin. Nothing here is an MCP tool,
so no agent can reach it (for example, no agent can mark a ticket resolved).
"""

import sqlite3
from contextlib import closing
from typing import Any

from mcp_server.db import (
    KIND_PURCHASE_ORDER,
    STATUS_PENDING,
    TICKET_OPEN,
    TICKET_RESOLVED,
    WriteRefused,
    connect_ro,
    connect_rw,
    shop_date,
)


def _approvals_table_exists(conn: sqlite3.Connection) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'approvals'"
    ).fetchone() is not None


def list_tickets() -> list[dict[str, Any]]:
    """Every ticket row (all columns). status is shown as "open" or "resolved",
    plus the number of pending approvals linked to the ticket."""
    with closing(connect_ro()) as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()]
        pending: dict[int, int] = {}
        if _approvals_table_exists(conn):
            for r in conn.execute(
                "SELECT ticket_id, COUNT(*) AS n FROM approvals WHERE status = ? AND ticket_id IS NOT NULL "
                "GROUP BY ticket_id",
                (STATUS_PENDING,),
            ):
                pending[r["ticket_id"]] = r["n"]
    for row in rows:
        row["status"] = TICKET_OPEN if row["status"] == TICKET_OPEN else TICKET_RESOLVED
        row["pending_approvals"] = pending.get(row["id"], 0)
    return rows


def get_ticket_status(ticket_id: int) -> str | None:
    """The ticket's status ("open" or "resolved"), or None if there is no such ticket."""
    with closing(connect_ro()) as conn:
        row = conn.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        return None
    return TICKET_OPEN if row["status"] == TICKET_OPEN else TICKET_RESOLVED


def get_cash(account: str) -> dict[str, Any] | None:
    """One cash account plus the shop date, or None if the account does not exist."""
    with closing(connect_ro()) as conn:
        row = conn.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = ?", (account,)
        ).fetchone()
        today = shop_date(conn)
    if row is None:
        return None
    return {
        "account": row["name"],
        "balance": row["balance"],
        "date": row["date"],
        "shop_date": today.isoformat() if today else None,
    }


def mark_ticket_resolved(ticket_id: int) -> bool:
    """Mark an open ticket resolved. Returns True if it changed.

    Refuses (raises WriteRefused) if the database path is the original.
    """
    conn = connect_rw()  # raises WriteRefused for the original database
    with closing(conn):
        cur = conn.execute(
            "UPDATE tickets SET status = ? WHERE id = ? AND status = ?",
            (TICKET_RESOLVED, ticket_id, TICKET_OPEN),
        )
    return cur.rowcount == 1
