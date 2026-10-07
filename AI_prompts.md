# Homework 5: Vibe Coder Prompt Log

This file logs what I typed to my vibe coder, one section per problem.

## Setup (before Problem 1)

Before starting Problem 1, I set up the project context (CLAUDE.md), the Python venv, .gitignore and the git repo.

### Setup Prompt 1

```
I'm working on Homework 5 for my AI class: "Campus Customs Multi-Agent Operations." We'll go one problem at a time, so please don't build ahead of what I ask for.

OVERVIEW
I'm building three pieces that talk to each other:
1. An MCP server
2. A FastAPI backend with a multi-agent team
3. A React dashboard so a human can watch the agents work and approve requests

AGENTS (full connectivity: any agent may delegate to any other agent)
- Boss: reads each ticket, decides who works on it, makes final calls
- Inventory: checks stock by SKU and size, spots shortfalls, figures out which vendor can restock
- Accounting: watches cash and invoices, checks margins, prepares payments/purchase orders for human approval
- Facilities: handles shop space (leases, rent, etc.)
- Customer Service: drafts messages for customers

DATA
- Original DB: data/campus_customs.db (NEVER modify this one)
- Working copy: data/campus_customs_new.db (MCP server and backend must point ONLY at this)
- Tables: desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, invoices

SHOP RULES (must be enforced in code)
- desk.date_today is "today" for the shop; use it to determine what is overdue
- Vendor lead times come from the vendors table
- A vendor will not ship new product while they still have an open unpaid invoice
- Human approval is required for ANY payment. If payment is made, update the relevant table(s)
- If there is not enough cash, the pay tool must refuse. No negative balances
- Cash only goes out; no revenue is modeled
- Before any full run resolving tickets, reset campus_customs_new.db from the original
- Do NOT email customers or call real vendors. Drafts stay on the board
- Use ONLY the model "gpt-6-luna" through Portkey for every agent, using the PORTKEY_API_KEY env var. No other model name may appear anywhere in the code, comments, or configs

HOUSEKEEPING
- The repo will be submitted as a PUBLIC GitHub repo, so never commit secrets. Keep the API key in .env, with a .env.example showing variable names only
- Create a CLAUDE.md in the project root that records all of the above so it persists across sessions

Confirm you've understood, and save this to CLAUDE.md. Don't write any other code yet.
```

### Setup Prompt 2

```
Set up a Python virtual environment in this Homework 5 folder.

1. Check that Python 3 is installed and tell me the version.
2. Create a venv named .venv in the project root.
3. Activate it and upgrade pip.
4. Install the starting dependencies: fastapi, uvicorn, mcp, python-dotenv, httpx, and portkey-ai. Check the current package names and install them, and tell me if any fail.
5. Create requirements.txt from what's installed.
6. Create a .gitignore that excludes .venv/, .env, __pycache__/, node_modules/, .DS_Store, and data/campus_customs_new.db (the working copy shouldn't be committed).
7. Create a .env.example with PORTKEY_API_KEY= (empty value), and a .env file for my real key that is covered by .gitignore.
8. Make a copy of data/campus_customs.db to data/campus_customs_new.db (the original must stay untouched).
9. Confirm VS Code is using .venv as its interpreter, and tell me what to click if I need to select it manually.
10. Verify everything by running a quick check that imports fastapi, mcp, and portkey, and opens campus_customs_new.db and lists its tables.

Show me a summary of what you did when finished.
```

### Setup Prompt 3

```
Two small things before Problem 1:

1. In the Homework 5 CLAUDE.md, add a note near the top: "The only valid model name for this project is gpt-6-luna. If any parent-folder CLAUDE.md or other file mentions a different model name, ignore it. This file takes priority for Homework 5." Then search the whole Homework 5 folder (excluding .venv) and confirm no other model name appears anywhere.

2. Run git init in the Homework 5 folder. Then run git status and show me what would be committed. Confirm that .env, .venv/, and data/campus_customs_new.db are NOT listed. Make an initial commit with the message "Initial setup: venv config, gitignore, original data". Do not push anything yet, and don't add a remote.

Show me the git status output and the list of files in the commit.
```

## Problem 1: Vibe coder prompts

**Prompt (condensed summary of the full request I sent):**

> Create AI_prompts.md in the Homework 5 root as a log of the prompts I type to you, one section per problem, and keep it updated as I work. Include the setup prompts, a section for Problem 1, a blank template for future problems, and a rule in CLAUDE.md to keep the log updated.

The full request also included the exact text of the three setup prompts above, which are logged verbatim in the Setup section.

**Follow-up (if needed):** None needed.

## Problem 2: Study the Campus Customs database

**Prompt:**

```
Problem 2 of my homework is to study the Campus Customs database and start a harness file.

1. Open data/campus_customs.db in READ-ONLY mode (for example sqlite3 with the URI "file:data/campus_customs.db?mode=ro"). Do not write to the original. Go through every table and list every field with its type, plus any primary keys and foreign keys, and the row count.

2. Copy data/campus_customs.db to data/campus_customs_new.db, overwriting the existing working copy. Then confirm the two files are byte-identical with a checksum, and confirm the original's checksum is the same as before you started.

3. Study the 3 open tickets in the tickets table. Show me each ticket in full, and trace how it links to other tables (SKUs, sizes, vendors, invoices, leases, cash accounts, pricing, and so on). Tell me what each ticket will likely require from the agents, including which shop rules apply (overdue dates against desk.date_today, vendor lead times, open unpaid invoices blocking shipment, human approval for payments, cash limits).

4. Create output/harness.md. Start it with a short title and one-line purpose. Add a section "Database tables" with one subsection per table (desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, invoices). Each subsection lists the fields (name, type, and a few words on what it holds) and then ONE short line on why that table matters for the agents. Add a second section "How the open tickets link to other tables" with a short summary of what you found in step 3. Don't put customer personal details in the file. Leave a clear spot at the bottom where later problems will add more sections.

5. Don't write any application code, don't change the schema or any data, and don't build ahead of this problem.
```

