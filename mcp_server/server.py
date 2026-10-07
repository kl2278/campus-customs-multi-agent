"""Campus Customs MCP server: read-only tools over the working database copy."""

import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from typing import Any

# mcp 1.x ships FastMCP (pinned: mcp 2.x renamed it to MCPServer).
from mcp.server.fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "campus_customs_new.db"

mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    """Open the working database read-only."""
    conn = sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _not_found(message: str) -> dict[str, Any]:
    return {"found": False, "message": message}


def _margin(price: float, unit_cost: float) -> tuple[float, float | None]:
    """Return (margin per unit, margin percent of price); percent is None if price is 0."""
    per_unit = price - unit_cost
    percent = round(per_unit / price * 100, 2) if price else None
    return round(per_unit, 2), percent


@mcp.tool()
def check_stock(sku: str, size: str, qty_needed: int | None = None) -> dict[str, Any]:
    """Check on-hand stock for one SKU and size in the inventory table.

    Use this when a ticket asks for a product and you need to know whether the
    shop has enough, where it is shelved, or how many units are short. Pass
    qty_needed to get the shortfall (0 when stock covers it). SKU and size must
    match exactly; if no row exists the result says "not found" instead of guessing.
    """
    if qty_needed is not None and qty_needed < 0:
        return {"found": False, "message": "qty_needed must not be negative."}
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT name, qty, location FROM inventory WHERE sku = ? AND size = ?",
            (sku, size),
        ).fetchone()
    if row is None:
        return _not_found(f"No inventory row for sku={sku!r}, size={size!r}.")
    result: dict[str, Any] = {
        "found": True,
        "sku": sku,
        "size": size,
        "name": row["name"],
        "qty_on_hand": row["qty"],
        "location": row["location"],
    }
    if qty_needed is not None:
        result["qty_needed"] = qty_needed
        result["shortfall"] = max(qty_needed - row["qty"], 0)
    return result


@mcp.tool()
def get_lease_rent_status(lease_id: int) -> dict[str, Any]:
    """Get rent details and due-date status for a lease.

    Use this when a ticket mentions rent or a lease and you need the amount,
    landlord, and whether rent is due soon or overdue. Everything is judged
    against desk.date_today (the shop's "today"), never the real date.
    days_until_due is negative when overdue.
    """
    with closing(_connect()) as conn:
        lease = conn.execute(
            "SELECT space_name, landlord, monthly_rent, next_due FROM leases WHERE id = ?",
            (lease_id,),
        ).fetchone()
        desk = conn.execute("SELECT date_today FROM desk LIMIT 1").fetchone()
    if lease is None:
        return _not_found(f"No lease with id={lease_id}.")
    if desk is None:
        return _not_found("desk table has no date_today row, so due status cannot be judged.")
    try:
        today = date.fromisoformat(desk["date_today"])
        next_due = date.fromisoformat(lease["next_due"])
    except ValueError as exc:
        return {"found": False, "message": f"Could not parse a date in the database: {exc}"}
    days_until_due = (next_due - today).days
    return {
        "found": True,
        "lease_id": lease_id,
        "space_name": lease["space_name"],
        "landlord": lease["landlord"],
        "monthly_rent": lease["monthly_rent"],
        "next_due": lease["next_due"],
        "date_today": desk["date_today"],
        "days_until_due": days_until_due,
        "is_overdue": days_until_due < 0,
    }


@mcp.tool()
def get_unit_pricing(sku: str, proposed_price: float | None = None) -> dict[str, Any]:
    """Get unit cost, list price and margins for a SKU from the pricing table.

    Use this when a ticket involves price, discounts or restock cost. Margin
    percent is margin per unit divided by the price. Pass proposed_price (for
    example a requested discount price) to see the margin at that price and
    whether it falls below cost.
    """
    if proposed_price is not None and proposed_price < 0:
        return {"found": False, "message": "proposed_price must not be negative."}
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT unit_cost, list_price FROM pricing WHERE sku = ?", (sku,)
        ).fetchone()
    if row is None:
        return _not_found(f"No pricing row for sku={sku!r}.")
    unit_cost, list_price = row["unit_cost"], row["list_price"]
    per_unit, percent = _margin(list_price, unit_cost)
    result: dict[str, Any] = {
        "found": True,
        "sku": sku,
        "unit_cost": unit_cost,
        "list_price": list_price,
        "margin_per_unit_at_list": per_unit,
        "margin_percent_at_list": percent,
    }
    if proposed_price is not None:
        p_unit, p_percent = _margin(proposed_price, unit_cost)
        result.update(
            proposed_price=proposed_price,
            margin_per_unit_at_proposed=p_unit,
            margin_percent_at_proposed=p_percent,
            below_cost=proposed_price < unit_cost,
        )
    return result


if __name__ == "__main__":
    mcp.run()
