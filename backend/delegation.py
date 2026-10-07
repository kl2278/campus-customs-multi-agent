"""The delegate tool every agent gets: hand a task to any other agent."""

from dataclasses import replace

from pydantic_ai import RunContext

from backend.config import MAX_DELEGATION_DEPTH, MAX_DELEGATIONS_PER_TICKET
from backend.models import AgentDeps, AgentReport, DelegationRequest
from backend.runner import AgentStepLimitError, run_logged


async def delegate_to_agent(ctx: RunContext[AgentDeps], request: DelegationRequest) -> AgentReport:
    """Hand a task to another agent and get that agent's report back.

    Use this when the task needs another agent's tools or expertise: inventory
    and vendors, payments and margins, leases and rent, or customer messages.
    Give the task in plain words with the ids it needs. You cannot delegate to
    yourself. Delegation is limited in depth and in count per ticket; if a
    limit is hit you get a failed report back and should escalate to the human.
    """
    deps = ctx.deps

    def failed(message: str) -> AgentReport:
        return AgentReport(agent=request.to_agent, status="failed", summary=message)

    if request.to_agent == deps.agent_name:
        return failed("An agent cannot delegate to itself.")
    if request.to_agent not in deps.team:
        return failed(f"Unknown agent {request.to_agent!r}.")
    if deps.depth + 1 > MAX_DELEGATION_DEPTH:
        return failed(f"Delegation depth limit ({MAX_DELEGATION_DEPTH}) reached; do the work yourself or escalate.")
    if deps.budget.used >= MAX_DELEGATIONS_PER_TICKET:
        return failed(f"Delegation limit for this ticket ({MAX_DELEGATIONS_PER_TICKET}) reached; escalate.")
    deps.budget.used += 1

    child = replace(deps, agent_name=request.to_agent, depth=deps.depth + 1)
    prompt = (
        f"Task from the {deps.agent_name} agent on ticket {deps.ticket_id}:\n{request.task}\n"
        + (f"\nContext from {deps.agent_name}:\n{request.context}\n" if request.context else "")
    )
    try:
        return await run_logged(deps.team[request.to_agent], prompt, child)
    except AgentStepLimitError as exc:
        return failed(str(exc))
