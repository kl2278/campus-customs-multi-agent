"""Inventory: stock by SKU and size, shortfalls, vendors and purchase orders."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.agents.common import build_agent
from backend.models import AgentDeps, AgentReport

NAME = "inventory"
ALLOWED_TOOLS = frozenset({
    "get_shop_date", "get_ticket", "check_stock", "list_vendors", "get_vendor_ship_status",
    "create_purchase_order", "list_purchase_orders",
})


def create(model: Model, mcp_toolset: MCPToolset) -> Agent[AgentDeps, AgentReport]:
    return build_agent(NAME, model, mcp_toolset, ALLOWED_TOOLS)