**Follow-up (if needed):** None needed.

## Problem 3: Build the MCP server

**Prompt:**

```
Problem 3 of my homework is to build the MCP server. We're only writing it in this problem, not connecting or running it.

1. Create mcp_server/ with a FastMCP server. The installed mcp package is a very new version, so check its docs or source for the correct FastMCP import before writing code. The server talks ONLY to data/campus_customs_new.db. Put that path in one config constant, resolved relative to the project root so it works from any working directory. Open the database in read-only mode, use parameterized SQL, and close connections properly. Never modify the original data/campus_customs.db.

2. Write exactly these 3 tools, with clear names, type hints and docstrings that say when an agent should use them:
   a. check_stock(sku, size, qty_needed=None): reads the inventory table. Returns the name, qty on hand and location for that SKU and size. If qty_needed is given, also return the shortfall (0 if there is enough stock).
   b. get_lease_rent_status(lease_id): reads the leases table and desk.date_today. Returns the space, landlord, monthly rent, next due date, days until due (negative if overdue), and an is_overdue flag, all judged against desk.date_today and never the real date.
   c. get_unit_pricing(sku, proposed_price=None): reads the pricing table. Returns unit_cost, list_price, and the margin per unit and margin percent at list price. If proposed_price is given, also return the margin per unit and margin percent at that price, and whether it is below cost.

3. Rules for the tools: never invent data. If a SKU, size or lease isn't found, return a clear "not found" result and don't guess. Don't hard-code any ticket data, SKUs or numbers in the code. Every number must come from the database or from the arguments. The tools are read-only, so no writes and no payments yet.

4. Update output/harness.md. Keep everything already in it, and add a new section "MCP tools" above the "Later sections" marker. For each of the 3 tools, include: the tool name, the table(s) it reads, which ticket it helps unlock (101, 102 or 103), and one sentence on why it is the right tool for that ticket. Tie each sentence to that ticket's actual facts from the database (for example the specific SKU, size, quantity, date or amount involved) and avoid vague lines like "reads inventory". Don't include customer personal details.

5. Create a short mcp_server/README.md that says what the MCP server is for, which database file it uses, and lists the 3 tools with a one-line description each. Mention that more tools will be added in later problems.

6. Don't start or connect the server. A syntax and import check is fine. You may call the underlying functions once directly to confirm they return correct data from campus_customs_new.db, and show me those results. Don't build FastAPI, agents or the dashboard yet. Don't touch the database contents, and make sure no AI model name appears anywhere in the new files.
```

**Follow-up (if needed):** The first prompt didn't say what to do if FastMCP was missing from the new mcp version, so the code used MCPServer instead of the FastMCP the assignment requires.

**Follow-up prompt:**

```
Follow-up on Problem 3: the assignment says to build the MCP server "using FastMCP", but you used MCPServer because mcp 2.3.0 removed FastMCP. I'd like the code to use a class actually named FastMCP.

1. Check which option installs cleanly alongside the other packages in .venv: (a) pin mcp to the latest 1.x release that still has mcp.server.fastmcp.FastMCP, or (b) use the standalone fastmcp package (from fastmcp import FastMCP). Pick the one that works, and tell me which you chose and why. If neither works, keep MCPServer and explain what failed.

2. Switch mcp_server/server.py to FastMCP. Keep the same 3 tools, signatures, read-only DB access and DB_PATH constant. Don't change any tool logic.

3. Re-run the same direct-call checks as before (tee S, hoodie M with 20, hat OS, lease 1, hoodie pricing at list and at 40) and confirm the results are identical.

4. Update mcp_server/README.md and output/harness.md only where they mention MCPServer or the library. Regenerate requirements.txt. Confirm the model-name search of the files is still clean and both database checksums still start 23686a90.
```

## Problem 4: Add the MCP server to vibe coder and test each tool

**Prompt:**

```
Problem 4 of my homework is to add my MCP server to this project so you (my vibe coder) can call its tools. This first step is only the connection setup.

1. Open mcp_server/server.py. If it doesn't already start the server when run as a script, add the minimal lines needed to run it over stdio (if __name__ == "__main__": mcp.run()). Don't change any tool logic. Nothing in the server may print to stdout, since stdout carries the protocol.

2. Add the server to this project's local MCP list in .mcp.json at the project root, with the server name "campus-customs". Use `claude mcp add --scope project` or write the JSON yourself. The command must be portable because this goes in a public repo: use the relative path .venv/bin/python with args ["-m", "mcp_server.server"], with no absolute paths, no usernames, and no env values or secrets.

3. Check that the server starts and answers a tools/list request over stdio from the project root (a quick script that launches it as a subprocess is fine). Show me that it lists exactly 3 tools, then stop it.

4. Run `claude mcp list` and show me the status. Tell me exactly what I need to do next to approve and load the project server (I expect I need to restart Claude Code in this folder and approve it).

5. Don't run the three tools yet, don't change the database, don't upgrade the mcp package (it stays pinned at 1.30.0), and don't build ahead.
```

**Note:** The test prompts for each tool follow after I restart Claude Code and approve the server.

### Problem 4 test prompts

**Test prompt 1 (check_stock):**

```
Use the campus-customs MCP tool check_stock to look up the white tee in size S (CC-TEE-WHITE) for ticket 101. I need to know how many we have on hand and whether we're short if a customer wants 1. Call the MCP tool itself. Don't query the database or write code. Show me the tool name and the raw output.
```

