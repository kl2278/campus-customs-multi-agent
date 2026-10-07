import type { AgentId } from "./types";

export interface AgentInfo {
  id: AgentId;
  name: string;
  role: string;
  personality: string;
  color: string; // CSS variable name
}

export const AGENTS: AgentInfo[] = [
  { id: "boss", name: "Boss", role: "Reads the ticket and makes the final call", personality: "Calm and decisive", color: "--boss" },
  { id: "inventory", name: "Inventory", role: "Counts stock and finds who can restock", personality: "Methodical counter", color: "--inventory" },
  { id: "accounting", name: "Accounting", role: "Watches cash, invoices and margins", personality: "Careful penny-watcher", color: "--accounting" },
  { id: "facilities", name: "Facilities", role: "Looks after the shop space and rent", personality: "Practical fixer", color: "--facilities" },
  { id: "customer_service", name: "Customer Service", role: "Drafts friendly messages (never sends)", personality: "Warm and friendly", color: "--service" },
];

export const AGENT_NAME: Record<string, string> = Object.fromEntries(AGENTS.map((a) => [a.id, a.name]));

const TOOL_VERBS: Record<string, string> = {
  get_ticket: "read the ticket",
  get_open_tickets: "looked at the open tickets",
  get_shop_date: "checked the shop date",
  check_stock: "checked stock",
  list_vendors: "looked up the vendors",
  get_vendor_ship_status: "checked whether the vendor can ship",
  get_invoice: "read an invoice",
  list_open_invoices: "listed the unpaid invoices",
  get_cash_balance: "checked the cash balance",
  list_payments: "looked at past payments",
  get_unit_pricing: "checked pricing and margin",
  get_lease_rent_status: "checked the lease and rent date",
  list_approvals: "checked the approvals",
  list_purchase_orders: "looked at purchase orders",
  list_customer_drafts: "looked at the drafts",
  queue_payment_for_approval: "queued a payment for approval",
  create_purchase_order: "saved a purchase order for approval",
  save_customer_draft: "saved a customer draft",
  execute_approved_payment: "executed an approved payment",
  delegate_to_agent: "handed work to a teammate",
};

export const toolVerb = (tool: string) => TOOL_VERBS[tool] ?? tool.replace(/_/g, " ");
