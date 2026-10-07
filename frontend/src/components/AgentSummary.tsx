import { AGENTS, toolVerb } from "../agents";
import type { AgentView } from "../derive";
import type { AgentId, AgentReport } from "../types";

interface Props {
  views: Record<AgentId, AgentView>;
  report: AgentReport | null;
  hasRun: boolean;
}

export function AgentSummary({ views, report, hasRun }: Props) {
  if (!hasRun) return <p className="empty">Run the agents on this ticket to see what each one did.</p>;
  return (
    <section className="panel" aria-labelledby="summary-title">
      <h2 id="summary-title">What each agent did</h2>
      {report ? <p className="boss-decision"><strong>Boss's call:</strong> {report.decision ?? report.summary}</p> : null}
      <ul className="summary-list">
        {AGENTS.map((agent) => {
          const view = views[agent.id];
          return (
            <li key={agent.id} style={{ ["--accent" as string]: `var(${agent.color})` }}>
              <strong>{agent.name}</strong>
              {view.involved ? (
                <>
                  <span>{view.finalMessage ?? view.said ?? "Worked on it."}</span>
                  {view.tools.length ? <small>{view.tools.map(toolVerb).join(", ")}.</small> : null}
                </>
              ) : (
                <span className="muted">Wasn't involved in this ticket.</span>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
