# Campus Customs MCP Server

An MCP server that gives the Campus Customs agents their shop facts and a small set of controlled actions.

**Database:** `data/campus_customs_new.db` (the working copy). The path is the `DB_PATH` constant in `db.py`, relative to the project root. An optional env var, `CAMPUS_CUSTOMS_DB_PATH`, overrides it for tests. Read tools open the database read-only. Write tools open it read-write but refuse to run if the path resolves to the original `data/campus_customs.db`.

Three small tables, `approvals`, `purchase_orders` and `customer_drafts`, are created lazily inside the working copy only, so a reset from the original wipes them.

## Tools

Read tools:
- `check_stock(sku, size, qty_needed=None)`: on-hand quantity, location and shortfall for a SKU and size.
- `get_lease_rent_status(lease_id)`: rent, due date, days until due and overdue flag, judged against `desk.date_today`.
- `get_unit_pricing(sku, proposed_price=None)`: unit cost, list price, margins, and a below-cost check.
- `get_shop_date()`: the shop's "today" from `desk.date_today`.
- `get_open_tickets()`: all open tickets.
- `get_ticket(ticket_id)`: one ticket with its links.
- `list_vendors()`: vendor id, name, specialty and lead days (no SKU-to-vendor link; choose by specialty).
- `get_invoice(invoice_id)`: one invoice with days past due and overdue flag.
- `list_open_invoices(vendor_id=None)`: unpaid invoices, optionally for one vendor.
- `get_vendor_ship_status(vendor_id)`: whether a vendor can ship today (no if it has any open unpaid invoice).
- `get_cash_balance(account=None)`: cash balance of one or all accounts.
- `list_payments()`: payments already made.
- `list_approvals(status=None)`: payment approvals and their state.
- `list_purchase_orders()`: purchase orders recorded.
- `list_customer_drafts(ticket_id=None)`: customer drafts saved on the board.

Write tools (these change the working copy only):
- `queue_payment_for_approval(kind, ref_id, requested_by, ...)`: queues an invoice or rent payment for human approval; moves no cash.
- `create_purchase_order(vendor_id, sku, size, qty, created_by, ...)`: saves an order with status `pending_approval` (a human approves it through the backend); refuses if the vendor has an open unpaid invoice; expected arrival is the shop date plus the vendor's lead days.
- `save_customer_draft(ticket_id, subject, body, created_by)`: saves a draft on the board; nothing is sent.
- `execute_approved_payment(approval_id)`: pays a human-approved approval once, in a single transaction; refuses without approval, on a repeat, or if cash is short.

Approving or rejecting is not a tool. Humans do it through the backend routes `POST /approvals/{id}/approve` and `/reject`, which call `approvals.py`. Other non-tool modules: `payments.py` (the single payment transaction shared by the tool and the approve route), `board.py` (tickets, cash, marking a ticket resolved) and `reset.py` (restore the working copy from the original).

More tools may be added in later problems.
