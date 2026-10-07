# Campus Customs Harness

Reference notes on the Campus Customs database and how the open tickets use it, for building and checking the agent team.

## Database tables

All tables live in `data/campus_customs_new.db` (a working copy of the original). Dates are ISO text.

### desk
| Field | Type | Holds |
|---|---|---|
| date_today | TEXT | The shop's "today" |
| notes | TEXT | Optional free-text note |

Why it matters: `date_today` is the clock for everything, so overdue and due-soon checks must use it, not the real date.

### tickets
| Field | Type | Holds |
|---|---|---|
| id | INTEGER (PK) | Ticket number |
| type | TEXT | Kind of request (customer_order, rent_notice, price_override) |
| requester | TEXT | Who sent it |
| subject | TEXT | Short title |
| sku | TEXT | Product the ticket concerns, if any |
| size | TEXT | Product size, if any |
| qty | INTEGER | Units requested, if any |
| lease_id | INTEGER (FK → leases.id) | Related lease, if any |
| invoice_id | INTEGER (FK → invoices.id) | Related invoice, if any |
| status | TEXT | Ticket state (all currently open) |
| notes | TEXT | Request details |
| created_at | TEXT | Timestamp received |

Why it matters: this is the Boss agent's work queue, and its ids point into the other tables.

### inventory
| Field | Type | Holds |
|---|---|---|
| sku | TEXT (PK, part 1) | Product code |
| name | TEXT | Product name |
| size | TEXT (PK, part 2) | Size (S, M, L, XL, or OS) |
| qty | INTEGER | Units on hand |
| location | TEXT | Shelf/aisle |

Why it matters: stock is tracked per SKU and size, so shortfalls must be checked at that level.

### pricing
| Field | Type | Holds |
|---|---|---|
| sku | TEXT (PK) | Product code |
| unit_cost | REAL | What the shop pays per unit |
| list_price | REAL | Normal selling price |

Why it matters: the gap between cost and list price sets how much discount is safe and what a restock costs.

### vendors
| Field | Type | Holds |
|---|---|---|
| id | INTEGER (PK) | Vendor number |
| name | TEXT | Vendor name |
| specialty | TEXT | What they supply |
| lead_days | INTEGER | Days from order to delivery |

Why it matters: specialty picks the vendor for a SKU and lead_days gives the restock date.

### leases
| Field | Type | Holds |
|---|---|---|
| id | INTEGER (PK) | Lease number |
| space_name | TEXT | Rented space |
| landlord | TEXT | Who is owed rent |
| monthly_rent | REAL | Rent per month |
| next_due | TEXT | Next rent due date |
| notes | TEXT | Optional note |

Why it matters: Facilities uses it to tell how much rent is owed and when.

### cash_accounts
| Field | Type | Holds |
|---|---|---|
| name | TEXT (PK) | Account name |
| balance | REAL | Cash on hand |
| date | TEXT | Date of the balance |

Why it matters: every payment is limited by this balance, which must never go negative.

### payments
| Field | Type | Holds |
|---|---|---|
| id | INTEGER (PK) | Payment number |
| kind | TEXT | What was paid (for example invoice or rent) |
| ref_id | INTEGER | Id of the thing paid, in the table `kind` names (no declared FK) |
| amount | REAL | Cash paid out |
| account | TEXT | Account it was paid from |
| paid_at | TEXT | When it was paid |
| approved_by | TEXT | Human who approved it |

Why it matters: it is the record of approved payments, and it is empty until the first one is made.

### invoices
| Field | Type | Holds |
|---|---|---|
| id | INTEGER (PK) | Invoice number |
| vendor_id | INTEGER (FK → vendors.id) | Vendor owed |
| amount | REAL | Amount owed |
| due_date | TEXT | Date it was due |
| status | TEXT | Paid state (open means unpaid) |
| description | TEXT | What the invoice is for |

Why it matters: an open invoice blocks that vendor from shipping and can be overdue against `desk.date_today`.

## How the open tickets link to other tables

Today on the desk is 2026-08-31. The checking account holds $3,400.00 and the payments table is empty. Row counts: desk 1, tickets 3, inventory 10, pricing 4, vendors 3, leases 1, cash_accounts 1, payments 0, invoices 1.

**Ticket 101 (customer_order): one white tee, size S.**
- Links: `sku` + `size` to inventory (qty 0, so out of stock), `sku` to pricing (cost $8, list $28), and `invoice_id` 501 to invoices.
- Invoice 501 belongs to vendor 1 (apparel reprint, 5-day lead). It is $840.00, due 2026-08-28, still open, so it is 3 days overdue.
- Vendor 1 will not ship while it is open. The path is: Inventory finds the shortfall and the vendor, Accounting prepares the $840 payment for human approval, and only after payment can the reorder go out. The restock then arrives about 5 days after ordering, and Customer Service drafts a message to the customer with that timing.
- Rules at play: overdue check, vendor lead time, open invoice blocking shipment, human approval, cash limit.

