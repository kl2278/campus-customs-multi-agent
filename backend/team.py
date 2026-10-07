"""Builds the five-agent team and runs a ticket starting from the Boss."""

import uuid
from pathlib import Path

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage, UsageLimits

from backend.agents import accounting, boss, customer_service, facilities, inventory
from backend.audit import AuditLog
from backend.config import (
    PROJECT_ROOT,
    TICKET_REQUEST_LIMIT,
    TICKET_TOTAL_TOKENS_LIMIT,
    build_model,
    mcp_command,
    mcp_env,
)
from backend.models import AgentDeps, AgentReport, DelegationBudget, TicketRunResult
from backend.runner import run_logged

AGENT_MODULES = {
    "boss": boss,
    "inventory": inventory,
    "accounting": accounting,
    "facilities": facilities,
    "customer_service": customer_service,
}


def make_mcp_toolset() -> MCPToolset:
    """One stdio connection to the campus-customs MCP server (same command as .mcp.json)."""
    command, args = mcp_command()
    transport = StdioTransport(command, args, env=mcp_env(), cwd=str(PROJECT_ROOT), keep_alive=False)
    return MCPToolset(transport)


def build_team(
    mcp_toolset: MCPToolset,
    model: Model | None = None,
    model_overrides: dict[str, Model] | None = None,
) -> dict[str, Agent[AgentDeps, AgentReport]]:
    """Create all five agents. Every agent uses the same model unless a test overrides one."""
    default_model = model or build_model()
    overrides = model_overrides or {}
    return {
        name: module.create(overrides.get(name, default_model), mcp_toolset)
        for name, module in AGENT_MODULES.items()
    }


async def run_ticket(
    ticket_id: int,
    *,
    model: Model | None = None,
    model_overrides: dict[str, Model] | None = None,
    audit_path: Path | None = None,
) -> TicketRunResult:
    """Start the Boss on a ticket. Limits and the audit trail apply to the whole team."""
    run_id = uuid.uuid4().hex[:12]
    audit = AuditLog(audit_path)
    audit.ensure_exists()
    usage = RunUsage()
    toolset = make_mcp_toolset()
    deps = AgentDeps(
        run_id=run_id,
        ticket_id=ticket_id,
        agent_name="boss",
        depth=0,
        usage=usage,
        usage_limits=UsageLimits(request_limit=TICKET_REQUEST_LIMIT, total_tokens_limit=TICKET_TOTAL_TOKENS_LIMIT),
        budget=DelegationBudget(),
        audit=audit,
    )
    prompt = f"Work ticket {ticket_id}. Start by reading it with get_ticket."
    report: AgentReport | None = None
    status, error = "finished", None
    async with toolset:  # one MCP server process shared by the whole team for this run
        deps.team = build_team(toolset, model, model_overrides)
        try:
            report = await run_logged(deps.team["boss"], prompt, deps)
        except UsageLimitExceeded as exc:
            status, error = "limit_reached", str(exc)
        except Exception as exc:  # reported, not raised, so the caller gets the audit run id
            status, error = "error", f"{type(exc).__name__}: {exc}"
    return TicketRunResult(
        run_id=run_id,
        ticket_id=ticket_id,
        status=status,
        report=report,
        error=error,
        requests=usage.requests,
        total_tokens=usage.total_tokens,
    )
