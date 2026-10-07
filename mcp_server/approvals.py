"""Human approve/reject logic for payment approvals.

This is plain Python, deliberately NOT an MCP tool, so no agent can approve its
own request. The dashboard (a later problem) calls these functions on behalf of
a signed-in human.
"""

from contextlib import closing
from typing import Any

from mcp_server.db import (
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    connect_rw,
    shop_date,
)


def _decide(approval_id: int, decided_by: str, new_status: str, note: str) -> dict[str, Any]:
    decided_by = (decided_by or "").strip()
    if not decided_by:
        return {"ok": False, "message": "decided_by (the human's name) is required."}
    with closing(connect_rw()) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
            if row is None:
                conn.execute("ROLLBACK")
                return {"ok": False, "message": f"No approval with id={approval_id}."}
            if row["status"] != STATUS_PENDING:
                conn.execute("ROLLBACK")
                return {"ok": False, "message": f"Approval {approval_id} is {row['status']}, not pending."}
            if row["requested_by"].strip().lower() == decided_by.lower():
                conn.execute("ROLLBACK")
                return {"ok": False, "message": "The requester cannot decide their own request."}
            today = shop_date(conn)
            if today is None:
                conn.execute("ROLLBACK")
                return {"ok": False, "message": "desk has no date_today."}
            conn.execute(
                "UPDATE approvals SET status = ?, decided_by = ?, decided_on = ?, decision_note = ? "
                "WHERE id = ? AND status = ?",
                (new_status, decided_by, today.isoformat(), note, approval_id, STATUS_PENDING),
            )
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    return {"ok": True, "approval_id": approval_id, "status": new_status, "decided_by": decided_by}


def approve(approval_id: int, decided_by: str, note: str = "") -> dict[str, Any]:
    """Mark a pending approval as approved by a named human."""
    return _decide(approval_id, decided_by, STATUS_APPROVED, note)


def reject(approval_id: int, decided_by: str, note: str = "") -> dict[str, Any]:
    """Mark a pending approval as rejected by a named human."""
    return _decide(approval_id, decided_by, STATUS_REJECTED, note)


def list_pending() -> list[dict[str, Any]]:
    """List approvals waiting for a human decision."""
    with closing(connect_rw()) as conn:
        rows = conn.execute(
            "SELECT * FROM approvals WHERE status = ? ORDER BY id", (STATUS_PENDING,)
        ).fetchall()
    return [dict(r) for r in rows]