**Test prompt 2 (get_lease_rent_status):**

```
Use the campus-customs MCP tool get_lease_rent_status for lease 1, which is the lease on ticket 102. Tell me the rent, the due date, today's shop date and whether it's overdue. Call the MCP tool itself. Don't query the database or write code. Show me the tool name and the raw output.
```

**Test prompt 3 (get_unit_pricing):**

```
Use the campus-customs MCP tool get_unit_pricing for the navy hoodie (CC-HOOD-NAVY) from ticket 103. I want the cost, the list price and the margin at list price. Call the MCP tool itself. Don't query the database or write code. Show me the tool name and the raw output.
```

**Smoke-test evidence prompt:**

```
Now save the smoke-test evidence for Problem 4.

1. Create output/mcp_smoke.json with one entry per tool for the three tests I just ran in this session. Each entry must have "prompt" (the exact prompt I typed), "tool" (the exact MCP tool name that was called, plus the server name), "arguments", and "output" (the raw output the MCP tool returned in this session, copied exactly, not re-run through Python or retyped from memory). Add a top-level "note" saying these calls went through the vibe coder's MCP connection. Make it valid JSON, with no model names.

2. Verify against the database in read-only mode (data/campus_customs_new.db, mode=ro). Confirm every value in each output matches: qty and location for the tee, rent, due date and today's date for lease 1, and cost and list price for the hoodie. Show me a comparison table. If anything doesn't match, tell me and don't edit the outputs.

3. Add a short "MCP smoke test" section to output/harness.md above the Later sections marker. It should say the 3 tools were tested through the vibe coder, point to output/mcp_smoke.json, and give one line per tool with the ticket and the verified values. Keep all existing content.
```

**Follow-up (if needed):** None needed.

## Problem 5: Build the agent team and grow the MCP tools

**Prompt:**

```
Problem 5 of my homework is to build the agent team and grow the MCP tools. We are building and wiring only; we are not resolving the real tickets yet.

1. Dependencies and model config. Install PydanticAI in .venv (check the current package name and the extras needed for OpenAI-compatible models and MCP). IMPORTANT: mcp must stay pinned at 1.30.0 because mcp.server.fastmcp.FastMCP must keep working. After installing, run pip check and confirm the mcp version. If PydanticAI would force mcp to 2.x, stop and tell me instead of upgrading. Create backend/config.py with one constant for the model name, "gpt-6-luna", and route every agent through Portkey using the PORTKEY_API_KEY env var loaded with python-dotenv (check the current Portkey and PydanticAI docs for how to point an OpenAI-compatible provider at the Portkey gateway). If Portkey needs any extra routing value (a virtual key, provider slug or config id), read it from an env var, add only the variable NAME to .env.example, and tell me what I need to fill in. Don't read, print or copy any value from .env; you may only check whether a variable is set. gpt-6-luna must be the only model name anywhere in the repo.

2. Grow the MCP server (mcp_server/server.py, keep the 3 existing tools and their behavior unchanged). Add the tools the agents need for any ticket like the 3 open ones, with clear names, type hints and docstrings. Read tools should include: get_open_tickets, get_ticket, get_shop_date, list_vendors (id, name, specialty, lead_days; the database has no SKU-to-vendor link, so agents choose by specialty and say so), get_invoice, list_open_invoices (optionally by vendor), get_vendor_ship_status (can this vendor ship today? no if it has any open unpaid invoice), get_cash_balance, and list_payments. Write tools should include: queue_payment_for_approval (creates a pending approval for an invoice or rent, moves no cash), create_purchase_order (refuses if the vendor has an open unpaid invoice, otherwise records a purchase order with the expected arrival date from desk.date_today plus the vendor's lead_days), save_customer_draft (stores a draft on the board, sends nothing), and execute_approved_payment. execute_approved_payment must refuse unless a human-approved approval record exists for that exact payment, it hasn't been executed already, and the cash balance covers it (never a negative balance). When it succeeds, do everything in ONE database transaction: insert the payments row with approved_by, decrease cash_accounts, mark the invoice paid (for an invoice), and move the lease next_due forward one calendar month (for rent), then mark the approval executed. Approving is NOT an MCP tool: put the human approve/reject logic in a plain Python module (for example mcp_server/approvals.py) that a later dashboard will call, so no agent can approve its own request. Store pending approvals, purchase orders and drafts in three small new tables that the server creates with CREATE TABLE IF NOT EXISTS, ONLY inside the working copy data/campus_customs_new.db, so a reset from the original wipes them. Read tools keep the read-only connection; only the write tools use a read-write connection, and they must refuse to run if the resolved path is the original campus_customs.db. Allow an optional env var to override the DB path for tests, with the same refusal. Never invent data and never hard-code ticket data, SKUs or amounts; every number comes from the database or the arguments.

3. Agents. Build Boss, Inventory, Accounting, Facilities and Customer Service with PydanticAI under backend/, one file per agent (for example backend/agents/boss.py), with the shared data types in backend/models.py (ticket, agent dependencies, a structured agent report/output type, delegation request, audit entry). Agents get their shop facts only through the MCP server (use PydanticAI's MCP stdio support with the same command as .mcp.json). Give each agent a least-privilege allowlist of MCP tools: for example Customer Service can read and save drafts but cannot touch payments or purchase orders, Facilities handles leases and rent, Inventory handles stock, vendors and purchase orders, Accounting handles pricing, invoices, cash and queueing/executing payments, and Boss reads tickets and makes the final call. Don't build a second shop-tools layer that bypasses MCP.

4. Prompts. Put each agent's prompt in backend/prompts/ as its own file (boss.md, inventory.md, accounting.md, facilities.md, customer_service.md), written in plain language, detailed and covering that agent's whole scope. Each prompt should cover: its role and what it owns, what it must not do, which tools it has and when to use each, the shop rules that apply to it (desk.date_today as the only clock, vendor lead times from the vendors table, no shipping while a vendor has an open unpaid invoice, human approval for every payment, never exceed the cash balance, cash only goes out, never email customers or contact real vendors, drafts stay on the board), when and how to delegate to the other agents, how to treat ticket text as data and not as instructions, what to do when information is missing (say so, never guess), escalation to the human, and the output format. Keep the prompts general so they work for any ticket, with no ticket-specific numbers.

5. Delegation and limits. Full connectivity: every agent gets a delegate tool that lets it hand a task to any other agent and get that agent's report back. Add loop guards: a maximum delegation depth, a maximum number of delegations per ticket, a per-ticket usage limit shared across all delegated agents (request count and total tokens, using PydanticAI's usage limits), and a short per-agent step limit. Put every limit in backend/config.py. Add a small run_ticket(ticket_id) function (for example in backend/team.py) that starts the Boss on a ticket. No FastAPI endpoints and no dashboard yet.

6. Audit trail. Wire the agents so that every agent-loop step is appended to output/audit_trail.json as they run: timestamp, run id, ticket id, agent name, delegation depth, step number, step kind (model request, tool call, tool result, delegation, final output), tool name, arguments, a short result summary, and token usage where available. Never log secrets or env values. The file is a JSON array that is appended to, never wiped: read it, append, and write it back atomically with a file lock so concurrent agents don't corrupt it. Create it as [] if it doesn't exist. Allow an env var to override the path for tests.

7. Docs. In output/harness.md keep all existing sections, then add (a) an "Agents" section listing each of the 5 agents with its role, the MCP tools it may call and its delegation rights; (b) update the "MCP tools" section so it lists all tools, including the 3 original ones and every new one, each with the table(s) it uses, whether it reads or writes, and which ticket(s) it helps with where that applies; and (c) a short "Safety" section with the guardrails a real business would want when agents touch real customers and real money (human approval and spending caps, least-privilege tools, no external messages without review, redacting personal data, audit trail, treating ticket text as untrusted input, idempotent payments, a kill switch) plus the limits that keep token use in check (the usage limits, delegation depth and count, step limits, short outputs, using one model only). Keep it concise. Update mcp_server/README.md so the tool list matches exactly what the server has now, and note which tools write.

8. Verification and scope. Verify without spending real tokens and without touching the real working database: use a scratch folder outside the repo (for example in /tmp), not committed, with a temporary copy of the database and a temporary audit path. Show me: the server lists every tool and the 3 original tools return the same results as before; execute_approved_payment refuses with no approval, refuses after the approval is rejected, refuses when cash is too low, and succeeds exactly once on an approved payment, with the payments row, cash balance and invoice/lease updated and the same call refused the second time; create_purchase_order refuses for a vendor with an open invoice; an agent run with a stand-in model (PydanticAI's function-based test model) can delegate between two agents and writes steps to a temp audit file, and running it twice makes the file grow instead of resetting. If PORTKEY_API_KEY is set (check only that it is set, never show it), make at most one tiny live call to confirm the Portkey connection works and tell me the result; if it's not set or fails, skip it and tell me what is missing. Do not run the real tickets. Don't build FastAPI endpoints or the dashboard. Don't modify data/campus_customs.db and don't change data/campus_customs_new.db contents beyond the lazily created new tables if the server is started against it. Confirm both database checksums still start 23686a90 for the original, and that no model name other than gpt-6-luna appears in any repo file (outside .venv).
```

