import type { Ticket } from "../types";

const TYPE_LABEL: Record<string, string> = {
  customer_order: "Customer order",
  rent_notice: "Rent notice",
  price_override: "Price override",
};

interface Props {
  tickets: Ticket[];
  selectedId: number | null;
  runningId: number | null;
  onSelect: (id: number) => void;
}

export function TicketList({ tickets, selectedId, runningId, onSelect }: Props) {
  return (
    <ul className="ticket-list">
      {tickets.map((t) => {
        const selected = t.id === selectedId;
        return (
          <li key={t.id}>
            <button
              type="button"
              className={`work-order ${selected ? "work-order--selected" : ""} ${t.status === "resolved" ? "work-order--resolved" : ""}`}
              aria-pressed={selected}
              onClick={() => onSelect(t.id)}
            >
              <span className="work-order-top">
                <span className="work-order-no">Work order #{t.id}</span>
                <span className="work-order-type">{TYPE_LABEL[t.type] ?? t.type}</span>
              </span>
              <span className="work-order-subject">{t.subject}</span>
              <span className="work-order-notes">{t.notes}</span>
              <span className="work-order-meta">
                {t.qty !== null && t.sku ? <span>{t.qty} × {t.sku}{t.size ? ` (${t.size})` : ""}</span> : null}
                <span className={`badge badge--${t.status}`}>{t.status === "resolved" ? "Resolved" : "Open"}</span>
                {runningId === t.id ? <span className="badge badge--running">Agents working…</span> : null}
                {t.pending_approvals > 0 ? (
                  <span className="badge badge--pending" title="Waiting for a human decision">
                    {t.pending_approvals} {t.pending_approvals === 1 ? "approval" : "approvals"} waiting
                  </span>
                ) : null}
              </span>
              {t.status === "resolved" ? <span className="stamp" aria-hidden="true">RESOLVED</span> : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
