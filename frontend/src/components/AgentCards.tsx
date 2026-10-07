import { AGENT_NAME, AGENTS, toolVerb } from "../agents";
import type { AgentView } from "../derive";
import type { AgentId } from "../types";
import { AgentIcon } from "./AgentIcon";

const STATUS_WORDS = { idle: "Idle", working: "Working", delegating: "Delegating", done: "Done" } as const;

interface Props {
  views: Record<AgentId, AgentView>;
  hasRun: boolean;
}

export function AgentCards({ views, hasRun }: Props) {
  return (
    <section aria-labelledby="agents-title">
      <h2 id="agents-title">The team</h2>
      <ul className="agent-grid">
        {AGENTS.map((agent) => {
          const view = views[agent.id];
          const lastHandoff = view.handoffs[view.handoffs.length - 1];
          return (
            <li key={agent.id} className={`agent-card agent-card--${view.status}`} style={{ ["--accent" as string]: `var(${agent.color})` }}>
              <div className="agent-head">
                <span className="agent-icon"><AgentIcon id={agent.id} /></span>
                <div>
                  <h3>{agent.name}</h3>
                  <p className="agent-personality">{agent.personality}</p>
                </div>
                <span className={`status-pill status-pill--${view.status}`}>{STATUS_WORDS[view.status]}</span>
              </div>
              {view.status === "delegating" && lastHandoff ? (
                <p className="handoff" role="status">Handed this to {AGENT_NAME[lastHandoff.to] ?? lastHandoff.to}, waiting for the answer.</p>
              ) : null}
              <div className="bubble" aria-live="polite">
                {view.said ?? (view.involved ? "…" : hasRun ? "Not needed on this ticket." : agent.role)}
              </div>
              {view.handoffs.length > 0 ? (
                <p className="handoff-list">
                  {view.handoffs.map((h, i) => (
                    <span key={i} className="handoff-chip">→ {AGENT_NAME[h.to] ?? h.to}</span>
                  ))}
                </p>
              ) : null}
              <ul className="chips" aria-label={`Tools used by ${agent.name}`}>
                {view.tools.length === 0 ? <li className="chip chip--empty">no tools used yet</li> : null}
                {view.tools.map((tool) => (
                  <li key={tool} className="chip" title={toolVerb(tool)}>{tool}</li>
                ))}
              </ul>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