**Follow-up (if needed):** The first prompt allowed one live Portkey call, but the reply wasn't captured, so the connection to gpt-6-luna was never actually shown to work.

**Follow-up prompt:**

```
Follow-up on Problem 5: the one live Portkey call went through, but my print line crashed, so I never saw the reply, the model name or the token usage. I want proof the connection works with gpt-6-luna.

1. You may make exactly ONE more tiny live call through the backend config (the same client and settings the agents use). Ask it to reply with the single word OK. Fix the print line (usage is a property, not a method). Show me the reply text, the model name taken from backend/config.py, and the input and output token counts. Never print the API key, headers or any env value. If it fails, show me the error message with any secret removed and tell me what is missing (for example PORTKEY_PROVIDER, PORTKEY_VIRTUAL_KEY or PORTKEY_CONFIG), and don't retry more than that one call.

2. Check that AI_prompts.md has a "Problem 5: Build the agent team and grow the MCP tools" section with the Problem 5 prompt logged verbatim from "Problem 5 of my homework" through item 8. If it's missing or incomplete, tell me and add it. Don't paraphrase.

3. In AI_prompts.md under Problem 5, replace "Follow-up (if needed): None needed." with: "Follow-up (if needed): The first prompt allowed one live Portkey call, but the reply wasn't captured, so the connection to gpt-6-luna was never actually shown to work." Then log this message verbatim as the follow-up prompt, from "Follow-up on Problem 5" through item 3 (leave out this item 4 and item 5).
```

## Problem 6: Plan the 3 tickets

**Prompt:**

