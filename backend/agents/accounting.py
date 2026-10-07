"""Accounting: cash, invoices, margins, and payments that need human approval."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.agents.common import build_agent
from backend.models import AgentDeps, AgentReport

NAME = "accounting"
ALLOWED_TOOLS = frozenset({
    "get_shop_date", "get_ticket", "get_unit_pricing", "get_invoice", "list_open_invoices",
    "get_cash_balance", "list_payments", "list_approvals",
    "queue_payment_for_approval", "execute_approved_payment",
})


def create(model: Model, mcp_toolset: MCPToolset) -> Agent[AgentDeps, AgentReport]:
    return build_agent(NAME, model, mcp_toolset, ALLOWED_TOOLS)
