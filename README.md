# Campus Customs Multi-Agent Operations

A small campus shop has three open tickets: a customer order for a tee that is out of stock, a rent notice, and a request for a bulk hoodie discount. This project resolves them with a team of agents while a human keeps control of the money. It has three parts that talk to each other: an **MCP server** that gives the agents their shop facts and a few controlled actions, a **FastAPI backend** that runs **five PydanticAI agents** (Boss, Inventory, Accounting, Facilities and Customer Service), and a **React board** where a person watches the agents work and approves or rejects every payment and purchase order.

## Folder layout

```
README.md             this file
AI_prompts.md         log of the prompts I typed, one section per problem
requirements.txt      Python packages (mcp is pinned at 1.30.0)
.env.example          variable names only (copy to .env and fill in)
.mcp.json             registers the MCP server as "campus-customs"
data/                 campus_customs.db (original, course data) and campus_customs_new.db (working copy)
mcp_server/           the MCP server (server.py) plus db, payments, approvals, board and reset helpers
backend/              FastAPI app (main.py), config.py, models.py, agents/ and prompts/ (one .md per agent)
frontend/             React + Vite + TypeScript board
output/               plans, results and evidence (see "Where the evidence is")
```

## Requirements

- Python 3.14 (developed with 3.14.7)
- Node.js and npm (developed with Node 24.20.0 and npm 11.19.0)
- A Portkey API key. `.mcp.json` assumes the virtual environment is at `.venv/bin/python` (macOS or Linux paths).

## Setup

From the project folder:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd frontend && npm install
```

Then open `.env` and set `PORTKEY_API_KEY`. `.env.example` also lists `PORTKEY_PROVIDER`, `PORTKEY_VIRTUAL_KEY` and `PORTKEY_CONFIG`; fill those in only if your Portkey workspace needs them to reach the model.

## Get a clean database

The agents only ever use `data/campus_customs_new.db`. To start from the original data, stop the servers and run, from the project folder:

```
cp data/campus_customs.db data/campus_customs_new.db
```

## Start the MCP server

You normally don't have to. The backend launches it automatically over stdio, using the command in `.mcp.json` (`.venv/bin/python -m mcp_server.server`, run from the project folder). To run it by hand:

```
.venv/bin/python -m mcp_server.server
```

It speaks the MCP protocol on stdin and stdout and waits for a client, so there is nothing to see in the terminal. Press Ctrl-C to stop it. The same `.mcp.json` entry lets Claude Code load it as `campus-customs`.

## Start the FastAPI backend

With the virtual environment active:

```
cd backend
uvicorn main:app --reload --port 8000
```

## Start the React board

In a second terminal:

```
cd frontend
npm run dev
```

Then open http://localhost:5173. The port is fixed because the backend only allows that origin (and 127.0.0.1:5173 and localhost:3000). Other scripts: `npm run typecheck` and `npm run build`.

## Reset before a full three-ticket run

Do one of these before running the tickets:

- Click **Reset desk** on the board (it asks to confirm), or
- call `POST /reset` (for example `curl -X POST http://localhost:8000/reset`) with the backend running, or
- with the servers stopped, run the copy command from "Get a clean database".

A reset copies the original database over the working copy, which also wipes approvals, purchase orders and drafts, and adds a reset marker to the audit trail.

## Notes

- **The database in this repo is the end state of my run.** `data/campus_customs_new.db` has a $160 checking balance and all three tickets resolved. Reset before running anything. The original `data/campus_customs.db` is course data and is never written to.
- **One model only.** Every agent uses the model `gpt-6-luna` through Portkey.
- **Do not upgrade `mcp`.** It stays pinned at 1.30.0 because the server uses `mcp.server.fastmcp.FastMCP`, which later major versions removed.
- **Real runs spend tokens.** The limits (run timeout, delegation depth and count, requests, total tokens and steps) are in `backend/config.py`.
- **Humans approve every payment** in the dashboard, typing their own name each time. There is no approve tool for the agents.
- **Audit trail.** The committed `output/audit_trail.json` is a redacted copy of my real runs, and new runs append to it. My raw trail stayed local (`output/audit_trail.raw.json`, ignored by git) because it contained a customer's name.
- **One gateway deployment name.** The name the gateway reported in the first failed run appears once in `output/audit_trail.json` and once in `output/audit_trail_redacted.json`, as part of an error message.
- **Ticket order matters.** Paying invoice 501 (ticket 101) is what lets vendor 1 ship, so it changes what the other tickets can do.

## Where the evidence is

- `output/harness.md`: database tables, MCP tools, agents, API routes, dashboard, safety rules and the resolution run.
- `output/mcp_smoke.json`: the three first MCP tool calls made through Claude Code, with raw outputs.
- `output/desk_tickets.html`: my plan for each ticket next to what actually happened, the cash table and a written reflection (open it in a browser).
- `output/resolved_tickets.json`: one entry per ticket with its final status, runs, agents, cash change and approvals.
- `output/resolved_board.html`: dashboard screenshots for each resolved ticket (screenshots also in `output/screenshots/`).
- `output/audit_trail.json`: every agent step, redacted. `output/audit_trail_redacted.json` is the same export with a note.
- `output/design.md`: why the dashboard looks and behaves the way it does.
- `output/github_url.txt`: the repository URL.
- `AI_prompts.md`: the prompts I typed, problem by problem.