```
Problem 6 of my homework is to plan the 3 tickets before I wire the backend. In this problem I only write down what I EXPECT the team to do. Don't run any agents or tickets, don't start the MCP server against the working database, and don't open output/audit_trail.json. The plan must be written before I see any results.

1. Create output/desk_tickets.html: one self-contained file I can double-click to open in a browser. No external scripts, fonts, images or network requests, just HTML, CSS and a little JavaScript. It has five tabs: "Ticket 101", "Ticket 102", "Ticket 103", "Cash" and "Reflection". Keep it clean, readable and printable, with a clear active-tab style, and make sure it works without a server and stays readable on a narrow window.

2. Each ticket tab has these parts, in this order:
   a. A short "Ticket facts" box with the facts that matter, checked read-only against data/campus_customs_new.db (mode=ro) and against output/harness.md. Don't include customer names or other personal details.
   b. An "Expected" section with three labelled parts: "Boss calls first, and why", "Delegations I expect", and "MCP tools I expect this run to use". Use my wording from the plan below. You may fix grammar and format it as HTML, but don't add agents or tools I didn't list and don't change who is called first.
   c. An empty "Actual" section with a clear placeholder ("To fill in after I run the agents") and blank sub-headings that mirror the Expected parts (who the Boss called first, delegations, tools used, outcome, and how it differed from my plan), so I can fill it in later without restructuring the page.

3. The "Cash" and "Reflection" tabs are blank apart from a short "Coming later" note.

MY PLAN (today on the desk is 2026-08-31, checking balance $3,400):

TICKET 101: one white tee, size S, out of stock.
Facts: stock is 0 in Aisle B. The tee is tied to invoice 501: $840 from vendor 1 (apparel reprint, 5-day lead time), due 2026-08-28, still open, so 3 days overdue.
- Boss calls first: Inventory. Everything else depends on whether we can restock and who can ship, and Inventory is the agent that checks stock and vendors.
- Delegations I expect: Boss to Inventory. Inventory finds the shortfall, picks vendor 1 by specialty (apparel reprint, since the database has no SKU-to-vendor link), and sees that vendor 1 can't ship because invoice 501 is open. Inventory (or Boss) then delegates to Accounting to queue the $840 payment for human approval. Boss then delegates to Customer Service to draft a status message for the customer. Facilities is not involved because nothing about the lease or space is touched.
- MCP tools I expect: get_ticket, get_shop_date, check_stock, list_vendors, get_vendor_ship_status, get_invoice (or list_open_invoices), get_cash_balance, list_approvals, queue_payment_for_approval, save_customer_draft.
- Expected end state: the payment is pending human approval. The agents can't approve it, so the purchase order can't be created until the payment is approved and executed. If it were created today, it would arrive 5 days after the shop date. The customer draft should say the restock is pending and should not promise a date as certain.

TICKET 102: rent notice, rent due in 2 days.
Facts: lease 1 is $2,400 a month, next due 2026-09-02, which is 2 days after today, so it is not overdue.
- Boss calls first: Facilities. It is a lease question, and Facilities owns leases and rent timing.
- Delegations I expect: Boss to Facilities, who confirms the notice against the lease and the shop date. Facilities (or Boss) then delegates to Accounting to check cash and queue the $2,400 rent payment for human approval. Inventory is not needed because no stock is involved. Customer Service is not needed because the notice comes from the landlord side and there is no customer to answer.
- MCP tools I expect: get_ticket, get_shop_date, get_lease_rent_status, get_cash_balance, list_approvals, queue_payment_for_approval.
- Expected end state: the rent payment is pending human approval. $3,400 covers $2,400, but paying both this and invoice 501 leaves $160.

TICKET 103: 20 navy hoodies, size M, bulk discount requested.
Facts: 8 on hand, so 12 short. Cost $22 and list $58, so the margin at list is $36 per unit (62.07%). Restocking would come from vendor 1, who is blocked by the open invoice 501.
- Boss calls first: Accounting. The core of the ticket is a price override, so the first question is how much discount keeps a safe margin above cost. Stock comes second.
- Delegations I expect: Boss to Accounting, who checks pricing and margin at the requested price and checks cash. Then Boss to Inventory, who confirms 8 in stock and a shortfall of 12 and checks vendor 1's ship status (blocked by invoice 501). Then Boss to Customer Service to draft the reply with the Boss's decision. Facilities is not involved.
- MCP tools I expect: get_ticket, get_shop_date, get_unit_pricing, get_cash_balance, check_stock, list_vendors, get_vendor_ship_status, list_approvals, save_customer_draft.
- Expected end state: a discount decision that stays above the $22 cost, a draft reply, and no purchase order, because vendor 1 can't ship while invoice 501 is unpaid. Restocking 12 units costs about $264, which doesn't fit in the cash left after paying invoice 501 and the rent ($160), so agents shouldn't queue a second payment for it.

4. Verify the numbers: check every figure in the "Ticket facts" boxes and the plan (stock, dates, amounts, cost, list price, margin, lead time, cash balance) against the database read-only and tell me about any mismatch. Don't change my plan to fit what you find without telling me. Confirm the HTML has no external links, no customer personal details, and no model names. Confirm that every tool I listed exists in mcp_server/server.py, and tell me if any name doesn't.

5. Scope: write only output/desk_tickets.html, plus the log and commit steps below. Don't change any code, don't touch either database, and don't run the agents.
```

**Follow-up (if needed):** None needed.

## Problem 7: Backend routes

**Prompt:**

