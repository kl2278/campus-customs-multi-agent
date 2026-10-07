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

---

## Template for future problems

### Problem N: [Title]

**Prompt:**

> [Paste the exact prompt text here]

**Follow-up (if needed):** [One sentence on what was lacking after the first prompt, followed by the exact follow-up prompt text.]
