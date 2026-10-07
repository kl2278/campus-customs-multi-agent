"""Human approve/reject logic for approvals (payments and purchase orders).

This is plain Python, deliberately NOT an MCP tool, so no agent can approve its
own request. The backend's approve/reject routes call these functions on behalf
of a human who typed their name.

Results are dicts: {"ok": True, ...} or {"ok": False, "code": ..., "message": ...}
where code is one of not_found, conflict, forbidden, invalid.
"""

import sqlite3
from contextlib import closing
from typing import Any

from mcp_server.db import (
    KIND_PURCHASE_ORDER,
    PO_APPROVED,
    PO_REJECTED,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    WriteRefused,
    connect_ro,
    connect_rw,
    shop_date,
)
from mcp_server.payments import PaymentRefused, execute_payment

_VIEW_SQL = (
    "SELECT a.*, p.qty AS quantity, p.sku AS po_sku, p.size AS po_size, p.vendor_id AS po_vendor_id, "
    "p.expected_arrival AS po_expected_arrival, p.status AS po_status "
    "FROM approvals a LEFT JOIN purchase_orders p ON a.kind = ? AND p.id = a.ref_id "
)


def _fail(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"ok": False, "code": code, "message": message, **extra}


def _view(conn: sqlite3.Connection, approval_id: int) -> dict[str, Any]:
    row = conn.execute(_VIEW_SQL + "WHERE a.id = ?", (KIND_PURCHASE_ORDER, approval_id)).fetchone()
    return dict(row)


def list_approvals(status: str | None = None) -> list[dict[str, Any]]:
    """All approvals (payments and purchase orders), newest last, optionally by status."""
    with closing(connect_ro()) as conn:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'approvals'"
        ).fetchone()
        if not exists:
            return []
        sql, params = _VIEW_SQL, [KIND_PURCHASE_ORDER]
        if status:
            sql += "WHERE a.status = ? "
            params.append(status)
        rows = conn.execute(sql + "ORDER BY a.id", params).fetchall()
    return [dict(r) for r in rows]


def _check_decider(decided_by: str) -> str | None:
    return None if (decided_by or "").strip() else "decided_by (the human's name) is required."


def approve_and_execute(approval_id: int, decided_by: str, note: str = "") -> dict[str, Any]:
    """Approve a pending approval. A payment is executed in the SAME transaction.

    If the payment cannot be executed (cash too low, invoice no longer open, ...)
    nothing is changed and the approval stays pending. A purchase order is only
    marked approved; it moves no cash.
    """
    problem = _check_decider(decided_by)
    if problem:
        return _fail("invalid", problem)
    decided_by = decided_by.strip()
    try:
        conn = connect_rw()
    except WriteRefused as exc:
        return _fail("conflict", str(exc))
    with closing(conn):
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            today = shop_date(conn)
            if row is None:
                conn.execute("ROLLBACK")
                return _fail("not_found", f"No approval with id={approval_id}.")
            if row["status"] != STATUS_PENDING:
                conn.execute("ROLLBACK")
                return _fail("conflict", f"Approval {approval_id} is already {row['status']}; nothing was changed.")
            if row["requested_by"].strip().lower() == decided_by.lower():
                conn.execute("ROLLBACK")
                return _fail("forbidden", "The requester cannot approve their own request.")
            if today is None:
                conn.execute("ROLLBACK")
                return _fail("conflict", "desk has no date_today.")
            conn.execute(
                "UPDATE approvals SET status = ?, decided_by = ?, decided_on = ?, decision_note = ? "
                "WHERE id = ? AND status = ?",
                (STATUS_APPROVED, decided_by, today.isoformat(), note, approval_id, STATUS_PENDING),
            )
            payment = None
            if row["kind"] == KIND_PURCHASE_ORDER:
                conn.execute(
                    "UPDATE purchase_orders SET status = ?, decided_by = ?, decided_on = ?, decision_note = ? "
                    "WHERE id = ?",
                    (PO_APPROVED, decided_by, today.isoformat(), note, row["ref_id"]),
                )
            else:
                payment = execute_payment(conn, approval_id)
            view = _view(conn, approval_id)
            conn.execute("COMMIT")
        except PaymentRefused as exc:
            conn.execute("ROLLBACK")
            return _fail("conflict", exc.payload["message"] + " The approval is still pending.")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"ok": True, "approval": view, "payment": payment}


def reject(approval_id: int, decided_by: str, note: str = "") -> dict[str, Any]:
    """Reject a pending approval. Moves no cash. A purchase order is marked rejected."""
    problem = _check_decider(decided_by)
    if problem:
        return _fail("invalid", problem)
    decided_by = decided_by.strip()
    try:
        conn = connect_rw()
    except WriteRefused as exc:
        return _fail("conflict", str(exc))
    with closing(conn):
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            today = shop_date(conn)
            if row is None:
                conn.execute("ROLLBACK")
                return _fail("not_found", f"No approval with id={approval_id}.")
            if row["status"] != STATUS_PENDING:
                conn.execute("ROLLBACK")
                return _fail("conflict", f"Approval {approval_id} is already {row['status']}; nothing was changed.")
            if row["requested_by"].strip().lower() == decided_by.lower():
                conn.execute("ROLLBACK")
                return _fail("forbidden", "The requester cannot decide their own request.")
            if today is None:
                conn.execute("ROLLBACK")
                return _fail("conflict", "desk has no date_today.")
            conn.execute(
                "UPDATE approvals SET status = ?, decided_by = ?, decided_on = ?, decision_note = ? "
                "WHERE id = ? AND status = ?",
                (STATUS_REJECTED, decided_by, today.isoformat(), note, approval_id, STATUS_PENDING),
            )
            if row["kind"] == KIND_PURCHASE_ORDER:
                conn.execute(
                    "UPDATE purchase_orders SET status = ?, decided_by = ?, decided_on = ?, decision_note = ? "
                    "WHERE id = ?",
                    (PO_REJECTED, decided_by, today.isoformat(), note, row["ref_id"]),
                )
            view = _view(conn, approval_id)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"ok": True, "approval": view, "payment": None}