```
Problem 7 of my homework is to build the FastAPI routes in backend/main.py that the React dashboard will call in the next problem. We are building and testing the routes only. Don't build the dashboard, make no live model calls, and don't run the real tickets, so no tokens are spent.

1. Start command and layout. backend/main.py defines `app` so that this works from the backend/ folder with the venv active: `uvicorn main:app --reload --port 8000`. Because the server is started from backend/, it must work regardless of the working directory: put the project root on sys.path and import the existing backend.* modules, and make sure the agents' MCP stdio launch (the same command as .mcp.json) resolves the python path and working directory from the project root, not from the current directory. Add CORS for the local React dev server only (http://localhost:5173, http://127.0.0.1:5173, http://localhost:3000), with the origins listed in backend/config.py and no wildcard. Use Pydantic models for request bodies and responses. Return clear HTTP errors (404 for an unknown id, 409 for a conflict, 422 for bad input) with short messages, never stack traces, secrets or env values. Keep all shop facts and rules in the existing mcp_server code (db.py, approvals.py) and reuse it; don't write a second copy of the payment logic in the routes.

2. Routes. Use these paths:
   a. GET /tickets: every row of the tickets table (all its columns), with status shown as "open" or "resolved", plus the number of pending approvals linked to each ticket.
   b. GET /cash: the current checking balance read from cash_accounts (account name, balance, date), plus the shop date from desk.date_today.
   c. GET /events: recent agent events read from output/audit_trail.json so the board can refresh. Each event has timestamp, run id, ticket id, agent, depth, step kind, tool name, arguments, short result summary and, for agent messages and final outputs, what the agent said. Support optional filters ticket_id and run_id, a limit (default 100, capped at 500), and a way to ask only for events newer than a given timestamp. By default return only events after the most recent reset marker (see the reset route); allow all=true to return everything. A missing or empty file returns an empty list, not an error. Never modify the file in this route.
   d. GET /approvals: pending and past payment approvals and purchase orders (id, kind, linked ticket, amount or quantity, who requested it, status, who decided), optionally filtered by status.
   e. POST /approvals/{approval_id}/approve and POST /approvals/{approval_id}/reject. The body requires decided_by (a non-empty human name typed by the person clicking, never defaulted by the server) and accepts an optional note. Approve for a payment approves it and then executes it in ONE step through the same code path and transaction rules as execute_approved_payment: payments row with approved_by, cash decreased, invoice marked paid or lease next_due moved forward one month, approval marked executed. If the payment can't be executed (cash too low, already executed, rejected earlier), refuse with 409 and leave the approval pending, with no partial changes and never a negative balance. Approving the same payment twice must change nothing the second time. The approver may not be the agent that requested it. Reject changes no cash. Approve/reject must also work for a purchase order, where it only changes the order's status. These routes are the ONLY way an approval happens: confirm there is no approve tool in the MCP server and no agent allowlist can reach it.
   f. POST /reset: restore data/campus_customs_new.db to the original values by copying data/campus_customs.db over it atomically (copy to a temporary file, then replace, and remove any stale -wal or -shm files), so the added approval, purchase order and draft tables are wiped too. Refuse with 409 while a ticket run is in progress. Never write to the original; refuse if the target path resolves to the original. After resetting, append a reset marker entry to output/audit_trail.json (the audit file is never wiped; reuse the existing locked append, adding a "reset" step kind if the entry type needs it).

3. Run route: POST /tickets/{ticket_id}/run. Check that the ticket exists (404 if not) and refuse (409) if any run is already in progress, so only one run happens at a time, or if the ticket is already resolved. Otherwise run backend.team.run_ticket for that ticket, awaiting it in an async handler so the other routes (events, cash, approvals) stay responsive while it runs. Wrap it in a timeout set in backend/config.py. Get the run function through a FastAPI dependency so tests can override it with a stand-in; add no test-only switches or env flags in production code. Return the run id, the Boss's final report and the ticket's resulting status. Mark the ticket "resolved" in the tickets table only if the Boss's final report says the work is complete (not failed, not escalated or blocked on missing information). Pending human approvals don't block this, since the board shows them separately. Look at the report type in backend/models.py first and tell me which field you used. If it has no clear field, add the smallest one and tell me. The status update must be a plain function in mcp_server (not an MCP tool, so no agent can mark tickets resolved themselves) that refuses to write if the path is the original database. On a timeout or error, leave the ticket open, release the in-progress flag, and return a short error.

4. Purchase order approval. Check the purchase orders table and the create_purchase_order tool. If new orders are recorded as already final, change it so a new order is saved with status "pending_approval" (it still refuses for a vendor with an open unpaid invoice, and still sets the expected arrival date from desk.date_today plus lead_days). A human approves or rejects it with the routes above, and it moves no cash. The three new tables only exist in the working copy and the reset recreates it, so a schema change is safe. Make the smallest edits needed to the Inventory and Accounting prompts in backend/prompts/ so they say purchase orders are saved as pending and need human approval. Don't change anything else about the agents, and keep the 3 original tools and every other tool's behavior the same.

5. Docs. In output/harness.md keep all existing sections, and add a "Backend routes" section that gives the start command and then lists each route in one line (method, URL, and what it does). Update the create_purchase_order entry in the MCP tools section and the Safety section so they say the approve route is the only approval path. Update mcp_server/README.md only if a tool's behavior changed.

6. Verification, with no tokens and without touching the real working database. Use a scratch folder outside the repo (for example in /tmp), not committed, with a temporary copy of the database and a temporary audit path, and FastAPI's TestClient with the run dependency overridden by a stand-in model. Show me results for all of these:
   - GET /tickets returns the 3 tickets, all open on a fresh copy, and GET /cash equals the database balance.
   - The run route with the stand-in: an unknown ticket returns 404, a run while another is in progress returns 409, a completed run marks the ticket resolved, a failed or timed-out run leaves it open and frees the lock, and running a resolved ticket returns 409.
   - GET /events returns the stand-in run's steps, respects ticket_id, run_id, limit and the newer-than filter, and returns an empty list for a missing file.
   - Approvals: approving with the requesting agent's name is refused, an empty decided_by is rejected, approving an invoice payment executes it exactly once (payments row, cash down, invoice paid) and a second approve returns 409 with nothing changed, approving rent moves next_due one month, reject changes no cash, approving with too little cash returns 409 and the approval stays pending with the balance unchanged, and a purchase order can be approved and rejected with no cash change.
   - Reset: after changes it restores the original values (balance, invoice open, payments empty, tickets open, new tables empty or gone), the audit file is not wiped and gains a reset marker, GET /events then shows only post-reset events by default and everything with all=true, it returns 409 during a run, and the original database checksum is unchanged.
   - The real start command: start it exactly as `cd backend && uvicorn main:app --reload --port 8000` with the environment overrides pointing the database and audit file at the scratch copies, call the GET routes with curl, then stop the server and confirm no uvicorn process is left running.
   - Also show the MCP tool list (no approve tool) and a summary of every route with method, path and response status codes.

7. Scope. Don't build the dashboard or any frontend files. Don't modify data/campus_customs.db, and don't change data/campus_customs_new.db contents (tests use scratch copies). Keep mcp pinned at 1.30.0 and run pip check. Update requirements.txt only if something new was installed. Confirm the original database checksum still starts 23686a90, that gpt-6-luna is still the only model name in any repo file outside .venv, and that .env and the working database are not staged.
```

