"""Customer Service: drafts messages for customers (drafts only, nothing is sent)."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.agents.common import build_agent
from backend.models import AgentDeps, AgentReport

NAME = "customer_service"
ALLOWED_TOOLS = frozenset({
    "get_shop_date", "get_ticket", "save_customer_draft", "list_customer_drafts",
})


def create(model: Model, mcp_toolset: MCPToolset) -> Agent[AgentDeps, AgentReport]:
    return build_agent(NAME, model, mcp_toolset, ALLOWED_TOOLS)
