"""Shared data types for the agent team."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pydantic_ai import Agent
    from pydantic_ai.usage import RunUsage, UsageLimits

    from backend.audit import AuditLog

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
AGENT_NAMES: tuple[str, ...] = ("boss", "inventory", "accounting", "facilities", "customer_service")


class Ticket(BaseModel):
    """A ticket row as returned by the get_ticket MCP tool."""

    id: int
    type: str
    requester: str
    subject: str
    sku: str | None = None
    size: str | None = None
    qty: int | None = None
    lease_id: int | None = None
    invoice_id: int | None = None
    status: str
    notes: str | None = None
    created_at: str


class AgentReport(BaseModel):
    """What every agent hands back: to the Boss, or from the Boss to the human."""

    agent: str = Field(description="Name of the agent writing this report.")
    status: Literal["done", "needs_human", "blocked", "failed"] = Field(
        description="done: finished. needs_human: waiting on a human (approval or decision). "
        "blocked: cannot proceed because of a rule or missing information. failed: could not complete."
    )
    summary: str = Field(description="Two to four plain sentences on what was found or done.")
    facts: list[str] = Field(default_factory=list, description="Facts learned, each with its source tool.")
    actions: list[str] = Field(
        default_factory=list, description="Actions taken, with ids (approval, purchase order, draft)."
    )
    open_questions: list[str] = Field(default_factory=list, description="Information that is missing.")
    escalate_to_human: bool = False
    escalation_reason: str | None = None
    decision: str | None = Field(default=None, description="Boss only: the final call on the ticket.")


class DelegationRequest(BaseModel):
    """A request from one agent to hand a task to another agent."""

    to_agent: AgentName = Field(description="Which agent should do the task.")
    task: str = Field(description="What you need, in plain words, with the ids it needs.")
    context: str | None = Field(default=None, description="Facts the other agent needs, if any.")


class AuditEntry(BaseModel):
    """One step of an agent loop, appended to output/audit_trail.json."""

    timestamp: str
    run_id: str
    ticket_id: int
    agent: str
    depth: int
    step: int
    kind: Literal["model_request", "tool_call", "tool_result", "delegation", "final_output", "error"]
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result_summary: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class TicketRunResult(BaseModel):
    """What run_ticket returns."""

    run_id: str
    ticket_id: int
    status: Literal["finished", "limit_reached", "error"]
    report: AgentReport | None = None
    error: str | None = None
    requests: int = 0
    total_tokens: int = 0


@dataclass
class DelegationBudget:
    """Counts delegations across the whole ticket (shared by every agent)."""

    used: int = 0


@dataclass
class AgentDeps:
    """Dependencies handed to every agent run. Shared objects are shared on purpose."""

    run_id: str
    ticket_id: int
    agent_name: str
    depth: int
    usage: "RunUsage"
    usage_limits: "UsageLimits"
    budget: DelegationBudget
    audit: "AuditLog"
    team: dict[str, "Agent[AgentDeps, AgentReport]"] = field(default_factory=dict)
