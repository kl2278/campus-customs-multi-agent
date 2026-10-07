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

The MCP server (`mcp_server/server.py`) exposes three read-only tools over `data/campus_customs_new.db`. Each one is matched below to the open ticket it unlocks.

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

---

## Later sections (added by later problems)

<!-- Add new sections below this line. -->
