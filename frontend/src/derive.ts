import { AGENT_NAME, AGENTS, toolVerb } from "./agents";
import type { AgentEvent, AgentId } from "./types";

export type AgentStatus = "idle" | "working" | "delegating" | "done";

export interface Handoff {
  to: string;
  task: string;
}

export interface AgentView {
  id: AgentId;
  status: AgentStatus;
  involved: boolean;
  said: string | null;
  tools: string[]; // MCP tools used on this ticket, in first-used order
  handoffs: Handoff[];
  finalMessage: string | null;
}

/** The id of the most recent run that touched this ticket. */
export function latestRunId(events: AgentEvent[], ticketId: number | null): string | null {
  if (ticketId === null) return null;
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].ticket_id === ticketId) return events[i].run_id;
  }
  return null;
}

export function parseHandoff(event: AgentEvent): Handoff | null {
  // Real runs send {to_agent, task, context}; older/stand-in runs nest it under "request".
  const args = (event.arguments ?? {}) as { to_agent?: string; task?: string; request?: { to_agent?: string; task?: string } };
  const to = args.to_agent ?? args.request?.to_agent;
  if (!to) return null;
  return { to, task: args.task ?? args.request?.task ?? "" };
}

/** Everything the agent cards and summaries show is derived from the events. */
export function deriveAgents(
  events: AgentEvent[],
  ticketId: number | null,
  running: boolean,
): { views: Record<AgentId, AgentView>; runId: string | null } {
  const runId = latestRunId(events, ticketId);
  const runEvents = events.filter((e) => e.ticket_id === ticketId && e.run_id === runId);
  const views = {} as Record<AgentId, AgentView>;
  for (const agent of AGENTS) {
    const mine = runEvents.filter((e) => e.agent === agent.id);
    const tools: string[] = [];
    const handoffs: Handoff[] = [];
    let said: string | null = null;
    let finalMessage: string | null = null;
    for (const e of mine) {
      if (e.kind === "tool_call" && e.tool_name && !tools.includes(e.tool_name)) tools.push(e.tool_name);
      if (e.kind === "delegation") {
        const handoff = parseHandoff(e);
        if (handoff) handoffs.push(handoff);
      }
      if (e.message) said = e.message;
      if (e.kind === "final_output") finalMessage = e.message;
    }
    const last = mine[mine.length - 1];
    let status: AgentStatus = "idle";
    if (last) {
      if (last.kind === "final_output" || last.kind === "error") status = "done";
      else if (!running) status = "done";
      else status = last.kind === "delegation" ? "delegating" : "working";
    }
    if (!said && last && last.kind === "tool_call" && last.tool_name) said = `Just ${toolVerb(last.tool_name)}.`;
    views[agent.id] = { id: agent.id, status, involved: mine.length > 0, said, tools, handoffs, finalMessage };
  }
  return { views, runId };
}

export function describeEvent(e: AgentEvent): string {
  const who = AGENT_NAME[e.agent] ?? e.agent;
  switch (e.kind) {
    case "delegation": {
      const h = parseHandoff(e);
      return h ? `${who} handed this to ${AGENT_NAME[h.to] ?? h.to}${h.task ? `: ${h.task}` : ""}` : `${who} handed work to a teammate`;
    }
    case "tool_call":
      return `${who} ${toolVerb(e.tool_name ?? "a tool")}`;
    case "tool_result":
      return `${who} got a result${e.result_summary ? `: ${e.result_summary}` : ""}`;
    case "model_request":
      return e.message ? `${who} said: ${e.message}` : `${who} is thinking`;
    case "final_output":
      return `${who} finished${e.message ? `: ${e.message}` : ""}`;
    case "error":
      return `${who} ran into a problem`;
    case "reset":
      return "The desk was reset";
    default:
      return `${who}: ${e.kind}`;
  }
}

export function eventKey(e: AgentEvent): string {
  return `${e.timestamp}|${e.run_id}|${e.agent}|${e.step}|${e.kind}|${e.tool_name ?? ""}`;
}
