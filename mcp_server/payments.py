"""The one place a payment is executed.

Used by the execute_approved_payment MCP tool and by the human approve route,
so both follow the same rules and the same single transaction.
"""

import sqlite3
from datetime import date
from typing import Any

from mcp_server.db import (
    INVOICE_OPEN,
    INVOICE_PAID,
    KIND_INVOICE,
    KIND_PURCHASE_ORDER,
    KIND_RENT,
    STATUS_APPROVED,
    STATUS_EXECUTED,
    add_one_month,
    shop_date,
)


class PaymentRefused(Exception):
    """The payment cannot be executed. `payload` is the refusal result for the caller."""

    def __init__(self, message: str, **extra: Any) -> None:
        super().__init__(message)
        self.payload: dict[str, Any] = {"ok": False, "message": message, **extra}


def execute_payment(conn: sqlite3.Connection, approval_id: int) -> dict[str, Any]:
    """Execute an approved payment inside the caller's open transaction.

    The caller owns BEGIN/COMMIT/ROLLBACK. On any refusal this raises
    PaymentRefused before changing anything it could not roll back. On success it
    does all of this and returns the result (the caller then commits):
    insert the payments row with the approving human, lower the cash balance,
    mark the invoice paid (or move the lease next_due one month), and mark the
    approval executed.
    """
    today = shop_date(conn)
    ap = conn.execute("SELECT * FROM approvals WHERE id = ?", (approval_id,)).fetchone()
    if today is None:
        raise PaymentRefused("desk table has no date_today row.")
    if ap is None:
        raise PaymentRefused(f"No approval with id={approval_id}.")
    if ap["kind"] == KIND_PURCHASE_ORDER:
        raise PaymentRefused("Purchase orders are not payments; they only need approval.")
    if ap["status"] != STATUS_APPROVED:
        raise PaymentRefused(f"Approval {approval_id} is {ap['status']}; only an approved payment can be executed.")
    if not (ap["decided_by"] or "").strip():
        raise PaymentRefused(f"Approval {approval_id} has no recorded human approver.")
    if ap["kind"] == KIND_INVOICE:
        target = conn.execute("SELECT amount, status FROM invoices WHERE id = ?", (ap["ref_id"],)).fetchone()
        if target is None or target["status"] != INVOICE_OPEN:
            raise PaymentRefused(f"Invoice {ap['ref_id']} is missing or no longer open.")
        current_amount = target["amount"]
    elif ap["kind"] == KIND_RENT:
        target = conn.execute("SELECT monthly_rent, next_due FROM leases WHERE id = ?", (ap["ref_id"],)).fetchone()
        if target is None:
            raise PaymentRefused(f"Lease {ap['ref_id']} not found.")
        current_amount = target["monthly_rent"]
    else:
        raise PaymentRefused(f"Unknown approval kind {ap['kind']!r}.")
    if round(current_amount, 2) != round(ap["amount"], 2):
        raise PaymentRefused("The approved amount no longer matches the invoice or lease; queue a new approval.")
    acct = conn.execute("SELECT balance FROM cash_accounts WHERE name = ?", (ap["account"],)).fetchone()
    if acct is None:
        raise PaymentRefused(f"Cash account {ap['account']!r} not found.")
    if acct["balance"] < ap["amount"]:
        raise PaymentRefused(
            "Not enough cash. The payment was refused and no balance changed.",
            cash_balance=acct["balance"],
            amount=ap["amount"],
        )
    pay = conn.execute(
        "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
        (ap["kind"], ap["ref_id"], ap["amount"], ap["account"], today.isoformat(), ap["decided_by"]),
    )
    debited = conn.execute(
        "UPDATE cash_accounts SET balance = balance - ?, date = ? WHERE name = ? AND balance >= ?",
        (ap["amount"], today.isoformat(), ap["account"], ap["amount"]),
    )
    if ap["kind"] == KIND_INVOICE:
        settled = conn.execute(
            "UPDATE invoices SET status = ? WHERE id = ? AND status = ?",
            (INVOICE_PAID, ap["ref_id"], INVOICE_OPEN),
        )
        new_next_due = None
    else:
        new_next_due = add_one_month(date.fromisoformat(target["next_due"]))
        settled = conn.execute("UPDATE leases SET next_due = ? WHERE id = ?", (new_next_due, ap["ref_id"]))
    marked = conn.execute(
        "UPDATE approvals SET status = ?, executed_on = ?, payment_id = ? WHERE id = ? AND status = ?",
        (STATUS_EXECUTED, today.isoformat(), pay.lastrowid, approval_id, STATUS_APPROVED),
    )
    if debited.rowcount != 1 or settled.rowcount != 1 or marked.rowcount != 1:
        raise PaymentRefused("A concurrent change blocked the payment; nothing was changed.")
    new_balance = conn.execute(
        "SELECT balance FROM cash_accounts WHERE name = ?", (ap["account"],)
    ).fetchone()["balance"]
    return {
        "ok": True,
        "approval_id": approval_id,
        "payment_id": pay.lastrowid,
        "kind": ap["kind"],
        "ref_id": ap["ref_id"],
        "amount": ap["amount"],
        "approved_by": ap["decided_by"],
        "new_cash_balance": new_balance,
        "new_next_due": new_next_due,
        "message": "Payment executed once and recorded.",
    }
