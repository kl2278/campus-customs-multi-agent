"""FastAPI routes for the Campus Customs dashboard.

Start from the backend/ folder with the venv active:
    uvicorn main:app --reload --port 8000
"""

import asyncio
import logging
import sys
import threading
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path

# Make the project root importable no matter where uvicorn was started, and drop the
# backend/ folder itself so backend/config.py can never shadow another module.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import Depends, FastAPI, HTTPException, Query, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from backend import config  # noqa: E402
from backend.audit import append_reset_marker, read_events, scrub_secrets  # noqa: E402
from backend.models import AgentReport, TicketRunResult  # noqa: E402
from backend.schemas import (  # noqa: E402
    ApprovalOut,
    CashOut,
    DecisionIn,
    DecisionOut,
    ErrorOut,
    EventOut,
    PaymentOut,
    ResetOut,
    RunOut,
    TicketOut,
)
from backend.team import run_ticket  # noqa: E402
from mcp_server import approvals, board  # noqa: E402
from mcp_server.db import WriteRefused  # noqa: E402
from mcp_server.reset import reset_working_copy  # noqa: E402

log = logging.getLogger("campus_customs.api")
LOG_LIMIT = 600  # characters of an error message written to the terminal
config.load_env()

app = FastAPI(title="Campus Customs Operations API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,  # explicit local dev origins, no wildcard
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

ERR = {"model": ErrorOut}


# --- Short, safe error bodies -------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    problems = "; ".join(
        f"{'.'.join(str(p) for p in e['loc'] if p != 'body')}: {e['msg']}" for e in exc.errors()
    )
    return JSONResponse(status_code=422, content={"detail": problems[:300]})


@app.exception_handler(WriteRefused)
async def write_refused(_: Request, exc: WriteRefused) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    log.error("Unhandled %s on a request", type(exc).__name__)  # type only: no details, no secrets
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on the server."})


