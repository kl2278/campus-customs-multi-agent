"""Runs one agent and writes every loop step to the audit trail."""

from typing import Any

from pydantic_ai import Agent
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.settings import ModelSettings

from backend.audit import scrub_arguments, summarize
from backend.config import MAX_OUTPUT_TOKENS, MAX_STEPS_PER_AGENT
from backend.models import AgentDeps, AgentReport

DELEGATE_TOOL = "delegate_to_agent"
OUTPUT_TOOL = "final_result"  # PydanticAI's default name for the structured-output tool


class AgentStepLimitError(Exception):
    """One agent used more than MAX_STEPS_PER_AGENT model requests."""


async def run_logged(agent: Agent[AgentDeps, AgentReport], prompt: str, deps: AgentDeps) -> AgentReport:
    """Run an agent to completion, appending an audit entry for each step."""
    step = 0

    def log(kind: str, **fields: Any) -> None:
        deps.audit.append(
            run_id=deps.run_id, ticket_id=deps.ticket_id, agent=deps.agent_name,
            depth=deps.depth, step=step, kind=kind, **fields,
        )

    try:
        async with agent.iter(
            prompt,
            deps=deps,
            usage=deps.usage,  # shared, so limits cover every delegated agent
            usage_limits=deps.usage_limits,
            model_settings=ModelSettings(max_tokens=MAX_OUTPUT_TOKENS),
        ) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    for part in node.request.parts:
                        if isinstance(part, ToolReturnPart):
                            log("tool_result", tool_name=part.tool_name, result_summary=summarize(part.content))
                        elif isinstance(part, RetryPromptPart):
                            log("tool_result", tool_name=part.tool_name, result_summary=summarize(part.content))
                    step += 1
                    if step > MAX_STEPS_PER_AGENT:
                        raise AgentStepLimitError(
                            f"{deps.agent_name} reached its step limit of {MAX_STEPS_PER_AGENT}."
                        )
                elif Agent.is_call_tools_node(node):
                    usage = node.model_response.usage
                    log("model_request", input_tokens=usage.input_tokens, output_tokens=usage.output_tokens)
                    for part in node.model_response.parts:
                        if not isinstance(part, ToolCallPart) or part.tool_name == OUTPUT_TOOL:
                            continue
                        kind = "delegation" if part.tool_name == DELEGATE_TOOL else "tool_call"
                        log(kind, tool_name=part.tool_name, arguments=scrub_arguments(part.args))
            report = run.result.output
    except Exception as exc:
        log("error", result_summary=summarize(f"{type(exc).__name__}: {exc}"))
        raise
    log("final_output", result_summary=summarize(report.model_dump()))
    return report