**Follow-up (if needed):** None needed.

## Problem 8: Agent dashboard

**Prompt:**

```
Problem 8 of my homework is to build the React dashboard in frontend/ (React + Vite + TypeScript) that calls the backend routes from Problem 7. We are building and checking the UI only. Make no live model calls and don't run the real tickets, so no tokens are spent.

1. Setup. Check that node and npm are installed and tell me the versions (if missing, stop and tell me how to install them). Create frontend/ with Vite + React + TypeScript. Dev server on port 5173 with strictPort. Keep node_modules out of git (already in .gitignore) but commit package-lock.json. Don't add anything to the Python requirements. The API base URL is one constant, http://localhost:8000, optionally overridable by a VITE_API_URL env var. Confirm the backend CORS origins in backend/config.py already include http://localhost:5173 and http://127.0.0.1:5173. Only edit backend code if something is missing, and tell me if you do. Use as few dependencies as possible; bundle the font through npm (for example @fontsource/eb-garamond) so nothing loads from the internet at runtime.

2. Features. The page calls these routes: GET /tickets, GET /cash, GET /events, GET /approvals, POST /tickets/{id}/run, POST /approvals/{id}/approve, POST /approvals/{id}/reject and POST /reset. It must:
   a. List all 3 tickets with status (open or resolved) and a badge for pending approvals.
   b. Let me pick one ticket and start the agent team on it. While a run is in progress, disable the run and reset buttons and poll GET /events (using the since filter), /tickets, /approvals and /cash every 1.5 seconds. Handle 404, 409, 422, 500 and 504 from the run route with a short friendly message, never a stack trace. The run request can take minutes, so don't time it out in the browser. Stop polling when the run ends, and do one last refresh.
   c. Show the five agents (Boss, Inventory, Accounting, Facilities, Customer Service) as separate cards. Each card shows its status (idle, working, delegating, done), the latest thing it said, and chips for the MCP tools it has used on this ticket, all derived from the events. Delegations between agents should be visible (for example "Boss handed this to Inventory").
   d. When a run finishes and the ticket is resolved, mark the ticket resolved in the list. If the run ends without resolving it, say so plainly.
   e. Show a short per-agent summary for the selected ticket after the run (what each agent did, built from its final output events and tool calls). Agents that weren't involved should say so.
   f. Show pending and past approvals. Approve and reject buttons ask for the approver's name in a text field the human must fill in (no default value from the app, and the button stays disabled while it's empty). Show the backend's 409 and 403 messages in friendly words. Show amount or quantity, who requested it and the linked ticket.
   g. Show the checking balance and the shop date. The balance must visibly count down after an approved payment, with a small "-$X" delta showing for a moment.
   h. A Reset button with a confirmation dialog, since it restores the database. After reset, clear the board.
   i. Loading, empty and error states everywhere, and a calm message if the backend is not reachable ("Start the backend first").

3. Look and feel. Make it feel like a real, cozy shop desk people want to sit at. Use a Yale-inspired theme: navy mixed with baby blue and a warm off-white paper tone. Use the font Garamond (stack: "EB Garamond", Garamond, "Cormorant Garamond", Georgia, serif). Use CSS variables for colors. Do not use Yale's logo, wordmark, crest or any official artwork. Ideas to use, and improve on freely:
   - An original, cute bulldog mascot drawn by you as inline SVG (not a copy of any official mascot image), called "Dan the Bulldog" as a nod to Handsome Dan. He sits at the desk, is sleepy when idle, perky and watching when agents are working, and happy when a ticket resolves. Respect prefers-reduced-motion.
   - Tickets styled like paper work orders on a desk, with a "RESOLVED" stamp that thumps down when done.
   - Each agent has its own accent color, icon and personality so they read differently at a glance, and a speech-bubble style for what they say.
   - A tidy activity feed of events, newest first, that can be collapsed.
   - Responsive layout that stays usable on a narrow window, and keyboard accessible, with good contrast and visible focus.

4. Sound. Add soft, short sound effects made with the Web Audio API (no audio files): a gentle doorbell or chime when a ticket resolves, a tiny blip when an agent starts, a soft ding when an approval is requested, and a low coin sound when a payment goes through. Keep the volume low. Nothing plays until the user has clicked something, and a visible mute/unmute button remembers its setting (localStorage is fine for that). Sounds must never repeat or loop.

5. Bone game. When the selected ticket is resolved, a "Give Dan a bone" button unlocks. Clicking it (or dragging a bone onto Dan, if you can do it simply and accessibly) makes Dan do a happy animation with a soft sound, and adds to a "treats given" counter. Keep it simple, with no scoring pressure. It is optional fun, and the dashboard must work fine without it.

6. Docs. Write output/design.md describing what you chose and why: layout, how the agents read differently, how resolved tickets and cash show up, the mascot, theme, font, sounds and bone game, and the accessibility choices (mute, reduced motion, contrast, keyboard use). Say clearly that the mascot is an original drawing inspired by Yale's bulldog tradition, with no official artwork. Keep it under about 1 page. Add a short frontend/README.md with the start commands: backend first (`cd backend && uvicorn main:app --reload --port 8000`), then `cd frontend && npm install && npm run dev`. In output/harness.md keep everything and add a short "Dashboard" section saying which routes the page calls and that humans approve through the dashboard.

7. Verification without spending tokens, and without touching the real working database. Show me:
   - npm run build and the TypeScript check both pass with no errors.
   - Start the backend with its environment overrides pointing the database and audit file at scratch copies in /tmp, and seed a scratch audit file and a pending approval so the UI has something to show. Check from the command line that the dev server at http://localhost:5173 serves the page and that the API calls succeed from that origin (a CORS check with curl and an Origin header is fine). If you can do a headless browser check cheaply, do one screenshot, otherwise skip it and tell me I need to look myself.
   - Confirm nothing in the frontend source calls an external URL other than http://localhost:8000, and that no model name other than gpt-6-luna appears in any repo file outside .venv and node_modules.
   - Stop both servers afterwards and confirm no process is left on ports 8000 and 5173.
   Don't run POST /tickets/{id}/run against the real backend, don't modify data/campus_customs.db, and don't change data/campus_customs_new.db. Confirm the original database checksum still starts 23686a90 and that .env and node_modules are not staged.
```

