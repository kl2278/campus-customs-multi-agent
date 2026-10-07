"""Facilities: shop space, leases and rent."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.agents.common import build_agent
from backend.models import AgentDeps, AgentReport

NAME = "facilities"
ALLOWED_TOOLS = frozenset({
    "get_shop_date", "get_ticket", "get_lease_rent_status",
})


def create(model: Model, mcp_toolset: MCPToolset) -> Agent[AgentDeps, AgentReport]:
    return build_agent(NAME, model, mcp_toolset, ALLOWED_TOOLS)