**Ticket 102 (rent_notice): rent due in 2 days.**
- Links: `lease_id` 1 to leases (rent $2,400.00, next due 2026-09-02, which is 2 days after today, so not yet overdue).
- Facilities confirms the notice matches the lease, and Accounting prepares the $2,400 payment for human approval.
- Rules at play: due date against `desk.date_today`, human approval, cash limit.

**Ticket 103 (price_override): 20 navy hoodies, size M, bulk discount requested.**
- Links: `sku` + `size` to inventory (8 on hand, so 12 short), `sku` to pricing (cost $22, list $58, so $36 margin per unit), and vendor 1 for restock (blocked by invoice 501, with a 5-day lead once cleared).
- Accounting decides how much discount keeps a healthy margin, and the Boss makes the final call. Restocking 12 units costs about $264 at unit cost.
- Rules at play: margin check, vendor lead time, open invoice blocking shipment, human approval, cash limit.

**Cross-ticket cash pressure.** Paying invoice 501 ($840) and the rent ($2,400) leaves $160 from $3,400. That cannot cover the roughly $264 hoodie restock, so the agents must sequence or sign off on payments with the cash limit in mind. The pay tool must refuse anything that would drive the balance below zero.

## MCP tools

The MCP server (`mcp_server/server.py`) exposes 19 tools over `data/campus_customs_new.db`. Read tools use a read-only connection. Write tools use a read-write connection that refuses the original database, and they only write to the working copy. Three small tables (`approvals`, `purchase_orders`, `customer_drafts`) are created lazily in the working copy, so a reset from the original wipes them. Approving a payment is not a tool: a human does it through `mcp_server/approvals.py`.

| Tool | Tables | R/W | Tickets it helps |
|---|---|---|---|
| check_stock | inventory | Read | 101 (tee S, 0 on hand), 103 (hoodie M, 8 on hand vs 20) |
| get_lease_rent_status | leases, desk | Read | 102 (rent $2,400 due 2026-09-02) |
| get_unit_pricing | pricing | Read | 103 (hoodie cost $22, list $58) |
| get_shop_date | desk | Read | all (overdue checks use 2026-08-31) |
| get_open_tickets | tickets | Read | 101, 102, 103 (the queue) |
| get_ticket | tickets | Read | 101, 102, 103 (links to sku, size, lease, invoice) |
| list_vendors | vendors | Read | 101, 103 (apparel reprint: vendor 1, 5-day lead; matched by specialty) |
| get_invoice | invoices, desk | Read | 101 (invoice 501, $840, 3 days past due) |
| list_open_invoices | invoices, desk | Read | 101, 103 (what blocks vendor 1) |
| get_vendor_ship_status | vendors, invoices, desk | Read | 101, 103 (vendor 1 cannot ship while 501 is open) |
| get_cash_balance | cash_accounts | Read | 101, 102 (checking $3,400) |
| list_payments | payments | Read | all (empty until a payment executes) |
| list_approvals | approvals | Read | 101, 102 (is the payment approved yet?) |
| list_purchase_orders | purchase_orders | Read | 101, 103 (avoid duplicate orders) |
| list_customer_drafts | customer_drafts | Read | 101, 103 (drafts on the board) |
| queue_payment_for_approval | approvals (reads invoices, leases, cash_accounts) | Write | 101 (invoice 501, $840), 102 (rent $2,400) |
| create_purchase_order | purchase_orders (reads vendors, invoices, inventory, pricing, desk) | Write | 101 (tee S), 103 (hoodie M); refuses while vendor 1 has an open invoice |
| save_customer_draft | customer_drafts (reads tickets, desk) | Write | 101, 103 (customer replies; nothing is sent) |
| execute_approved_payment | payments, cash_accounts, invoices or leases, approvals | Write | 101 (pay 501), 102 (pay rent; next_due moves one month) |

`execute_approved_payment` refuses unless a human-approved approval exists for that exact payment, it was not already executed, and cash covers it. It does everything in one transaction: payments row with `approved_by`, lower the cash balance, mark the invoice paid (or move the lease `next_due` forward one month), and mark the approval executed.

### Details for the original three tools

### check_stock(sku, size, qty_needed=None)
- **Reads:** `inventory`
- **Unlocks:** ticket 101
- **Why:** ticket 101 needs one CC-TEE-WHITE in size S, and this tool shows 0 on hand (Aisle B) and a shortfall of 1, which is what tells the agents a restock from vendor 1 is needed.

