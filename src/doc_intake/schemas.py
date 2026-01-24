from pydantic import BaseModel, Field
from typing import Optional, Literal


class InvoiceHeader(BaseModel):
    document_type: Literal["invoice"] = "invoice"
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None  # keep string for MVP
    currency: Optional[str] = None
    subtotal: Optional[str] = None
    tax: Optional[str] = None
    total_amount: Optional[str] = None
    po_number: Optional[str] = None


class ReceiptHeader(BaseModel):
    document_type: Literal["receipt"] = "receipt"
    merchant_name: Optional[str] = None
    transaction_date: Optional[str] = None
    currency: Optional[str] = None
    total_amount: Optional[str] = None
    payment_method: Optional[str] = None


class PurchaseOrderHeader(BaseModel):
    document_type: Literal["purchase_order"] = "purchase_order"
    buyer_name: Optional[str] = None
    supplier_name: Optional[str] = None
    po_number: Optional[str] = None
    po_date: Optional[str] = None
    total_amount: Optional[str] = None