**Follow-up (if needed):** None needed.

## Problem 9: Resolve the tickets

**Prompt (stage 1 of 2):**

```
Problem 9 of my homework is to resolve the 3 tickets with real agent runs. This is stage 1: a read-only check before I start. I do every Run, Approve, Reject and Reset click myself in the dashboard. Don't spend any tokens and don't write to any database in this stage.

1. I have just pressed Reset desk. Confirm it worked: open data/campus_customs_new.db read-only (mode=ro) and compare it with data/campus_customs.db on these: checking balance, payments empty, invoice 501 status, lease 1 next_due, all 3 tickets open, inventory and pricing unchanged, and approvals, purchase_orders and customer_drafts empty or absent. Show a comparison table and tell me the starting checking balance. Tell me about any difference.

2. Look at output/audit_trail.json: show the number of entries and the step kind and timestamp of the last 3 (no message content). Confirm the last one is a reset marker.

3. Print the limits in backend/config.py (run timeout, delegation depth and count, request and token limits, step limit) so I know what to expect. Don't change them.

4. Confirm ports 8000 and 5173 are both being listened on, and that GET /tickets, GET /cash and GET /approvals on localhost:8000 agree with the database. Only GET requests. Check only that PORTKEY_API_KEY is set, and never show it.

5. Rules for the rest of this session: never call POST /tickets/{id}/run, POST /approvals/{id}/approve or reject, or POST /reset; never write to the working database; never edit code, prompts or limits unless I say so. When I tell you a run finished or I approved something, do read-only checks and tell me: the ticket status, the new audit events grouped by run id (which agents worked, who handed work to whom, which tools were used, the Boss's final report), any pending approvals with their amounts, token use if the audit shows it, and whether the balance in GET /cash matches the database. Flag anything odd, such as a refused tool call, repeated steps, a payment that doesn't match its invoice or rent, or a run that hit a limit. Never show names of customers.
```

**Follow-up (if needed):** The first prompt didn't say what to do if a real agent run crashed, and the first run on ticket 101 failed because the gateway rejects function tools together with reasoning effort on the chat completions endpoint for this model.

**Follow-up prompt:**

```
Follow-up on Problem 9: the run on ticket 101 failed with a 500. The audit file shows the gateway rejected the Boss's first request with a 400: "Function tools with reasoning_effort are not supported for gpt-6-luna-global in /v1/chat/completions. To use function tools, use /v1/responses or set reasoning_eff…". I want this fixed before any ticket runs again. Don't run any ticket and don't call POST /tickets/{id}/run, /approve, /approve, /reject or /reset. Don't change the limits in backend/config.py and don't touch either database.

1. Apply the logging change you proposed: log the exception type and a short message (up to about 600 characters) to the backend terminal when a run stops with an error, and keep up to 800 characters in the audit error event, with the PORTKEY_API_KEY value scrubbed. Add the import it needs. Keep the HTTP response to the browser short and free of exception text, as it is now.

2. Fix the model call. In backend/config.py, switch build_model from OpenAIChatModel to OpenAIResponsesModel with the same Portkey provider, the same model name gpt-6-luna and the same headers. Check the installed PydanticAI source for the right class name and import. Keep gpt-6-luna as the only model name. Don't set any reasoning effort yourself.

3. Test with ONE tiny live call, using the same build_model the agents use. The call must include a small function tool, for example a made-up tool that returns the word "pong", and ask the model to call it and then reply with one short sentence. Run it as a scratch script in /tmp, not in the repo, and don't use any MCP tools or the database. Show me whether the tool was called, the final reply, and the input and output token counts. Never print the API key, headers or env values. If it fails, show me the full error message with any secret removed, then stop. Don't retry more than that one call and don't try other options on your own.

4. If the one call succeeds, also check that the real Boss agent builds without a model call: construct it and list its tools and output type, but don't run it. Run the agent tests you used earlier with the stand-in model (delegation between two agents, audit trail growth, and the ping-pong depth limit) to confirm nothing broke. Confirm that pip check is clean, mcp is still 1.30.0, and the original database checksum still starts 23686a90.
```

---

## Template for future problems

### Problem N: [Title]

**Prompt:**

> [Paste the exact prompt text here]

**Follow-up (if needed):** [One sentence on what was lacking after the first prompt, followed by the exact follow-up prompt text.]
