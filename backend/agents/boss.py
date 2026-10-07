"""Boss: reads tickets, decides who works on them, and makes the final call."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.agents.common import build_agent
from backend.models import AgentDeps, AgentReport

NAME = "boss"
ALLOWED_TOOLS = frozenset({
    "get_shop_date", "get_open_tickets", "get_ticket", "get_cash_balance",
    "list_approvals", "list_purchase_orders", "list_customer_drafts",
})


def create(model: Model, mcp_toolset: MCPToolset) -> Agent[AgentDeps, AgentReport]:
    return build_agent(NAME, model, mcp_toolset, ALLOWED_TOOLS)
