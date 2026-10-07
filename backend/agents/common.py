"""Shared agent construction: prompt loading and MCP tool allowlists."""

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from pydantic_ai.models import Model

from backend.config import PROMPTS_DIR
from backend.delegation import delegate_to_agent
from backend.models import AgentDeps, AgentReport


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def build_agent(
    name: str, model: Model, mcp_toolset: MCPToolset, allowed_tools: frozenset[str]
) -> Agent[AgentDeps, AgentReport]:
    """Build an agent that sees only its allowlisted MCP tools plus delegation."""
    shop_tools = mcp_toolset.filtered(lambda _ctx, tool_def: tool_def.name in allowed_tools)
    return Agent(
        model,
        deps_type=AgentDeps,
        output_type=AgentReport,
        instructions=load_prompt(name),
        toolsets=[shop_tools],
        tools=[delegate_to_agent],
        name=name,
    )