# --- One run at a time -----------------------------------------------------------
class RunGuard:
    """Only one ticket run (or reset) may be active; the check-and-set is atomic."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.active: str | None = None

    def start(self, what: str) -> None:
        with self._lock:
            if self.active is not None:
                raise HTTPException(status_code=409, detail=f"Busy: {self.active} is in progress.")
            self.active = what

    def finish(self) -> None:
        with self._lock:
            self.active = None


guard = RunGuard()

RunFunction = Callable[[int], Awaitable[TicketRunResult]]


def get_run_function() -> RunFunction:
    """Dependency that provides the function which runs a ticket (tests override it)."""

    async def run(ticket_id: int) -> TicketRunResult:
        return await run_ticket(ticket_id)

    return run


def _is_complete(report: AgentReport | None) -> bool:
    """A ticket is resolved only if the Boss reports work_complete and is not failed/blocked."""
    return report is not None and report.work_complete and report.status not in ("failed", "blocked")


# --- Routes ------------------------------------------------------------------------
@app.get("/tickets", response_model=list[TicketOut])
def get_tickets() -> list[dict]:
    """Every ticket (all columns), status open/resolved, with its pending approval count."""
    return board.list_tickets()


@app.get("/cash", response_model=CashOut, responses={404: ERR})
def get_cash() -> dict:
    """Current checking balance and the shop date."""
    cash = board.get_cash(config.CASH_ACCOUNT_NAME)
    if cash is None:
        raise HTTPException(status_code=404, detail="Cash account not found.")
    return cash


@app.get("/events", response_model=list[EventOut], responses={500: ERR})
def get_events(
    ticket_id: int | None = None,
    run_id: str | None = None,
    since: datetime | None = Query(default=None, description="Only events newer than this ISO timestamp."),
    limit: int = Query(default=config.EVENTS_DEFAULT_LIMIT, ge=1),
    all_events: bool = Query(default=False, alias="all", description="Include events before the last reset."),
) -> list[dict]:
    """Recent agent events from the audit trail (read only). Default: after the last reset."""
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    try:
        return read_events(
            ticket_id=ticket_id, run_id=run_id, since=since,
            limit=min(limit, config.EVENTS_MAX_LIMIT), include_before_reset=all_events,
        )
    except ValueError:
        raise HTTPException(status_code=500, detail="The audit file could not be read.")


@app.get("/approvals", response_model=list[ApprovalOut])
def get_approvals(status: str | None = None) -> list[ApprovalOut]:
    """Payment approvals and purchase orders, pending and past, optionally by status."""
    return [ApprovalOut.from_row(r) for r in approvals.list_approvals(status)]


def _decision_response(result: dict) -> DecisionOut:
    if not result["ok"]:
        code = {"not_found": 404, "conflict": 409, "forbidden": 403, "invalid": 422}[result["code"]]
        raise HTTPException(status_code=code, detail=result["message"])
    pay = result["payment"]
    return DecisionOut(
        approval=ApprovalOut.from_row(result["approval"]),
        payment=PaymentOut(**{k: pay[k] for k in PaymentOut.model_fields}) if pay else None,
    )


@app.post(
    "/approvals/{approval_id}/approve", response_model=DecisionOut,
    responses={403: ERR, 404: ERR, 409: ERR, 422: ERR},
)
def approve_approval(approval_id: int, body: DecisionIn) -> DecisionOut:
    """Approve (and, for a payment, execute) in one transaction. This is the only approval path."""
    return _decision_response(approvals.approve_and_execute(approval_id, body.decided_by, body.note or ""))


@app.post(
    "/approvals/{approval_id}/reject", response_model=DecisionOut,
    responses={403: ERR, 404: ERR, 409: ERR, 422: ERR},
)
def reject_approval(approval_id: int, body: DecisionIn) -> DecisionOut:
    """Reject an approval. Moves no cash."""
    return _decision_response(approvals.reject(approval_id, body.decided_by, body.note or ""))


@app.post("/reset", response_model=ResetOut, responses={409: ERR})
def reset() -> ResetOut:
    """Restore the working copy from the original and add a reset marker to the audit trail."""
    guard.start("reset")
    try:
        reset_working_copy()
        append_reset_marker()
    finally:
        guard.finish()
    return ResetOut(message="Working copy restored from the original database.")


@app.post(
    "/tickets/{ticket_id}/run", response_model=RunOut,
    responses={404: ERR, 409: ERR, 500: ERR, 504: ERR},
)
async def run_ticket_route(ticket_id: int, run: RunFunction = Depends(get_run_function)) -> RunOut:
    """Run the Boss on one open ticket. Resolved only if the Boss reports the work complete."""
    status = board.get_ticket_status(ticket_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"No ticket with id={ticket_id}.")
    if status == "resolved":
        raise HTTPException(status_code=409, detail=f"Ticket {ticket_id} is already resolved.")
    guard.start(f"a run on ticket {ticket_id}")
    try:
        try:
            result = await asyncio.wait_for(run(ticket_id), timeout=config.RUN_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="The run timed out. The ticket stays open.")
        except Exception as exc:
            log.error("Run on ticket %s failed: %s", ticket_id, scrub_secrets(f"{type(exc).__name__}: {exc}")[:LOG_LIMIT])
            raise HTTPException(status_code=500, detail="The run failed. The ticket stays open.")
        if result.status != "finished":
            log.error(
                "Run %s on ticket %s stopped (%s): %s",
                result.run_id, ticket_id, result.status, scrub_secrets(result.error or "")[:LOG_LIMIT],
            )
            raise HTTPException(
                status_code=500,
                detail=f"The run stopped early ({result.status}, run {result.run_id}). The ticket stays open.",
            )
        if _is_complete(result.report):
            board.mark_ticket_resolved(ticket_id)
        return RunOut(
            run_id=result.run_id,
            ticket_id=ticket_id,
            run_status=result.status,
            report=result.report,
            ticket_status=board.get_ticket_status(ticket_id) or "open",
        )
    finally:
        guard.finish()
