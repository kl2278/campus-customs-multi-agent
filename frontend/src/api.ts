import type { AgentEvent, Approval, Cash, DecisionResult, RunResult, Ticket } from "./types";

/** The one place the API address lives. Override with VITE_API_URL if needed. */
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number; // 0 means the backend could not be reached
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    // No timeout on purpose: a ticket run can take minutes.
    response = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError(0, "Can't reach the backend.");
  }
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = typeof body?.detail === "string" ? body.detail : "";
    } catch {
      /* no JSON body */
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

const post = (body?: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const api = {
  tickets: () => request<Ticket[]>("/tickets"),
  cash: () => request<Cash>("/cash"),
  approvals: () => request<Approval[]>("/approvals"),
  events: (since?: string) =>
    request<AgentEvent[]>(`/events?limit=500${since ? `&since=${encodeURIComponent(since)}` : ""}`),
  run: (ticketId: number) => request<RunResult>(`/tickets/${ticketId}/run`, post()),
  approve: (id: number, decidedBy: string) =>
    request<DecisionResult>(`/approvals/${id}/approve`, post({ decided_by: decidedBy })),
  reject: (id: number, decidedBy: string) =>
    request<DecisionResult>(`/approvals/${id}/reject`, post({ decided_by: decidedBy })),
  reset: () => request<{ message: string }>("/reset", post()),
};

/** Friendly words for errors the human may see. Never shows technical detail. */
export function friendlyError(error: unknown, context: "run" | "approve" | "reject" | "reset" | "load"): string {
  if (!(error instanceof ApiError)) return "Something unexpected happened. Please try again.";
  if (error.status === 0) return "Can't reach the backend. Start the backend first, then try again.";
  const detail = error.message;
  switch (error.status) {
    case 403:
      return "The person approving can't be the same as the one who asked. Someone else needs to decide this one.";
    case 404:
      return context === "run" ? "That ticket isn't on the desk anymore." : "That item isn't on the desk anymore.";
    case 409:
      if (/not enough cash/i.test(detail)) return "Not enough cash in checking to pay this. Nothing was changed and it is still waiting.";
      if (/already/i.test(detail)) return "That was already decided, so nothing was changed.";
      if (context === "run") return "The desk is busy with something else, or this ticket is already resolved. Nothing was started.";
      if (context === "reset") return "The desk is busy with a run right now. Try the reset again when it finishes.";
      return detail ? `That can't go through right now: ${detail}` : "That can't go through right now.";
    case 422:
      return "That didn't look right. Please check what you typed and try again.";
    case 504:
      return "The run took too long and was stopped. The ticket stays open.";
    case 500:
      return context === "run"
        ? "The agents hit a snag. The ticket stays open. The activity feed shows how far they got."
        : "The backend hit a snag. Please try again.";
    default:
      return "Something went wrong. Please try again.";
  }
}
