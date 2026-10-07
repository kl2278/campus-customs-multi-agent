# Campus Customs MCP Server

A small MCP server that gives the Campus Customs agents read-only access to shop data.

**Database:** `data/campus_customs_new.db` (the working copy), opened read-only. The path is set once as `DB_PATH` in `server.py`, relative to the project root. The original `data/campus_customs.db` is never touched.

## Tools

- `check_stock(sku, size, qty_needed=None)`: on-hand quantity and location for a SKU and size, plus the shortfall if a quantity is needed.
- `get_lease_rent_status(lease_id)`: rent, due date, days until due and overdue flag for a lease, judged against `desk.date_today`.
- `get_unit_pricing(sku, proposed_price=None)`: unit cost, list price and margins, plus margin and below-cost check at a proposed price.

More tools will be added in later problems.