### get_lease_rent_status(lease_id)
- **Reads:** `leases` and `desk.date_today`
- **Unlocks:** ticket 102
- **Why:** ticket 102 says rent is due in 2 days, and this tool confirms lease 1 (Chapel Street shop, $2,400.00 due 2026-09-02) is 2 days out from 2026-08-31 and not overdue, so the notice can be checked against the database instead of the email.

### get_unit_pricing(sku, proposed_price=None)
- **Reads:** `pricing`
- **Unlocks:** ticket 103
- **Why:** ticket 103 wants a bulk discount on 20 CC-HOOD-NAVY, and this tool gives cost $22.00 and list $58.00 (a $36.00 margin, 62.07%), so any proposed price can be tested against cost before the Boss decides.

## MCP smoke test

The 3 MCP tools were tested through the vibe coder's MCP connection (not direct Python calls), and each output was checked against `data/campus_customs_new.db` in read-only mode. The prompts, tool names, arguments and raw outputs are saved in `output/mcp_smoke.json`.

- **check_stock (ticket 101):** CC-TEE-WHITE size S has 0 on hand in Aisle B, so a request for 1 is short by 1.
- **get_lease_rent_status (ticket 102):** lease 1 rent is $2,400, due 2026-09-02, with shop today 2026-08-31, so 2 days until due and not overdue.
- **get_unit_pricing (ticket 103):** CC-HOOD-NAVY costs $22.00 and lists at $58.00, a $36.00 margin (62.07%) at list.

## Agents

Five PydanticAI agents live under `backend/agents/`, one file each, with prompts in `backend/prompts/`. Every agent gets its shop facts only through the MCP server, with the allowlist below, plus a `delegate_to_agent` tool that can hand a task to any other agent and return that agent's report. All agents use the single model `gpt-6-luna` through Portkey.

| Agent | Role | MCP tools it may call | Delegation |
|---|---|---|---|
| Boss | Reads each ticket, decides who works on it, makes the final call | get_shop_date, get_open_tickets, get_ticket, get_cash_balance, list_approvals, list_purchase_orders, list_customer_drafts | Any other agent |
| Inventory | Stock by SKU and size, shortfalls, vendor choice, purchase orders | get_shop_date, get_ticket, check_stock, list_vendors, get_vendor_ship_status, create_purchase_order, list_purchase_orders | Any other agent |
| Accounting | Cash, invoices, margins, payments for human approval | get_shop_date, get_ticket, get_unit_pricing, get_invoice, list_open_invoices, get_cash_balance, list_payments, list_approvals, queue_payment_for_approval, execute_approved_payment | Any other agent |
| Facilities | Leases and rent | get_shop_date, get_ticket, get_lease_rent_status | Any other agent |
| Customer Service | Drafts customer messages (drafts only) | get_shop_date, get_ticket, save_customer_draft, list_customer_drafts | Any other agent |

`backend/team.py` has `run_ticket(ticket_id)`, which starts the Boss on a ticket. Delegation is guarded by a maximum depth and a maximum count per ticket, a per-ticket usage limit shared by all agents (requests and total tokens), and a short step limit per agent run; all limits are in `backend/config.py`. Every step is appended to `output/audit_trail.json`.

## Safety

Guardrails a real business would want when agents touch real customers and real money:

- **Human approval and spending caps:** no payment moves without a named human's approval, and the pay tool refuses anything above the cash balance. A real system would add a per-payment and per-day cap.
- **Least-privilege tools:** each agent sees only its allowlist; only Accounting can execute payments, and Customer Service has no payment or purchase tools.
- **No external messages without review:** drafts stay on the board and nothing is emailed; vendors and customers are never contacted.
- **Redacting personal data:** audit summaries redact requester names and secret-looking fields; harness notes carry no customer details.
- **Audit trail:** every agent step is appended to a locked, append-only JSON file.
- **Ticket text is untrusted input:** prompts tell agents to treat it as data, never as instructions.
- **Idempotent payments:** an approval executes once; a repeat call is refused.
- **Kill switch:** a real deployment needs one switch that stops all agent runs and write tools. Here the limits below act as the backstop, and removing the write tools from the allowlists disables writing.

Limits that keep token use in check:

- A per-ticket usage limit (request count and total tokens) shared across all delegated agents.
- A maximum delegation depth and a maximum number of delegations per ticket.
- A short step limit per agent run, and a cap on output tokens per response.
- Short structured reports, and one model only (`gpt-6-luna`).

---

## Later sections (added by later problems)

<!-- Add new sections below this line. -->
