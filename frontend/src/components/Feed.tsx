import { useState } from "react";
import { describeEvent } from "../derive";
import type { AgentEvent } from "../types";

export function Feed({ events }: { events: AgentEvent[] }) {
  const [open, setOpen] = useState(true);
  const newestFirst = [...events].reverse().slice(0, 120);
  return (
    <section className="panel" aria-labelledby="feed-title">
      <h2 id="feed-title">
        <button type="button" className="disclosure" aria-expanded={open} aria-controls="feed-list" onClick={() => setOpen(!open)}>
          Activity feed <span aria-hidden="true">{open ? "▾" : "▸"}</span>
        </button>
      </h2>
      {open ? (
        newestFirst.length === 0 ? (
          <p className="empty" id="feed-list">No activity for this ticket yet.</p>
        ) : (
          <ol className="feed" id="feed-list">
            {newestFirst.map((e, i) => (
              <li key={`${e.timestamp}-${i}`} className={`feed-item feed-item--${e.kind}`}>
                <span className="feed-agent">{e.agent.replace("_", " ")}</span>
                <span className="feed-text">{describeEvent(e)}</span>
              </li>
            ))}
          </ol>
        )
      ) : null}
    </section>
  );
}
