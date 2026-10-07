export type AgentId = "boss" | "inventory" | "accounting" | "facilities" | "customer_service";

export interface Ticket {
  id: number;
  type: string;
  requester: string;
  subject: string;
  sku: string | null;
  size: string | null;
  qty: number | null;
  lease_id: number | null;
  invoice_id: number | null;
  status: "open" | "resolved";
  notes: string | null;
  created_at: string;
  pending_approvals: number;
}

export interface Cash {
  account: string;
  balance: number;
  date: string;
  shop_date: string | null;
}

export interface AgentEvent {
  timestamp: string;
  run_id: string;
  ticket_id: number | null;
  agent: string;
  depth: number;
  step: number;
  kind: string;
  tool_name: string | null;
  arguments: Record<string, unknown> | null;
  result_summary: string | null;
  message: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
}

export interface Approval {
  id: number;
  kind: "invoice" | "rent" | "purchase_order";
  ref_id: number;
  ticket_id: number | null;
  amount: number;
  quantity: number | null;
  sku: string | null;
  size: string | null;
  vendor_id: number | null;
  expected_arrival: string | null;
  requested_by: string;
  reason: string | null;
  status: string;
  decided_by: string | null;
  decided_on: string | null;
  decision_note: string | null;
}

export interface AgentReport {
  agent: string;
  status: "done" | "needs_human" | "blocked" | "failed";
  summary: string;
  facts: string[];
  actions: string[];
  open_questions: string[];
  escalate_to_human: boolean;
  escalation_reason: string | null;
  work_complete: boolean;
  decision: string | null;
}

export interface RunResult {
  run_id: string;
  ticket_id: number;
  run_status: string;
  report: AgentReport | null;
  ticket_status: "open" | "resolved";
}

export interface DecisionResult {
  approval: Approval;
  payment: { payment_id: number; amount: number; new_cash_balance: number } | null;
}
