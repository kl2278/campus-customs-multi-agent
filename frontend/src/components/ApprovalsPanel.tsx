import { useState } from "react";
import type { Approval } from "../types";

const money = (n: number) => n.toLocaleString("en-US", { style: "currency", currency: "USD" });
const KIND: Record<Approval["kind"], string> = { invoice: "Invoice payment", rent: "Rent payment", purchase_order: "Purchase order" };

interface Props {
  approvals: Approval[];
  busyId: number | null;
  message: { tone: "error" | "ok"; text: string } | null;
  onDecide: (id: number, action: "approve" | "reject", name: string) => void;
}

export function ApprovalsPanel({ approvals, busyId, message, onDecide }: Props) {
  const [name, setName] = useState(""); // never pre-filled: a human types their own name
  const pending = approvals.filter((a) => a.status === "pending");
  const past = approvals.filter((a) => a.status !== "pending");
  const ready = name.trim().length > 0;

  return (
    <section aria-labelledby="approvals-title" className="panel">
      <h2 id="approvals-title">Approvals</h2>
      <label className="name-field">
        <span>Your name (needed to approve or reject)</span>
        <input type="text" value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" placeholder="Type your name" />
      </label>
      {message ? <p className={`note note--${message.tone}`} role="status">{message.text}</p> : null}

      <h3>Waiting for you</h3>
      {pending.length === 0 ? <p className="empty">Nothing is waiting for approval.</p> : null}
      <ul className="approval-list">
        {pending.map((a) => (
          <li key={a.id} className="approval">
            <div className="approval-top">
              <strong>{KIND[a.kind]}</strong>
              <span className="approval-amount">{a.kind === "purchase_order" ? `${a.quantity} × ${a.sku} (${a.size})` : money(a.amount)}</span>
            </div>
            <p className="approval-meta">
              Asked by {a.requested_by}{a.ticket_id ? ` for ticket #${a.ticket_id}` : ""}
              {a.kind === "purchase_order" ? ` · ${money(a.amount)} · expected ${a.expected_arrival}` : ""}
            </p>
            {a.reason ? <p className="approval-reason">{a.reason}</p> : null}
            <div className="approval-actions">
              <button type="button" className="btn btn--approve" disabled={!ready || busyId === a.id} onClick={() => onDecide(a.id, "approve", name.trim())}>
                {a.kind === "purchase_order" ? "Approve order" : "Approve and pay"}
              </button>
              <button type="button" className="btn btn--ghost" disabled={!ready || busyId === a.id} onClick={() => onDecide(a.id, "reject", name.trim())}>
                Reject
              </button>
            </div>
            {!ready ? <p className="hint">Type your name above to enable these buttons.</p> : null}
          </li>
        ))}
      </ul>

      <h3>Past decisions</h3>
      {past.length === 0 ? <p className="empty">No decisions yet.</p> : null}
      <ul className="approval-list approval-list--past">
        {past.map((a) => (
          <li key={a.id} className="approval approval--past">
            <div className="approval-top">
              <span>{KIND[a.kind]}{a.ticket_id ? ` · ticket #${a.ticket_id}` : ""}</span>
              <span className={`badge badge--${a.status === "rejected" ? "rejected" : "resolved"}`}>{a.status}</span>
            </div>
            <p className="approval-meta">
              {a.kind === "purchase_order" ? `${a.quantity} × ${a.sku} (${a.size})` : money(a.amount)} · asked by {a.requested_by} · decided by {a.decided_by ?? "—"}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
