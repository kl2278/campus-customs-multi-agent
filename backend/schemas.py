"""Request and response models for the FastAPI routes."""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from backend.models import AgentReport


class TicketOut(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    sku: str | None = None
    size: str | None = None
    qty: int | None = None
    lease_id: int | None = None
    invoice_id: int | None = None
    status: Literal["open", "resolved"]
    notes: str | None = None
    created_at: str
    pending_approvals: int = 0


class CashOut(BaseModel):
    account: str
    balance: float
    date: str
    shop_date: str | None


class EventOut(BaseModel):
    timestamp: str
    run_id: str
    ticket_id: int | None = None
    agent: str
    depth: int
    step: int
    kind: str
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result_summary: str | None = None
    message: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None


class ApprovalOut(BaseModel):
    id: int
    kind: Literal["invoice", "rent", "purchase_order"]
    ref_id: int
    ticket_id: int | None = None
    amount: float
    quantity: int | None = Field(default=None, description="Purchase orders only.")
    sku: str | None = None
    size: str | None = None
    vendor_id: int | None = None
    expected_arrival: str | None = None
    account: str | None = None
    requested_by: str
    reason: str | None = None
    status: str
    decided_by: str | None = None
    decided_on: str | None = None
    decision_note: str | None = None
    created_on: str
    executed_on: str | None = None
    payment_id: int | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ApprovalOut":
        return cls(
            **{k: row.get(k) for k in cls.model_fields if k in row},
            sku=row.get("po_sku"),
            size=row.get("po_size"),
            vendor_id=row.get("po_vendor_id"),
            expected_arrival=row.get("po_expected_arrival"),
        )


class DecisionIn(BaseModel):
    decided_by: str = Field(description="The human's name, typed by the person clicking.")
    note: str | None = None

    @field_validator("decided_by")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("decided_by must not be empty")
        return value.strip()


class PaymentOut(BaseModel):
    payment_id: int
    kind: str
    ref_id: int
    amount: float
    approved_by: str
    new_cash_balance: float
    new_next_due: str | None = None


class DecisionOut(BaseModel):
    approval: ApprovalOut
    payment: PaymentOut | None = None


class RunOut(BaseModel):
    run_id: str
    ticket_id: int
    run_status: Literal["finished", "limit_reached", "error"]
    report: AgentReport | None
    ticket_status: Literal["open", "resolved"]


class ResetOut(BaseModel):
    message: str


class ErrorOut(BaseModel):
    detail: str
